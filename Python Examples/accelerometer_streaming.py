#!/usr/bin/python
import time
import sys

from circuitplayground import *


# Grab the serial port from the command line parameters.
if len(sys.argv) != 2:
    print('ERROR! Must specify the serial port as command line parameter.')
    sys.exit(-1)
port = sys.argv[1]

# Connect to Circuit Playground board on specified port.
board = CircuitPlayground(port)

# Change the range of the accelerometer.
# You can use values like: ACCEL_2G, ACCEL_4G, ACCEL_8G or ACCEL_16G
# to change the range from small to large.  ACCEL_2G = +/- 2G
board.set_accel_range(ACCEL_2G)

def accel_data(x, y, z):
    print('Received accelerometer data!')
    print('X = {0}'.format(x))
    print('Y = {0}'.format(y))
    print('Z = {0}'.format(z))

# Stream accelerometer data for 2 seconds, pause for 5 seconds, then stream forever.
print('Printing accelerometer data for 2 seconds...')
board.start_accel(accel_data)
time.sleep(2.0)

print('Pausing for 5 seconds...')
board.stop_accel()
time.sleep(5.0)

# Grab an accelerometer reading every 2 seconds.
try:
    print('Printing acceleromter data, press Ctrl-C to quit...')
    board.start_accel(accel_data)
    while (True):
        time.sleep(1.0)
finally:
    print('Stopping...')
    board.stop_accel()

# Close Firmata board connection when done.
board.close()
