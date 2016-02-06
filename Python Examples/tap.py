#!/usr/bin/python
import time
import sys

# Import CircuitPlayground class from the circuitplayground.py in the same directory.
from circuitplayground import CircuitPlayground


# Grab the serial port from the command line parameters.
if len(sys.argv) != 2:
    print('ERROR! Must specify the serial port as command line parameter.')
    sys.exit(-1)
port = sys.argv[1]

# Connect to Circuit Playground board on specified port.
board = CircuitPlayground(port)


def tap_data(tap):
    print('Received tap data: 0x{0:0X}'.format(tap))

# Grab an accelerometer reading every 2 seconds.
print('Printing accelerometer data (Ctrl-C to quit)...')
while True:
    board.read_tap(tap_data)
    time.sleep(2.0)

# Close Firmata board connection when done.
board.close()
