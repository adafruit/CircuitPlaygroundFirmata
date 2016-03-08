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

# Callback that will be called when a cap touch input result is available.
# The input_pin parameter is the pin number of the input, the touched parameter
# is a boolean that's true if the cap touch input is above a touch threshold
# (as defined by circuitplayground.CAP_THRSHOLD), and raw_value is the raw
# cap touch library value for the input (the bigger the value the more
# capacitance/bigger the thing touching an input).
def cap_touch_data(input_pin, touched, raw_value):
    print('Cap touch value for pin {0}: {1}'.format(input_pin, raw_value))
    if touched:
        print('Cap touch pin {0} is pressed!'.format(input_pin))

# Grab cap touch input 10's state every 2 seconds.
# You can read any of these inputs: 0, 1, 2, 3, 6, 9, 10, 12
print('Printing cap touch input 10 state (Ctrl-C to quit)...')
while True:
    board.read_cap_touch(10, cap_touch_data)
    time.sleep(2.0)

# Close Firmata board connection when done.
board.close()
