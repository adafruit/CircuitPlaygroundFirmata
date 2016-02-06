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

# Stream tap data for 2 seconds, then pause for 5 seconds and stream forever.
print('Streaming tap data for 2 seconds...')
board.start_tap(tap_data)
time.sleep(2.0)

print('Pausing for 5 seconds...')
board.stop_tap()
time.sleep(5.0)

try:
    # Wait in a loop to receive tap data from the board in the background.
    print('Printing tap data (Ctrl-C to quit)...')
    board.start_tap(tap_data)
    while True:
        time.sleep(1.0)
finally:
    print('Stopping!')
    board.stop_tap()

# Close Firmata board connection when done.
board.close()
