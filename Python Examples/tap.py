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

# Callback that will be called when a tap is detected.  The single parameter is
# a boolean that indicates if it was a single tap, and the double parameter is
# a boolean that indicates if it was a double tap.  You might see both a single
# and double tap!
def tap_data(single, double):
    if single:
        print('Single click!')
    if double:
        print('Double click!')

# Grab a tap detection reading every 2 seconds.
print('Printing tap detection every 2 seconds (Ctrl-C to quit)...')
while True:
    board.read_tap(tap_data)
    time.sleep(2.0)

# Close Firmata board connection when done.
board.close()
