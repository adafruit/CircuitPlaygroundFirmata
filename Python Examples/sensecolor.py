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

# Define a function which will be called when a color is detect and received.
# The red green blue parameters will be set with values from 0 to 255 (inclusive)
# which repreent the red, green, blue color value (0 is minimum intentiy, 255
# is maximum intensity).
def color(red, green, blue):
    print('Detected red={0} green={1} blue={2}'.format(red, green, blue))

# Connect to Circuit Playground board on specified port.
board = CircuitPlayground(port)

# Loop forever reading the color every second and printing it out.
try:
    print('Reading color every second, press Ctrl-C to quit...')
    while True:
        # Call sense_color and provide the color callback function defined above.
        board.sense_color(color)
        time.sleep(1)
finally:
    # Close Firmata board connection when done.
    board.close()
