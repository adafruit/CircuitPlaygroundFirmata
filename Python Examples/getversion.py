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

# Define a function which will be called when the version is received.
def print_version(maj, min, fix):
    print('Detected major={0} minor={1} fix={2}'.format(maj, min, fix))

# Connect to Circuit Playground board on specified port.
board = CircuitPlayground(port)

print('Reading version:')
board.read_implementation_version(print_version)
time.sleep(1)
# Close Firmata board connection when done.
board.close()
