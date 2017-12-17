#! /usr/bin/env python
  
import sys
from pyownet import protocol
import pyownet
from mydefs import *
import time

try:
    owproxy = protocol.OwnetProxy(host="localhost", port=4304, flags=pyownet.protocol.FLG_TEMP_F)
except:
    print "Failed to connect to owserver."
endtry

#print owproxy.present('/10.2B024D010800/temperature')
##print "Outside Temp present", owproxy.present('/uncached/26.B2CBA8000000/temperature')
##print "Outside Humidity present", owproxy.present('/uncached/26.B2CBA8000000/humidity')

try:
##print owproxy.ping()
##print owproxy.dir()
    prevCount = owproxy.read('/uncached/1D.8DBF0D000000/counters.A')
    prevTime = time.time()

    print "Starting Count: " + str(prevCount) + " Starting Time" + str(prevTime)

    while True:
##        print "Inside temp: ", owproxy.read('/uncached/10.2B024D010800/temperature')
##        print "Outside temp: ", owproxy.read('/uncached/26.B2CBA8000000/temperature')
##        print "Outside humidity: ", owproxy.read('/uncached/26.B2CBA8000000/humidity')
        count = owproxy.read('/uncached/1D.8DBF0D000000/counters.A')

        time.sleep(1)

        currentTime = time.time()
        count = owproxy.read('/uncached/1D.8DBF0D000000/counters.A')

        mph = (count - prevCount) * 1.25 / (currentTime - prevTime)
        print "Count: " + str(count) + " Prev Count: " + str(prevCount) + " Time: " + str(currentTime) + " Prev Time: " + str(prevTime) + str(mph) + "mph"

        prevCount = count
        prevTime = currentTime

    endwhile
except:
    print "Failed to read devices."
endtry
