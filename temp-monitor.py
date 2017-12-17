#!/usr/bin/env python

# Import smtplib for the actual sending function
import syslog, getopt
import smtplib
import email
from email.mime.text import MIMEText
import sys
import time
from datetime import datetime
import os.path
from subprocess import call
from mydefs import *
from ConfigParser import SafeConfigParser
from enum import IntEnum
import mysql.connector

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

MAX_RAIN_RATE = 1

def logMessage(level, msg):
    if ( level <= CURRENT_TRACE_LEVEL):
        print str(datetime.now()) + ": " + msg
        syslog.syslog(msg)
    endif
enddef

#================== Main =============================
main

configFile = ''

try:    
    opts, args = getopt.getopt(sys.argv[1:],"t:c:")
except getopt.GetoptError:
    logMessage(TraceLevel.Abort, "Usage: temp-monitor.py -t tracelevel -c configFile")
    sys.exit(2)
endtry

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
        configFile = arg
        logMessage(TraceLevel.Info,"Reading config file " + str(configFile))
    endif
endfor

if configFile == "":
    logMessage(TraceLevel.Abort, "No Config File! Usage: temp-monitor.py -t tracelevel -c configFile")
    sys.exit(2)
endif

logMessage(TraceLevel.Info, "Config File: " + str(configFile))

configParser = SafeConfigParser()
configParser.read(configFile)

        
dbHost = configParser.get('Database', 'host')
dbName = configParser.get('Database', 'database_name')
dbUser = configParser.get('Database', 'user')
dbPassword = configParser.get('Database', 'password')
dbPrefix = configParser.get('Database', 'prefix')
dbTableName = configParser.get('Database','tablename')
deviceSensorid = configParser.get('Database','sensorid')

minTemp = int(configParser.get('Range', 'min'))
maxTemp = int(configParser.get('Range', 'max'))

me = configParser.get('Email', 'originator')
smtp = configParser.get('Email', 'smtp')
smtpPort = configParser.get('Email', 'smtpPort')
password = configParser.get('Email', 'password')

logMessage(TraceLevel.Debug,
           "Src Address: " + str(me) +
           " smtp host: " + str(smtp) +
           " smtp port: " + str(smtpPort))
        
users = []
addresses = []
for name in configParser.options('Notifications'):
    string_value = configParser.get('Notifications', name)
    users.append(name)
    addresses.append(string_value)
endfor
            
logMessage(TraceLevel.Debug,
           "Starting Temperature Monitor. Monitoring Range " +
           str(minTemp) + "-" + str(maxTemp))
            
            
you = ''
            
for i in range(len(users)):
    if 0 == i:
        you = addresses[i]
    else: 
        you = you + ';' + addresses[i]
    endif
endfor
                    
logMessage(TraceLevel.Debug, "Notification List: " + str(you))


thresholdCrossedFileName = '/tmp/thresholdCrossed'
thresholdAlreadyCrossed = os.path.exists(thresholdCrossedFileName)
                            
temperature = (minTemp + maxTemp) / 2
                      
try:
    logMessage(TraceLevel.Debug, "DB User: " + str(dbUser) +
               " Password: " + str(dbPassword) +
               " Host: " + str(dbHost) +
               " DB Name: " + str(dbName))
    
    dbConnection = mysql.connector.connect(user=dbUser,
                                           password=dbPassword,
                                           host=dbHost,
                                           database=dbName)

    logMessage(TraceLevel.Debug, "DB connection successful.")
            
    cursor = dbConnection.cursor()

    logMessage(TraceLevel.Debug, "cursor successful.")
    
    queryCmd = ("select * from " +
                str(dbTableName) +
                " where sensorid=" + str(deviceSensorid) +
                " order by timeslot desc limit 1")
    logMessage(TraceLevel.Info, str(queryCmd))
    
    cursor.execute(queryCmd)
    rows = cursor.fetchall()
    temperature = rows[0][3]
except:
    logMessage(TraceLevel.Abort, 'Error reading Database.')
    sys.exit()
endtry

sendAlert = False;
txt = ''
dt = datetime.now()
dt = dt.replace(microsecond=0)

logMessage(TraceLevel.Debug, "Current Temperature: " + str(temperature))
            
if False == thresholdAlreadyCrossed:
    if temperature < minTemp:
        txt = 'Min Temp threshhold %3.2f crossed @ %s: %3.2f' % (minTemp, dt, temperature)
        sendAlert = True;
        call(['touch','%s' % thresholdCrossedFileName])
    endif
    if temperature > maxTemp:
        txt = 'Max Temp threshold %3.2f crossed @ %s: %3.2f' % (maxTemp, dt, temperature)
        sendAlert = True;
        call(['touch','%s' % thresholdCrossedFileName])
    endif
else:
    if temperature > minTemp and temperature < maxTemp:
        call(['rm', '%s' % thresholdCrossedFileName])
        txt = '%3.2f in range of %3.2f-%3.2f @ %s' % (temperature, minTemp, maxTemp, dt)
        sendAlert = True;
    else:
        logMessage(TraceLevel.Log,
                   "Temperature of %3.2f still outside of range %3.2f-%3.2f" % (temperature, minTemp, maxTemp))
    endif
endif

if True == sendAlert: 
    msg = MIMEText(txt)
    msg['Subject'] = 'Temperature Monitor Alert!'
    msg['From'] = me 
                        
    for i in range(len(users)):
        you = addresses[i]
        msg['To'] = you 
                        
        try:
            s = smtplib.SMTP('%s:%s' % (smtp, smtpPort))
            s.login(me, password)
            s.sendmail(me, [you], msg.as_string())
            s.quit()
            logMessage(TraceLevel.Log, 'Temperature Monitor sent Alert to %s, Current Temperature: %f.' % (you, temperature))
            logMessage(TraceLevel.Log,txt)
        except:
            logMessage(TraceLevel.Major, 'Error sending Email: %s' % (sys.exc_info()[0]))
        endtry
    endfor
endmain
