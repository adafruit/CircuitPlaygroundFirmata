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

# Define functions that will be called when data is received from the analog inputs.
def temp_data(data):
    # Print out the raw temp sensor ADC value (data[2] holds the value).
    print('Temp sensor: {0}'.format(data[2]))

def light_data(data):
    # Print out the raw light sensor ADC value (data[2] holds the value).
    print('Light sensor: {0}'.format(data[2]))

# Setup Firmata to listen to the temp sensor and light sensor analog inputs:
#  - Temp sensor = Analog input 0
#  - Light sensor = Analog input 5
#  - Not shown but the microphone is on analog input 4.
# The callback functions will be called whenever new data is available.
board.set_pin_mode(0, board.INPUT, board.ANALOG, temp_data)
board.set_pin_mode(5, board.INPUT, board.ANALOG, light_data)

# Loop forever waiting for buttons to be pressed or change state.
# When the button changes one of the callback functions above will be called.
print('Print temp and light sensor values (Ctrl-C to quit)...')
while (True):
    time.sleep(1)  # Do nothing and just sleep.  When data is available the callback
                   # functions above will be called.
