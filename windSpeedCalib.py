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
    exit(-1)
endtry

try:
    prevCount = int(owproxy.read('/uncached/1D.8DBF0D000000/counters.A'))
    prevTime = time.time()

    print "Starting Count: " + str(prevCount) + " Starting Time: " + str(prevTime)
    
except:
    print  "Failed to read device."
    exit(-1)
endtry

while True:
    time.sleep(1)

    try:
        count = int(owproxy.read('/uncached/1D.8DBF0D000000/counters.A'))
        currentTime = time.time()

        mph = (count - prevCount) * 1.25 / (currentTime - prevTime)
        print "Count: " + str(count) + " Prev Count: " + str(prevCount) + " Time: " + str(currentTime) + " Prev Time: " + str(prevTime) + " Time Diff: " + str(currentTime - prevTime) + "s " + str(mph) + "mph"

        prevCount = count
        prevTime = currentTime
        
    except:
        print  "Failed to read device."
    endtry
endwhile
