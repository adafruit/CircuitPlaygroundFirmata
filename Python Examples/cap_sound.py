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

playing = False
board.no_tone()

# Callback that will be called when a cap touch input result is available.
# The input_pin parameter is the pin number of the input, the touched parameter
# is a boolean that's true if the cap touch input is above a touch threshold
# (as defined by circuitplayground.CAP_THRSHOLD), and raw_value is the raw
# cap touch library value for the input (the bigger the value the more
# capacitance/bigger the thing touching an input).
def cap_touch_data(input_pin, touched, raw_value):
    #print('Cap touch value for pin {0}: {1}'.format(input_pin, raw_value))
    global playing
    if touched:
        print('Cap touch pin {0} is pressed!'.format(input_pin))
        if not playing:
            board.tone(440)
            playing = True
    else:
        if playing:
            board.no_tone()
            playing = False
try:
    # Wait in a loop to receive cap touch data from the board in the background.
    print('Touch pin 10 to play sound (Ctrl-C to quit)...')
    board.start_cap_touch(10, cap_touch_data)
    while True:
        time.sleep(1.0)
finally:
    print('Stopping!')
    board.no_tone()
    board.stop_cap_touch(10)

# Close Firmata board connection when done.
board.close()
