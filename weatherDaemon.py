#! /usr/bin/env python
#
# Program to gather data from 1-wire weather sensors and commit them to a database
# Copyright 2014, Kevin Canady (kevin@kevincanady.com)
#
#Inspired by:
# One Wire File System Weather Station
# Tim Sailer
# Coastal Internet, Inc
#
# usage: weatherDaemon.py -c configFileName -t outputLevel
#
# The outputLevel determines the level of verbose output from the software.
# Levels run from 1-10, 1 being the most Critical, 10 being the most verbose.
# The output is sent both to stdout and the system log.
#
# This program assumes that a mySQL database and a owserver server are operating.
# It assumes the database: "weather" exists and has the following tables and structures:
##+---------------------+
##| Tables_in_weather:
##+---------------------+
##
##| data_barometer:
##+-----------+----------------------+------+-----+---------------------+-------+
##| Field     | Type                 | Null | Key | Default             | Extra |
##+-----------+----------------------+------+-----+---------------------+-------+
##| sensorid  | tinyint(3) unsigned  | NO   | PRI | 0                   |       |
##| timeslot  | datetime             | NO   | PRI | 0000-00-00 00:00:00 |       |
##| dmin      | float                | NO   |     | 0                   |       |
##| davg      | float                | NO   |     | 0                   |       |
##| dmax      | float                | NO   |     | 0                   |       |
##| sampcount | smallint(5) unsigned | NO   |     | 0                   |       |
##+-----------+----------------------+------+-----+---------------------+-------+
##
##| data_humidity :
##+-----------+----------------------+------+-----+---------------------+-------+
##| Field     | Type                 | Null | Key | Default             | Extra |
##+-----------+----------------------+------+-----+---------------------+-------+
##| sensorid  | tinyint(3) unsigned  | NO   | PRI | 0                   |       |
##| timeslot  | datetime             | NO   | PRI | 0000-00-00 00:00:00 |       |
##| dmin      | float                | NO   |     | 0                   |       |
##| davg      | float                | NO   |     | 0                   |       |
##| dmax      | float                | NO   |     | 0                   |       |
##| sampcount | smallint(5) unsigned | NO   |     | 0                   |       |
##+-----------+----------------------+------+-----+---------------------+-------+
##
##| data_lightning:
##+-----------+----------------------+------+-----+---------------------+-------+
##| Field     | Type                 | Null | Key | Default             | Extra |
##+-----------+----------------------+------+-----+---------------------+-------+
##| sensorid  | tinyint(3) unsigned  | NO   | PRI | 0                   |       |
##| timeslot  | datetime             | NO   | PRI | 0000-00-00 00:00:00 |       |
##| dsum      | float                | NO   |     | 0                   |       |
##| sampcount | smallint(5) unsigned | NO   |     | 0                   |       |
##+-----------+----------------------+------+-----+---------------------+-------+
##
##| data_rain:
##+-----------+----------------------+------+-----+---------------------+-------+
##| Field     | Type                 | Null | Key | Default             | Extra |
##+-----------+----------------------+------+-----+---------------------+-------+
##| sensorid  | tinyint(3) unsigned  | NO   | PRI | 0                   |       |
##| timeslot  | datetime             | NO   | PRI | 0000-00-00 00:00:00 |       |
##| dsum      | float                | NO   |     | 0                   |       |
##| sampcount | smallint(5) unsigned | NO   |     | 0                   |       |
##+-----------+----------------------+------+-----+---------------------+-------+
##
##| data_solar:
##+-----------+----------------------+------+-----+---------------------+-------+
##| Field     | Type                 | Null | Key | Default             | Extra |
##+-----------+----------------------+------+-----+---------------------+-------+
##| sensorid  | tinyint(3) unsigned  | NO   | PRI | 0                   |       |
##| timeslot  | datetime             | NO   | PRI | 0000-00-00 00:00:00 |       |
##| dmin      | float                | NO   |     | 0                   |       |
##| davg      | float                | NO   |     | 0                   |       |
##| dmax      | float                | NO   |     | 0                   |       |
##| sampcount | smallint(5) unsigned | NO   |     | 0                   |       |
##+-----------+----------------------+------+-----+---------------------+-------+
##
##| data_temperature:
##+-----------+----------------------+------+-----+---------------------+-------+
##| Field     | Type                 | Null | Key | Default             | Extra |
##+-----------+----------------------+------+-----+---------------------+-------+
##| sensorid  | tinyint(3) unsigned  | NO   | MUL | 0                   |       |
##| timeslot  | datetime             | NO   | MUL | 0000-00-00 00:00:00 |       |
##| dmin      | float                | NO   |     | 0                   |       |
##| davg      | float                | NO   |     | 0                   |       |
##| dmax      | float                | NO   |     | 0                   |       |
##| sampcount | smallint(5) unsigned | NO   |     | 0                   |       |
##+-----------+----------------------+------+-----+---------------------+-------+
##
##| data_wind_direction:
##+-----------+----------------------+------+-----+---------------------+-------+
##| Field     | Type                 | Null | Key | Default             | Extra |
##+-----------+----------------------+------+-----+---------------------+-------+
##| sensorid  | tinyint(3) unsigned  | NO   | PRI | 0                   |       |
##| timeslot  | datetime             | NO   | PRI | 0000-00-00 00:00:00 |       |
##| davgx     | float                | NO   |     | 0                   |       |
##| davgy     | float                | NO   |     | 0                   |       |
##| sampcount | smallint(5) unsigned | NO   |     | 0                   |       |
##+-----------+----------------------+------+-----+---------------------+-------+
##
##| data_wind_speed:
##+-----------+----------------------+------+-----+---------------------+-------+
##| Field     | Type                 | Null | Key | Default             | Extra |
##+-----------+----------------------+------+-----+---------------------+-------+
##| sensorid  | tinyint(3) unsigned  | NO   | PRI | 0                   |       |
##| timeslot  | datetime             | NO   | PRI | 0000-00-00 00:00:00 |       |
##| dmin      | float                | NO   |     | 0                   |       |
##| davg      | float                | NO   |     | 0                   |       |
##| dmax      | float                | NO   |     | 0                   |       |
##| sampcount | smallint(5) unsigned | NO   |     | 0                   |       |
##+-----------+----------------------+------+-----+---------------------+-------+
##
## The field 'sensorid' must be a unique integer value assigned to each defined device.
##
## Different sensors can be on the same physical device. For example a
## combo temperature/humidity sensor. This one physical device should be defined
## in the config file as two seperate devices, differing only by the sensorid value
## assigned to them.
##
## Likewise, multiple devices of the same type can be defined to use the same database table.
## For example, one might have multiple temperature devices, one indoors, one
## outdoors. They can share the same database table. The different sensor values
## are distinquished by the different sensorid values assigned.
##
## The config file format is as follows:
## 
##[General]
##lowSpeedRate=30 #seconds between reads of low speed devices such as temperature and pressure
##highSpeedRate=1 #seconds between reads of high speed devices such as wind speed/direction
##commitRate=120 #seconds between commits of data to database
##wind_speed_uom=mph 
##barometric_pressure_uom=inhg
##
##[Database]
##host=localhost
##database_name=weather
##user=kevin
##password=kevin
##prefix=""
##
## Each "Devicexx" section describes one logical device. This section name must be unique.
## There is no relationship between the "xx" number and the sensorid value.
## Valid type parameters:
##        temp, wind_speed, wind_dir, rain, pressure, humidity
## The wind direction sensor type has the following additional parameters:
##   Direction offsets in case the North value of the sensor doesn't line up with zero
##   Text for direction names
##   Min and Max voltage values for each direction.
##   The software assumes 16 direction values, starting with North=0 and moving clockwise
##   around the compass. It assumes 22.5 degrees between each direction value.
##
## Devices can share the same physical address. For example a combo temperature/humidity
## sensor can be split into separate logical devices each with it's own "Devicexx" section.
## In this case the sensorid value must differ.
## Each device can be on a separate 1-wire bus. The physical address of each sensor
## is determined by the host and port of the owserver and the serialnumber of the
## physical device.
##
## Examples:
##
##[Device1] 
##type=temp
##bus=bus.0
##host=localhost
##port=4304
##options=-F
##serialnumber=10.2B024D010800
##name="Inside Temperature"
##calibmult=1 
##calibadd=0 
##speed=low
##tablename=data_temperature
##sensorid=2
##
##[Device2]
##type=wind_speed
##bus=bus.0
##speed=high
##host=localhost
##port=4304
##options=""
##serialnumber=1D.8DBF0D000000
##name="Wind Speed"
##calibmult=1.25
##calibadd=0
##tablename=data_wind_speed
##sensorid=3
##
##[Device3]
##type=wind_dir
##subtype=[inspeed | ads]
##bus=bus.0
##speed=high
##host=localhost
##port=4304
##options=""
##serialnumber=26.694DE7000000
##name="Wind Direction"
##calibmult=1
##calibadd=0
##tablename=data_wind_direction
##sensorid=4
##
##noffset=0
##nneoffset=22.5
##neoffset=45
##eneoffset=67.5
##eoffset=90
##eseoffset=112.5
##seoffset=135
##sseoffset=157.5
##soffset=180
##sswoffset=202.5
##swoffset=225
##wswoffset=247.5
##woffset=270
##wnwoffset=292.5
##nwoffset=315
##nnwoffset=337.5
##
##ntext=N
##nnetext=NNE
##netext=NE
##enetext=ENE
##etext=E
##esetext=ESE
##setext=SE
##ssetext=SSE
##stext=S
##sswtext=SSW
##swtext=SW
##wswtext=WSW
##wtext=W
##wnwtext=WNW
##nwtext=NW
##nnwtext=NNW
##
##nminvolt=2.65
##nmaxvolt=2.72
##
##nneminvolt=6.45
##nnemaxvolt=6.55
##
##neminvolt=5.92
##nemaxvolt=6.02
##
##eneminvolt=9.32
##enemaxvolt=9.41
##
##eminvolt=9.23
##emaxvolt=9.33
##
##eseminvolt=9.46
##esemaxvolt=9.56
##
##seminvolt=8.45
##semaxvolt=8.54
##
##sseminvolt=8.95
##ssemaxvolt=9.04
##
##sminvolt=7.53
##smaxvolt=7.63
##
##sswminvolt=7.92
##sswmaxvolt=8.01
##
##swminvolt=4.26
##swmaxvolt=4.34
##
##wswminvolt=4.58
##wswmaxvolt=4.65
##
##wminvolt=0.89
##wmaxvolt=0.95
##
##wnwminvolt=2.20
##wnwmaxvolt=2.26
##
##nwminvolt=1.54
##nwmaxvolt=1.60
##
##nnwminvolt=3.53
##nnwmaxvolt=3.60
##
##
##[Device4]
##type=rain
##bus=bus.0
##speed=low
##host=localhost
##port=4304
##options=""
##serialnumber=1D.9CFB09000000
##name="Rain"
##calibmult=0.01
##calibadd=0
##tablename=data_rain
##sensorid=1
##
##[Device5]
##type=temp
##bus=bus.0
##speed=low
##host=localhost
##port=4304
##options=-F
##serialnumber=26.B2CBA8000000
##name="Outside Temperature"
##calibmult=1
##calibadd=0
##tablename=data_temperature
##sensorid=6
##
##[Device6]
##type=pressure
##bus=bus.0
##speed=low
##host=localhost
##port=4304
##options=""
##serialnumber=26.7FBCB5000000
##name="Barometric Pressure"
##calibmult=0.6727
##calibadd=26.6546
##tablename=data_barometer
##sensorid=7
##
##[Device7]
##type=humidity
##bus=bus.0
##speed=low
##host=localhost
##port=4304
##options=-F
##serialnumber=26.B2CBA8000000
##name="Outside Humidity"
##calibmult=1
##calibadd=0
##tablename=data_humidity
##sensorid=8


import sys, getopt
import signal
from threading import Timer
from time import sleep
from datetime import datetime
from mydefs import *
import ping, socket
import syslog
from enum import IntEnum
import ConfigParser
import random
import string
import mysql.connector
import pyownet
from pyownet import protocol
import time

killSignal = False
DEBUG = False
g_sensorArrays = {}

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

def signal_handler(signal, frame):
    global killSignal
    logMessage(TraceLevel.Abort, 'Killing Process!')
    killSignal = True

    for sensorArray in g_sensorArrays:
        sensorArray.cancel()
    endfor
    
    sys.exit(0)
enddef

class MySensor(object):
    def __init__(self, sensorid, sensorType, name, calibMult, calibAdd, bus, host, port, options, serialNumber):
        self.sensorId = sensorid
        self.sensorType = sensorType
        self.name = name
        self.calibMult = calibMult
        self.calibAdd = calibAdd
        self.bus = bus
        self.host = host
        self.port = port
        self.options = options
        self.serialNumber = serialNumber

        try:
            self.owserverConnection = protocol.OwnetProxy(host=self.host,
                                                          port=self.port,
                                                          flags=pyownet.protocol.FLG_TEMP_F)
        except:
            logMessage(TraceLevel.Abort,"Failed to connection to owserver!")
            exit(-1)
        endtry

        self.average = 0
        self.max = 0
        self.min = 0

        self.samples = []

        self.tableName = ""

        self.path = ""
        
        logMessage(TraceLevel.Log, "Created sensor " + str(self.name) +
                   " of type " + str(self.sensorType) +
                   " Multiplication Calibration: " + str(self.calibMult) +
                   " Addition Calibration: " + str(self.calibAdd) +
                   " Bus: " + str(self.bus) +
                   " Serial # " + str(self.serialNumber) +
                   " @ " + str(self.host) + ":" + str(self.port) + " " + str(self.options))
    enddef

    def read(self):
        logMessage(TraceLevel.Info, "Read sensor " + str(self.name) + " @ " + str(self.serialNumber))
    enddef

    def present(self):
        devicePresent = False
        
        try:
            devicePresent = self.owserverConnection.present(self.path)
        except:
            logMessage(TraceLevel.Critical,"Device Presence check failed!")
        endtry

        return devicePresent

    enddef

    def computeAverage(self):
        self.average = 0
        for sample in self.samples:
            self.average = self.average + sample
        endfor
        
        if len(self.samples) > 0:
            self.average = self.average/len(self.samples)
        else:
            logMessage(TraceLevel.Critical, "No samples for Device: " +
                       str(self.name) +
                       " @ " + str(self.serialNumber))
        endif
    enddef

    def commit(self):
        self.computeAverage()
        
        logMessage(TraceLevel.Info, "Commiting sensor data " + str(self.name) +
                   " @ " + str(self.serialNumber) +
                   " number of samples: " + str(len(self.samples)) +
                   ", Min: " + str(self.min) +
                   ", Max: " + str(self.max) +
                   ", Average: " + str(self.average))

        dbCmd = ("insert into " +
                 self.tableName +
                 "(sensorid,timeslot,dmin,davg,dmax,sampcount) values (" +
                 str(self.sensorId) +
                 ",\"" + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + "\"" +
                 ",\"" + str(self.min) + "\"" +
                 ",\"" + str(self.average) + "\"" +
                 ",\"" + str(self.max) + "\"" +
                 "," + str(len(self.samples)) + ")\n")


        del self.samples[:]

        return dbCmd
    enddef

    def storeSample(self, sample):

        if len(self.samples) == 0:
            self.min = sample
            self.max = sample
        else:
            if sample < self.min:
                self.min = sample
            endif
            if sample > self.max:
                self.max = sample
            endif
        endif

        self.samples.append(sample)
    enddef    

    def printInfo(self):
        logMessage(TraceLevel.Info, "Sensor " + str(self.name) + " is type " + str(self.sensorType) + " @ " + str(self.serialNumber))
    enddef
endclass


class TemperatureSensor(MySensor):
    def __init__(self, sensorid, name, calibMult, calibAdd, bus, host, port, options, serialNumber):
        super(TemperatureSensor, self).__init__(sensorid, 'temp', name, calibMult, calibAdd, bus, host, port, options, serialNumber)

        self.path = "/uncached/" + str(self.serialNumber) + "/temperature"
    enddef

    def read(self):
        
        logMessage(TraceLevel.Debug,
                   "Reading from self.path: " +
                   str(self.path))

        try:
            sample = float(self.owserverConnection.read(self.path))
        except:
            logMessage(TraceLevel.Critical,"Failed to read from Device " +
                       str(self.name) + " @ " + str(self.serialNumber) + "!")
            return
        endtry            

        sample = sample * self.calibMult + self.calibAdd

        self.storeSample(sample)
        
        logMessage(TraceLevel.Debug, "Reading Temperature sensor " + str(self.name) + " @ " + str(self.serialNumber) + " value: " + str(sample))
    enddef

endclass

class PressureSensor(MySensor):
    def __init__(self, sensorid, name, calibMult, calibAdd, bus, host, port, options, serialNumber):
        super(PressureSensor, self).__init__(sensorid, 'pressure', name, calibMult, calibAdd, bus, host, port, options, serialNumber)
        self.path = "/uncached/" + str(self.serialNumber) + "/VAD"
    enddef

    def read(self):
        logMessage(TraceLevel.Debug,
                   "Reading from self.path: " +
                   str(self.path))

        try:
            sample = float(self.owserverConnection.read(self.path))
        except:
            logMessage(TraceLevel.Critical,"Failed to read from Device " +
                       str(self.name) + " @ " + str(self.serialNumber) + "!")
            return
        endtry            

        sample = sample * self.calibMult + self.calibAdd

        self.storeSample(sample)

        logMessage(TraceLevel.Debug, "Reading Barometric Pressure sensor " + str(self.name) + " @ " + str(self.serialNumber))
    enddef

endclass

class RainSensor(MySensor):
    def __init__(self, sensorid, name, calibMult, calibAdd, bus, host, port, options, serialNumber):
        super(RainSensor, self).__init__(sensorid, 'rain', name, calibMult, calibAdd, bus, host, port, options, serialNumber)

        self.previousCounter = 0
        self.firstPass = True

        self.path = "/uncached/" + str(self.serialNumber) + "/counters.B"
    enddef

    def read(self):
        logMessage(TraceLevel.Debug,
                   "Reading from self.path: " +
                   str(self.path))
        
        try:
            sample = int(self.owserverConnection.read(self.path))
        except:
            logMessage(TraceLevel.Critical,"Failed to read from Device " +
                       str(self.name) + " @ " + str(self.serialNumber) + "!")
            return
        endtry            
            

        logMessage(TraceLevel.Info, "Rain sensor value: " + str(sample) +
                   " Previous Value: " + str(self.previousCounter))
        if self.previousCounter > sample:
            logMessage(TraceLevel.Info, "Previous Rain sensor value: " + str(self.previousCounter) +
                       " Exceeds Current Value: " + str(sample) + ". Discarding")            
            self.previousCounter = sample
            sample = 0
        else:
            tmp = sample
            sample = sample - self.previousCounter
            self.previousCounter = tmp
        endif


        if False == self.firstPass:
            sample = sample * self.calibMult + self.calibAdd
            if sample > MAX_RAIN_RATE:
                logMessage(TraceLevel.Critical, str(sample) +
                           "in Exceeded max rain rate of " +
                           str(MAX_RAIN_RATE))
            else:
                self.storeSample(sample)
            endif
        else:
            self.firstPass = False
            logMessage(TraceLevel.Info, "Initial Rain sensor value: " + str(sample))
        endif        

        logMessage(TraceLevel.Debug, "Reading Rain sensor " + str(self.name) + " @ " + str(self.serialNumber))
    enddef

    def commit(self):
        sum = 0
        for i in range(len(self.samples)):
            sum += self.samples[i]
        endfor

        logMessage(TraceLevel.Info, "Commiting sensor data " + str(self.name) +
                   " @ " + str(self.serialNumber) +
                   " number of samples: " + str(len(self.samples)) +
                   ", Accumulation: " + str(sum))
        
        dbCmd = ("insert into " +
                 self.tableName +
                 "(sensorid,timeslot,dsum,sampcount) values (" +
                 str(self.sensorId) +
                 ",\"" + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + "\"" +
                 ",\"" + str(sum) + "\"" +
                 "," + str(len(self.samples)) + ")\n")

        del self.samples[:]

        return dbCmd
    enddef
    
endclass

class WindSpeedSensor(MySensor):
    def __init__(self, sensorid, name, calibMult, calibAdd, bus, host, port, options, serialNumber):
        super(WindSpeedSensor, self).__init__(sensorid, 'wind_speed', name, calibMult, calibAdd, bus, host, port, options, serialNumber)

        self.previousTimeStamp = time.time()
        self.previousCounter = 0
        self.firstPass = True

        self.path = "/uncached/" + str(self.serialNumber) + "/counters.A"

        # perform read to initialize current time stamp and counter value
        self.read()
        
    enddef

    def read(self):
        logMessage(TraceLevel.Debug,
                   "Reading from self.path: " +
                   str(self.path))


        try:
            sample = int(self.owserverConnection.read(self.path))
        except:
            logMessage(TraceLevel.Critical,"Failed to read from Device " +
                       str(self.name) + " @ " + str(self.serialNumber) + "!")
            return
        endtry            

        timeStamp = time.time()

        counterDiff = sample - self.previousCounter
        self.previousCounter = sample

        timeDiff = timeStamp - self.previousTimeStamp
        self.previousTimeStamp = timeStamp

        if False == self.firstPass:
            
            counterDiff = counterDiff * self.calibMult + self.calibAdd
            counterDiff = counterDiff / timeDiff
            
            self.storeSample(counterDiff)
        else:
            self.firstPass = False
            logMessage(TraceLevel.Info, "First Wind Speed readings " +
                       " Counter: " + str(self.previousCounter) +
                       " Time Stamp: " + str(self.previousTimeStamp))
        endif

        logMessage(TraceLevel.Debug, "Reading Wind Speed sensor " + str(self.name) + " @ " + str(self.serialNumber))
    enddef

endclass

class WindDirectionSensor(MySensor):
    def __init__(self, sensorid, name, calibMult, calibAdd, bus, host, port, options, serialNumber):
        super(WindDirectionSensor, self).__init__(sensorid, 'wind_dir', name, calibMult, calibAdd, bus, host, port, options, serialNumber)

        #direction numbers start at zero = North and proceed clockwise around
        #the compass. Each direction number equals 22.5 degrees.
        self.directionOffset = []
        self.directionText = []
        self.directionMinVoltage = []
        self.directionMaxVoltage = []

        self.path = "/uncached/" + str(self.serialNumber) + "/VAD"

        self.numberOfDirections = 16

    enddef

    def read(self):
        logMessage(TraceLevel.Debug,
                   "Reading from self.path: " +
                   str(self.path))

        try:
            sample = float(self.owserverConnection.read(self.path))
        except:
            logMessage(TraceLevel.Critical,"Failed to read from Device " +
                       str(self.name) + " @ " + str(self.serialNumber) + "!")
            return
        endtry                        

        sample = sample * self.calibMult + self.calibAdd

        validSample = False

        ## Convert voltage into a direction number (0-15)
        for i in range(self.numberOfDirections):
            if sample >= self.directionMinVoltage[i] and sample <= self.directionMaxVoltage[i] :
                validSample = True
                self.storeSample(i)
            endif
        endfor

        if False == validSample :
            logMessage(TraceLevel.Log, "Invalid Wind Direction reading " +
                       str(self.name) + " @ " + str(self.serialNumber) +
                       " Reading: " + str(sample))
        endif
            

        logMessage(TraceLevel.Debug, "Reading Wind Direction sensor " + str(self.name) + " @ " + str(self.serialNumber))
    enddef

    def commit(self):
        # build up conensus averaging bins for the samples

        consensusAverageBins = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

        for i in range(len(self.samples)):
            if self.samples[i] < self.numberOfDirections:
                consensusAverageBins[self.samples[i]] += 1
            else:
                logMessage(TraceLevel.Major,"Invalid Direction number " +
                           str(self.samples[i]) +
                           " (shoud be between 0-" + str(self.numberOfDirections) + ")")
            endif
        endfor
        consensusAverageBins[16] = consensusAverageBins[0]
        consensusAverageBins[17] = consensusAverageBins[1]
        consensusAverageBins[18] = consensusAverageBins[2]
        consensusAverageBins[19] = consensusAverageBins[3]

        largestBin = 0
        greatestSum = 0

        for i in range(self.numberOfDirections):
            sum = (consensusAverageBins[i] +
                   consensusAverageBins[i+1] +
                   consensusAverageBins[i+2] +
                   consensusAverageBins[i+3] +
                   consensusAverageBins[i+4])

            if sum > greatestSum:
                greatestSum = sum
                largestBin = i
            endif
        endfor

        weightedSum = ( consensusAverageBins[largestBin+1] +
                        2 * consensusAverageBins[largestBin+2] +
                        3 * consensusAverageBins[largestBin+3] +
                        4 * consensusAverageBins[largestBin+4] ) * 45 / greatestSum

        degrees = largestBin * 45 + weightedSum;

        if degrees > 720:
            degrees -= 720
        endif

        degrees = degrees / 2

        # adjust for a non-zero north offset
        degrees += self.directionOffset[0]
        
        if degrees >= 360:
            degrees -= 360
        endif

        logMessage(TraceLevel.Info, "Commiting sensor data " + str(self.name) +
                   " @ " + str(self.serialNumber) +
                   " number of samples: " + str(len(self.samples)) +
                   ", Direction: " + str(degrees))

        dbCmd = ("insert into " +
                 self.tableName +
                 "(sensorid,timeslot,davgx,davgy,sampcount) values (" +
                 str(self.sensorId) +
                 ",\"" + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + "\"" +
                 ",\"" + str(degrees) + "\"" +
                 ",\"" + str(degrees) + "\"" +
                 "," + str(len(self.samples)) + ")\n")

        del self.samples[:]

        return dbCmd
    enddef

    def printInfo(self):
        super(WindDirectionSensor, self).printInfo()
        for i in range(self.numberOfDirections):
            logMessage(TraceLevel.Debug, str(self.directionText[i]) + 
                       " Offset: " + str(self.directionOffset[i]) +
                       " Min Voltage: " + str(self.directionMinVoltage[i]) +
                       " Max Voltage: " + str(self.directionMaxVoltage[i]))
    enddef
endclass

class InspeedWindDirectionSensor(MySensor):
    def __init__(self, sensorid, name, calibMult, calibAdd, bus, host, port, options, serialNumber):
        super(InspeedWindDirectionSensor, self).__init__(sensorid, 'wind_dir', name, calibMult, calibAdd, bus, host, port, options, serialNumber)

        #direction numbers start at zero = North and proceed clockwise around
        #the compass. Each direction number equals 22.5 degrees.
        self.directionOffset = []
        self.directionText = []

        self.path = "/uncached/" + str(self.serialNumber) + "/VAD"
        self.vddPath = "/uncached/" + str(self.serialNumber) + "/VDD"

        self.numberOfDirections = 16

    enddef

    def read(self):
        logMessage(TraceLevel.Debug,
                   "Reading from self.path: " +
                   str(self.path))

        try:
            vad = float(self.owserverConnection.read(self.path))
            vdd = float(self.owserverConnection.read(self.vddPath))
        except:
            logMessage(TraceLevel.Critical,"Failed to read from Device " +
                       str(self.name) + " @ " + str(self.serialNumber) + "!")
            return
        endtry                        

        validSample = True
        sample = (self.calibMult*(vad-(0.05*vdd)))/vdd
        if sample < 0:
            validSample = False
        else:
            ## Convert degrees into a direction number (0-15)
            intSample = int(sample/22.5)
            if intSample >= self.numberOfDirections:
                validSample = False
            endif
        endif

        if True == validSample:
            self.storeSample(intSample)
        endif

        if False == validSample :
            logMessage(TraceLevel.Log, "Invalid Wind Direction reading " +
                       str(self.name) + " @ " + str(self.serialNumber) +
                       " Reading: " + str(sample))
        endif

        logMessage(TraceLevel.Debug, "Reading Wind Direction sensor " + str(self.name) + " @ " + str(self.serialNumber))
    enddef

    def commit(self):
        # build up conensus averaging bins for the samples

        consensusAverageBins = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

        for i in range(len(self.samples)):
            if self.samples[i] < self.numberOfDirections:
                consensusAverageBins[self.samples[i]] += 1
            else:
                logMessage(TraceLevel.Major,"Invalid Direction number " +
                           str(self.samples[i]) +
                           " (shoud be between 0-" + str(self.numberOfDirections) + ")")
            endif
        endfor
        consensusAverageBins[16] = consensusAverageBins[0]
        consensusAverageBins[17] = consensusAverageBins[1]
        consensusAverageBins[18] = consensusAverageBins[2]
        consensusAverageBins[19] = consensusAverageBins[3]

        largestBin = 0
        greatestSum = 0

        for i in range(self.numberOfDirections):
            sum = (consensusAverageBins[i] +
                   consensusAverageBins[i+1] +
                   consensusAverageBins[i+2] +
                   consensusAverageBins[i+3] +
                   consensusAverageBins[i+4])

            if sum > greatestSum:
                greatestSum = sum
                largestBin = i
            endif
        endfor

        weightedSum = ( consensusAverageBins[largestBin+1] +
                        2 * consensusAverageBins[largestBin+2] +
                        3 * consensusAverageBins[largestBin+3] +
                        4 * consensusAverageBins[largestBin+4] ) * 45 / greatestSum

        degrees = largestBin * 45 + weightedSum;

        if degrees > 720:
            degrees -= 720
        endif

        degrees = degrees / 2

        # adjust for a non-zero north offset
        degrees += self.directionOffset[0]
        
        if degrees >= 360:
            degrees -= 360
        endif

        logMessage(TraceLevel.Info, "Commiting sensor data " + str(self.name) +
                   " @ " + str(self.serialNumber) +
                   " number of samples: " + str(len(self.samples)) +
                   ", Direction: " + str(degrees))

        dbCmd = ("insert into " +
                 self.tableName +
                 "(sensorid,timeslot,davgx,davgy,sampcount) values (" +
                 str(self.sensorId) +
                 ",\"" + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + "\"" +
                 ",\"" + str(degrees) + "\"" +
                 ",\"" + str(degrees) + "\"" +
                 "," + str(len(self.samples)) + ")\n")

        del self.samples[:]

        return dbCmd
    enddef

    def printInfo(self):
        logMessage(TraceLevel.Info, "Inspeed Wind Direction")
        super(InspeedWindDirectionSensor, self).printInfo()
        for i in range(self.numberOfDirections):
            logMessage(TraceLevel.Debug, str(self.directionText[i]) + 
                       " Offset: " + str(self.directionOffset[i]))
        endfor
    enddef
endclass

class HumiditySensor(MySensor):
    def __init__(self, sensorid, name, calibMult, calibAdd, bus, host, port, options, serialNumber):
        super(HumiditySensor, self).__init__(sensorid, 'humidity', name, calibMult, calibAdd, bus, host, port, options, serialNumber)

        self.path = "/uncached/" + str(self.serialNumber) + "/humidity"
    enddef

    def read(self):
        logMessage(TraceLevel.Debug,
                   "Reading from self.path: " +
                   str(self.path))

        try:
            sample = float(self.owserverConnection.read(self.path))
        except:
            logMessage(TraceLevel.Critical,"Failed to read from Device " +
                       str(self.name) + " @ " + str(self.serialNumber) + "!")
            return
        endtry                        

        sample = sample * self.calibMult + self.calibAdd

        self.storeSample(sample)

        logMessage(TraceLevel.Debug, "Reading Humidity sensor " + str(self.name) + " @ " + str(self.serialNumber))
    enddef

endclass


class MyTimer(object):
    def __init__(self, name, seconds):
        self.name = name
        self.seconds = seconds
        
        self.timer = Timer(self.seconds,self.myTimerCallback)
    enddef
    
    def myTimerCallback(self):
        logMessage(TraceLevel.Debug,"Timer " + str(self.name))
        
        if ( killSignal == False ) :
            self.timer = Timer(self.seconds,self.myTimerCallback)
            self.timer.start()
        endif
    enddef

    def start(self) :
        self.timer.start()
    enddef

    def cancel(self) :
        self.timer.cancel()
    enddef
    
endclass

class SensorArray(MyTimer):
    def __init__(self, sensors, name, seconds):
        self.sensors = sensors
        super(SensorArray, self).__init__(name,seconds)
    enddef
    
    def myTimerCallback(self):
        logMessage(TraceLevel.Debug,"SensorArray timeout")
        
        for sensor in self.sensors:
            sensor.read()
        endfor
        
        super(SensorArray, self).myTimerCallback()
    enddef    
endclass


class CommitTimer(MyTimer):
    def __init__(self, sensors, name, seconds, user, password, host, dbase):
        self.sensors = sensors
        
        try:
            self.dbConnection = mysql.connector.connect(user=user,
                                                        password=password,
                                                        host=host,
                                                        database=dbase)
            self.cursor = self.dbConnection.cursor()
            
        except mysql.connector.Error as err:
            logMessage(TraceLevel.Abort,"Database failure!")
            sys.exit(2)
        endtry

        super(CommitTimer, self).__init__(name,seconds)
    enddef
    
    def myTimerCallback(self):
        logMessage(TraceLevel.Info,"Commiting sensor info to database.")
        
        for sensor in self.sensors:
            commitCmd = sensor.commit()
            logMessage(TraceLevel.Info, commitCmd)

            if DEBUG == False:
                self.cursor.execute(commitCmd)
            else:
                logMessage(TraceLevel.Major,"In Debug mode. Not commiting sensor info to database: " + commitCmd)
            endif
        endfor
        
        super(CommitTimer, self).myTimerCallback()
    enddef    
endclass

#>>>>>>>>>>>>>>>>>>>Begin Main Here <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
main

cmdLine = ""

for arg in sys.argv:
    cmdLine += " " + arg
endfor
logMessage(TraceLevel.Critical,cmdLine)

try:    
    opts, args = getopt.getopt(sys.argv[1:],"t:d:c:")
except getopt.GetoptError:
    logMessage(TraceLevel.Abort, "Usage: weatherDaemon.py -t tracelevel -c configFile [-d]")
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
lowSpeedSensors = []
highSpeedSensors = []
lowSpeedRate=30
highSpeedRate=0.1
commitRate=120

if DEBUG == "True":
    logMessage(TraceLevel.Critical,"Running in Debug Mode. No dBase updates performed!")
endif

for opt, arg in opts:
    if opt == '-d':
        DEBUG = True
        logMessage(TraceLevel.Critical,"Running in Debug Mode. No dBase updates performed!")
    elif opt == '-t':
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
        logMessage(TraceLevel.Info,"Reading config file " + str(configFile))
        
        configFile = arg
        configParser = ConfigParser.RawConfigParser()
        configParser.read(configFile)

        sections = configParser.sections()
        for section in sections:
            logMessage(TraceLevel.Info,"Section: " + str(section))
            
            if string.find(section,"Device") >= 0:
                deviceType = configParser.get(section,'type')
                deviceBus = configParser.get(section,'bus')
                deviceSpeed = configParser.get(section,'speed')
                deviceSerialNumber = configParser.get(section,'serialnumber')
                deviceName =  configParser.get(section,'name')
                deviceCalibrationMultiplier = configParser.getfloat(section,'calibmult')
                deviceCalibrationAddition = configParser.getfloat(section,'calibadd')
                deviceHost = configParser.get(section,'host')
                devicePort = configParser.getint(section,'port')
                deviceOptions = configParser.get(section,'options')
                deviceSensorid = configParser.getint(section,'sensorid')
                
                device = None
                
                if deviceType == "temp":
                    device = TemperatureSensor(deviceSensorid, deviceName, deviceCalibrationMultiplier, deviceCalibrationAddition, deviceBus, deviceHost, devicePort, deviceOptions, deviceSerialNumber)
                elif deviceType == "rain":
                    device = RainSensor(deviceSensorid,  deviceName, deviceCalibrationMultiplier, deviceCalibrationAddition, deviceBus, deviceHost, devicePort, deviceOptions, deviceSerialNumber)
                elif deviceType == "wind_speed":
                    device =   WindSpeedSensor(deviceSensorid,  deviceName, deviceCalibrationMultiplier, deviceCalibrationAddition, deviceBus, deviceHost, devicePort, deviceOptions, deviceSerialNumber)
                elif deviceType == "wind_dir":
                    subtype = configParser.get(section,'subtype')
                    if "ads" == subtype:
                        device = WindDirectionSensor(deviceSensorid,  deviceName, deviceCalibrationMultiplier, deviceCalibrationAddition, deviceBus, deviceHost, devicePort, deviceOptions, deviceSerialNumber)

                        device.directionMinVoltage.append(configParser.getfloat(section,'nminvolt'))
                        device.directionMinVoltage.append(configParser.getfloat(section,'nneminvolt'))
                        device.directionMinVoltage.append(configParser.getfloat(section,'neminvolt'))
                        device.directionMinVoltage.append(configParser.getfloat(section,'eneminvolt'))
                        device.directionMinVoltage.append(configParser.getfloat(section,'eminvolt'))
                        device.directionMinVoltage.append(configParser.getfloat(section,'eseminvolt'))
                        device.directionMinVoltage.append(configParser.getfloat(section,'seminvolt'))
                        device.directionMinVoltage.append(configParser.getfloat(section,'sseminvolt'))
                        device.directionMinVoltage.append(configParser.getfloat(section,'sminvolt'))
                        device.directionMinVoltage.append(configParser.getfloat(section,'sswminvolt'))
                        device.directionMinVoltage.append(configParser.getfloat(section,'swminvolt'))
                        device.directionMinVoltage.append(configParser.getfloat(section,'wswminvolt'))
                        device.directionMinVoltage.append(configParser.getfloat(section,'wminvolt'))
                        device.directionMinVoltage.append(configParser.getfloat(section,'wnwminvolt'))
                        device.directionMinVoltage.append(configParser.getfloat(section,'nwminvolt'))
                        device.directionMinVoltage.append(configParser.getfloat(section,'nnwminvolt'))
                        
                        device.directionMaxVoltage.append(configParser.getfloat(section,'nmaxvolt'))
                        device.directionMaxVoltage.append(configParser.getfloat(section,'nnemaxvolt'))
                        device.directionMaxVoltage.append(configParser.getfloat(section,'nemaxvolt'))
                        device.directionMaxVoltage.append(configParser.getfloat(section,'enemaxvolt'))
                        device.directionMaxVoltage.append(configParser.getfloat(section,'emaxvolt'))
                        device.directionMaxVoltage.append(configParser.getfloat(section,'esemaxvolt'))
                        device.directionMaxVoltage.append(configParser.getfloat(section,'semaxvolt'))
                        device.directionMaxVoltage.append(configParser.getfloat(section,'ssemaxvolt'))
                        device.directionMaxVoltage.append(configParser.getfloat(section,'smaxvolt'))
                        device.directionMaxVoltage.append(configParser.getfloat(section,'sswmaxvolt'))
                        device.directionMaxVoltage.append(configParser.getfloat(section,'swmaxvolt'))
                        device.directionMaxVoltage.append(configParser.getfloat(section,'wswmaxvolt'))
                        device.directionMaxVoltage.append(configParser.getfloat(section,'wmaxvolt'))
                        device.directionMaxVoltage.append(configParser.getfloat(section,'wnwmaxvolt'))
                        device.directionMaxVoltage.append(configParser.getfloat(section,'nwmaxvolt'))
                        device.directionMaxVoltage.append(configParser.getfloat(section,'nnwmaxvolt'))
                        
                    elif "inspeed" == subtype:
                        device = InspeedWindDirectionSensor(deviceSensorid,  deviceName, deviceCalibrationMultiplier, deviceCalibrationAddition, deviceBus, deviceHost, devicePort, deviceOptions, deviceSerialNumber)
                    endif
                    
                    device.directionText.append(configParser.get(section,'ntext'))
                    device.directionText.append(configParser.get(section,'nnetext'))
                    device.directionText.append(configParser.get(section,'netext'))
                    device.directionText.append(configParser.get(section,'enetext'))
                    device.directionText.append(configParser.get(section,'etext'))
                    device.directionText.append(configParser.get(section,'esetext'))
                    device.directionText.append(configParser.get(section,'setext'))
                    device.directionText.append(configParser.get(section,'ssetext'))
                    device.directionText.append(configParser.get(section,'stext'))
                    device.directionText.append(configParser.get(section,'sswtext'))
                    device.directionText.append(configParser.get(section,'swtext'))
                    device.directionText.append(configParser.get(section,'wswtext'))
                    device.directionText.append(configParser.get(section,'wtext'))
                    device.directionText.append(configParser.get(section,'wnwtext'))
                    device.directionText.append(configParser.get(section,'nwtext'))
                    device.directionText.append(configParser.get(section,'nnwtext'))
                    
                    device.directionOffset.append(configParser.getfloat(section,'noffset'))
                    device.directionOffset.append(configParser.getfloat(section,'nneoffset'))
                    device.directionOffset.append(configParser.getfloat(section,'neoffset'))
                    device.directionOffset.append(configParser.getfloat(section,'eneoffset'))
                    device.directionOffset.append(configParser.getfloat(section,'eoffset'))
                    device.directionOffset.append(configParser.getfloat(section,'eseoffset'))
                    device.directionOffset.append(configParser.getfloat(section,'seoffset'))
                    device.directionOffset.append(configParser.getfloat(section,'sseoffset'))
                    device.directionOffset.append(configParser.getfloat(section,'soffset'))
                    device.directionOffset.append(configParser.getfloat(section,'sswoffset'))
                    device.directionOffset.append(configParser.getfloat(section,'swoffset'))
                    device.directionOffset.append(configParser.getfloat(section,'wswoffset'))
                    device.directionOffset.append(configParser.getfloat(section,'woffset'))
                    device.directionOffset.append(configParser.getfloat(section,'wnwoffset'))
                    device.directionOffset.append(configParser.getfloat(section,'nwoffset'))
                    device.directionOffset.append(configParser.getfloat(section,'nnwoffset'))


                    device.printInfo()
                    
                elif deviceType == "pressure":
                    device = PressureSensor(deviceSensorid,  deviceName, deviceCalibrationMultiplier, deviceCalibrationAddition, deviceBus, deviceHost, devicePort, deviceOptions, deviceSerialNumber)
                elif deviceType == "humidity":
                    device = HumiditySensor(deviceSensorid,  deviceName, deviceCalibrationMultiplier, deviceCalibrationAddition, deviceBus, deviceHost, devicePort, deviceOptions, deviceSerialNumber)
                else:
                    logMessage(TraceLevel.Major, "Uknown Device Type: " + str(deviceType))
                endif

                device.tableName = configParser.get(section,'tablename')

                for d in lowSpeedSensors:
                    if d.sensorId == device.sensorId:
                        logMessage(TraceLevel.Critical,
                                   str(device.name) +
                                   " sensorid " +
                                   str(device.sensorId) +
                                   " collides with " +
                                   str(d.name))
                        sys.exit(-1)
                    endif
                endfor

                for d in highSpeedSensors:
                    if d.sensorId == device.sensorId:
                        logMessage(TraceLevel.Critical,
                                   str(device.name) +
                                   " sensorid " +
                                   str(device.sensorId) +
                                   " collides with " +
                                   str(d.name))
                        sys.exit(-1)
                    endif
                endfor

                if True == device.present():
                    if deviceSpeed == "low":
                        lowSpeedSensors.append(device)
                    elif deviceSpeed == "high":
                        highSpeedSensors.append(device)
                    else:
                        logMessage(TraceLevel.Major, "Uknown Device Speed: " +
                                   str(deviceSpeed) + "." +
                                   " Defaulting to low.")
                        lowSpeedSensors.append(device)
                    endif
                else:
                    logMessage(TraceLevel.Major, str(deviceName) +
                               " @ " + str(deviceSerialNumber) +
                               " not Present. Will not be used.")
                endif
                    

            elif string.find(section,"General") >= 0:
                lowSpeedRate = configParser.getfloat(section,'lowSpeedRate')
                highSpeedRate = configParser.getfloat(section,'highSpeedRate')
                commitRate = configParser.getfloat(section,'commitRate')
                windSpeedUom = configParser.get(section, 'wind_speed_uom')
                baroPressureUom = configParser.get(section, 'barometric_pressure_uom')
                
                logMessage(TraceLevel.Info,"Low Speed Rate: " + str(lowSpeedRate) + "s High Speed Rate: " + str(highSpeedRate) + "s Commit Rate: " + str(commitRate) + "s")
                logMessage(TraceLevel.Info,"Wind Speed UoM: " + str(windSpeedUom) + " Barometric Pressure UoM: " + str(baroPressureUom))
            elif string.find(section,"Database") >= 0:
                dbHost = configParser.get(section, 'host')
                dbName = configParser.get(section, 'database_name')
                dbUser = configParser.get(section, 'user')
                dbPassword = configParser.get(section, 'password')
                dbPrefix = configParser.get(section, 'prefix')
                
                logMessage(TraceLevel.Info,"Db Host: " + str(dbHost) + " Db Name: " + str(dbName) + " Db User: " + str(dbUser) + " Db Password: " + str(dbPassword) + " Db Prefix: " + str(dbPrefix))
            else:
                logMessage(TraceLevel.Minor,"Unknow Config Section: " + str(section))
            endif
        endfor
    endif
endfor

if configFile == "":
    logMessage(TraceLevel.Abort,
               "Usage weatherDaemon.py -t tracelevel -c configFileName")
    sys.exit(2)
endif    
 
signal.signal(signal.SIGINT, signal_handler)

g_sensors = lowSpeedSensors + highSpeedSensors

lowSpeedSensorArray = SensorArray(lowSpeedSensors, "Low speed sensors", lowSpeedRate)
highSpeedSensorArray = SensorArray(highSpeedSensors, "High speed sensors", highSpeedRate)

g_sensorArrays = { lowSpeedSensorArray, highSpeedSensorArray}

lowSpeedSensorArray.start()
highSpeedSensorArray.start()

commitTimer = CommitTimer(g_sensors,
                          "Commit Timer",
                          commitRate,
                          dbUser,
                          dbPassword,
                          dbHost,
                          dbName)
commitTimer.start()

signal.pause()

endmain
