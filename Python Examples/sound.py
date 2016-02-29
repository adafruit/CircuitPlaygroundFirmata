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

# Define function that will be called when data is received from the microphone.
def sound_data(data):
    # Print out the raw microphone ADC value (data[2] holds the value).
    print('Microphone: {0}'.format(data[2]))

# Setup Firmata to listen to the microphone analog input (A4):
# The callback functions will be called whenever new data is available.
board.set_pin_mode(4, board.INPUT, board.ANALOG, sound_data)

# Loop forever printing sound values as they change.
print('Printing microphone values (Ctrl-C to quit)...')
while (True):
    time.sleep(1)  # Do nothing and just sleep.  When data is available the callback
                   # functions above will be called.
