#! /usr/bin/env python
import sys, getopt
from time import sleep
from datetime import datetime, timedelta
from mydefs import *
import syslog
from enum import IntEnum
import ConfigParser
import random
import string
import mysql.connector
import time
import math
import httplib2
import urllib

class TraceLevel(IntEnum):
    Abort = 0
    Critical = 1
    Major = 2
    Minor = 3
    Log = 4
    Info = 5
    Debug = 10
endclass

CURRENT_TRACE_LEVEL = TraceLevel.Critical


def logMessage(level, msg):
    if ( level <= CURRENT_TRACE_LEVEL):
        print str(datetime.now()) + ": " + msg
        syslog.syslog(msg)
    endif
enddef


#>>>>>>>>>>>>>>>>>>>Begin Main Here <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
main

cmdLine = ""

for arg in sys.argv:
    cmdLine += " " + arg
endfor
logMessage(TraceLevel.Critical,cmdLine)

try:    
    opts, args = getopt.getopt(sys.argv[1:],"t:c:")
except getopt.GetoptError:
    logMessage(TraceLevel.Abort, "Usage: weatherUnderground.py -t tracelevel -c configFile")
    sys.exit(2)
endtry

configFile = ""
dbHost = ""
dbName = ""
dbUser = ""
dbPassword = ""
dbPrefix = ""
windSpeedUom = ""
baroPressureUom = ""

wu_url = ""
wu_sw = ""
wu_stationId = ""
wu_password = ""
wu_humiditySensorId = 0
wu_tempSensorId = 0
wu_rainSensorId = 0
wu_windSpeedSensorId = 0
wu_windDirSensorId = 0
wu_pressureSensorId = 0
serverFileName = ""

windSpeed = 0
windGust = 0
windDir = 0
temperature = 0
humidity = 0
dewPoint = 0
pressure = 0
rain = 0
rainRate = 0

foundHumidity = False
foundTemperature = False


for opt, arg in opts:
    if opt == '-t':
        if '1' == arg:
            CURRENT_TRACE_LEVEL = TraceLevel.Critical
        elif '2' == arg:
            CURRENT_TRACE_LEVEL = TraceLevel.Major
        elif '3' == arg:
            CURRENT_TRACE_LEVEL = TraceLevel.Minor
        elif '4' == arg:
            CURRENT_TRACE_LEVEL = TraceLevel.Log
        elif '5' == arg:
            CURRENT_TRACE_LEVEL = TraceLevel.Info
        elif '10' == arg:
            CURRENT_TRACE_LEVEL = TraceLevel.Debug
        else:
            logMessage(TraceLevel.Critical,
                       "Trace Level " + str(arg) + " out of range. Defaulting to Critical.")
        endif
    elif opt == '-c':
        logMessage(TraceLevel.Debug,"Reading config file " + str(configFile))
        
        configFile = arg
        configParser = ConfigParser.RawConfigParser()
        configParser.read(configFile)

        wu_url = configParser.get('WeatherUnderground','url')
        wu_sw = configParser.get('WeatherUnderground','software')
        wu_stationId = configParser.get('WeatherUnderground','stationid')
        wu_password = configParser.get('WeatherUnderground','password')
        wu_software = configParser.get('WeatherUnderground','software')
        wu_humiditySensorId = configParser.getint('WeatherUnderground','humiditysensorid')
        wu_tempSensorId = configParser.getint('WeatherUnderground','tempsensorid')
        wu_rainSensorId = configParser.getint('WeatherUnderground','rainsensorid')
        wu_windSpeedSensorId = configParser.getint('WeatherUnderground','windspeedsensorid')
        wu_windDirSensorId = configParser.getint('WeatherUnderground','winddirsensorid')
        wu_pressureSensorId = configParser.getint('WeatherUnderground','barometersensorid')
        serverFileName = configParser.get('WeatherUnderground','serverfile')
        
        dbHost = configParser.get('Database', 'host')
        dbName = configParser.get('Database', 'database_name')
        dbUser = configParser.get('Database', 'user')
        dbPassword = configParser.get('Database', 'password')
        dbPrefix = configParser.get('Database', 'prefix')

        try:
            dbConnection = mysql.connector.connect(user=dbUser,
                                                        password=dbPassword,
                                                        host=dbHost,
                                                        database=dbName)
            
            cursor = dbConnection.cursor()
        except mysql.connector.Error as err:
            logMessage(TraceLevel.Abort,"Database failure!")
            sys.exit(2)
        endtry

        wu_url += ("?action=updateraw&ID=" +
                   str(wu_stationId) +
                   "&PASSWORD=" + str(wu_password))

        timeStamp = ""

        sections = configParser.sections()
        for section in sections:
            logMessage(TraceLevel.Debug,"Section: " + str(section))

            queryCmd = ""
            
            if string.find(section,"Device") >= 0:
                deviceSerialNumber = configParser.get(section,'serialnumber')
                deviceName =  configParser.get(section,'name')
                deviceSensorid = configParser.getint(section,'sensorid')
                deviceTableName = configParser.get(section,'tablename')

                if deviceSensorid == wu_humiditySensorId:
                    foundHumidity = True
                    queryCmd = ("select * from " +
                                str(deviceTableName) +
                                " where sensorid=" + str(deviceSensorid) +
                                " order by timeslot desc limit 1")
                    logMessage(TraceLevel.Info, str(queryCmd))
                    cursor.execute(queryCmd)

                    rows = cursor.fetchall()
                    humidity = rows[0][3]
                    timeStamp = rows[0][1]
                    logMessage(TraceLevel.Info,"Humidity " +
                               "Min: " + str(rows[0][2]) +
                               " Average: " + str(rows[0][3]) +
                               " Max: " + str(rows[0][4]))

                    wu_url += "&humidity=" + str(round(humidity,2))
                    
                elif deviceSensorid == wu_tempSensorId:
                    foundTemperature = True
                    queryCmd = ("select * from " +
                                str(deviceTableName) +
                                " where sensorid=" + str(deviceSensorid) +
                                " order by timeslot desc limit 1")
                    logMessage(TraceLevel.Info, str(queryCmd))
                    cursor.execute(queryCmd)
                    rows = cursor.fetchall()
                    temperature = rows[0][3]
                    timeStamp = rows[0][1]
                    logMessage(TraceLevel.Info,"Temperature " +
                               "Min: " + str(rows[0][2]) +
                               " Average: " + str(rows[0][3]) +
                               " Max: " + str(rows[0][4]))
                    wu_url += "&tempf=" + str(round(temperature,2))
                elif deviceSensorid == wu_rainSensorId:
                    queryCmd = ("select * from " +
                                str(deviceTableName) +
                                " where sensorid=" + str(deviceSensorid) +
                                " order by timeslot desc limit 1")
                    logMessage(TraceLevel.Info, str(queryCmd))
                    cursor.execute(queryCmd)
                    rows = cursor.fetchall()
                    timeStamp = rows[0][1]

                    oneHourAgo = timeStamp - timedelta(hours=1)

                    queryCmd = ("select sum(dsum) as rainin from " +
                                str(deviceTableName) +
                                " where timeslot >= \"" +
                                str(oneHourAgo)  + "\"" +
                                " and timeslot <= \"" +
                                str(timeStamp) + "\"" +
                                " order by timeslot")
                    
                    logMessage(TraceLevel.Info, str(queryCmd))
                    cursor.execute(queryCmd)
                    rows = cursor.fetchall()
                    rainin = rows[0][0]

                    today = timeStamp.date()
                    queryCmd = ("select sum(dsum) as dailyrainin from " +
                                str(deviceTableName) +
                                " where sensorid=" +
                                str(deviceSensorid) +
                                " and timeslot like " +
                                "\"" + str(today) + "%\"")
                    
                    logMessage(TraceLevel.Info, str(queryCmd))
                    cursor.execute(queryCmd)
                    rows = cursor.fetchall()
                    dailyRain = rows[0][0]
                    
                    wu_url += ("&dailyrainin=" + str(round(dailyRain,2)) +
                            "&rainin=" + str(round(rainin,2)))

                elif deviceSensorid == wu_windSpeedSensorId:
                    queryCmd = ("select * from " +
                                str(deviceTableName) +
                                " where sensorid=" + str(deviceSensorid) +
                                " order by timeslot desc limit 1")
                    logMessage(TraceLevel.Info, str(queryCmd))
                    
                    cursor.execute(queryCmd)
                    rows = cursor.fetchall()
                    windSpeed = rows[0][3]
                    windGust = rows[0][4]                
                    timeStamp = rows[0][1]
                    logMessage(TraceLevel.Info,"Wind Speed " +
                               "Min: " + str(rows[0][2]) +
                               " Average: " + str(rows[0][3]) +
                               " Max: " + str(rows[0][4]))
                    wu_url += ("&windspeedmph=" + str(round(windSpeed,2)) +
                            "&windgustmph=" + str(round(windGust,2)))
                    
                elif deviceSensorid == wu_windDirSensorId:
                    queryCmd = ("select * from " +
                                str(deviceTableName) +
                                " where sensorid=" + str(deviceSensorid) +
                                " order by timeslot desc limit 1")
                    logMessage(TraceLevel.Info, str(queryCmd))
                    cursor.execute(queryCmd)
                    rows = cursor.fetchall()
                    windDir = rows[0][2]
                    timeStamp = rows[0][1]
                    logMessage(TraceLevel.Info,"Wind Dir " +
                               "Direction: " + str(rows[0][2]))
                    wu_url += "&winddir=" + str(round(windDir,2))
                            
                elif deviceSensorid == wu_pressureSensorId:
                    queryCmd = ("select * from " +
                                str(deviceTableName) +
                                " where sensorid=" + str(deviceSensorid) +
                                " order by timeslot desc limit 1")
                    logMessage(TraceLevel.Info, str(queryCmd))
                    cursor.execute(queryCmd)
                    rows = cursor.fetchall()
                    pressure = rows[0][3]
                    timeStamp = rows[0][1]
                    logMessage(TraceLevel.Info,"Barometric Pressure " +
                               "Min: " + str(rows[0][2]) +
                               " Average: " + str(rows[0][3]) +
                               " Max: " + str(rows[0][4]))
                    wu_url += "&baromin=" + str(round(pressure,2))                    
                endif
            endif
        endfor
    endif
endfor

if foundTemperature and foundHumidity:
    tempC = 5.0/9.0*(temperature - 32.0)
    dewptC = 237.3/( 7.5 / ( math.log10(humidity) + (( 7.5 * tempC) / ( 237.3 + tempC)) - 2 ) - 1 )
    dewPoint = (9.0/5.0) * dewptC + 32
    wu_url += "&dewptf=" + str(round(dewPoint,2))
endif

utcTimeStamp = time.mktime(timeStamp.timetuple())
utcTime = datetime.utcfromtimestamp(utcTimeStamp)

utcTime = str(utcTime).replace(" ", "+")
utcTime = utcTime.replace(":", "%3A")

wu_url += "&dateutc=" + str(utcTime)
wu_url += "&softwaretype=" + str(wu_software).replace(" ", "+")

logMessage(TraceLevel.Log, str(wu_url))

response = ""
content = ""
resp, content = httplib2.Http().request(wu_url)
logMessage(TraceLevel.Log, str(response) + " " + str(content))

logMessage(TraceLevel.Log, str(serverFileName))

if serverFileName != "":
    degree_sign = (u'\N{DEGREE SIGN}')
    degree_sign.encode('utf-8')

    if (windDir >= 0 and windDir <= 11.25): 
        windText="N"
    elif (windDir >= 11.25 and windDir <= 33.75): 
        windText="NNE"
    elif (windDir >= 33.75 and windDir <= 56.25): 
        windText="NE"
    elif (windDir >= 56.25 and windDir <= 78.75): 
        windText="ENE"
    elif (windDir >= 78.75 and windDir <= 101.25): 
        windText="E"
    elif (windDir >= 101.25 and windDir <= 123.75): 
        windText="ESE"
    elif (windDir >= 123.75 and windDir <= 146.25): 
        windText="SE"
    elif (windDir >= 146.25 and windDir <= 168.75): 
        windText="SSE"
    elif (windDir >= 168.75 and windDir <= 191.25): 
        windText="S"
    elif (windDir >= 191.25 and windDir <= 213.75): 
        windText="SSW"
    elif (windDir >= 213.75 and windDir <= 236.25): 
        windText="SW"
    elif (windDir >= 236.25 and windDir <= 258.75): 
        windText="WSW"
    elif (windDir >= 258.75 and windDir <= 281.25): 
        windText="W"
    elif (windDir >= 281.25 and windDir <= 303.75): 
      windText="WNW"
    elif (windDir >= 303.75 and windDir <= 326.25): 
        windText="NW"
    elif (windDir >= 326.25 and windDir <= 348.75): 
        windText="NNW"
    elif (windDir >= 348.75 and windDir <= 360): 
        windText="N"
    else:
        windText="N"
        logMessage(TraceLevel.Critical, "Invalid wind direction: " +
                   str(windDir))
    endif

    dataString = (str(round(temperature,1)) + degree_sign.encode('utf-8') + "/" +
                  str(int(humidity)) + "%" + "/" +
                  str(round(windSpeed,1)) + "/" +
                  str(round(windGust,1)) + "/" +
                  str(windText) + "/" +
                  str(round(dailyRain,2)) + "/" +
                  str(round(pressure,2)) + "/" +
                  str(round(rainin,2)) )
     
    logMessage(TraceLevel.Debug, "Writing to " + str(serverFileName))
    
    with open(serverFileName, 'w') as f:
        f.write(dataString)
    endwith
endif

endmain
