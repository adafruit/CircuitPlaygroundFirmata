#!/usr/bin/python
import atexit
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

# Initialize reading the thermistor by calling start_temperature once.
board.start_temperature()

# Optionally you can pass a callback function that will be called when a new
# temperature measurement is available.  This function should take two
# parameters, the temp in celsius and the raw ADC value.  See the commented
# code below:
# def new_temp(temp_c, raw):
#     print('Temperature: {0:.2f} Celsius'.format(temp_c))
#     print('Raw thermistor ADC value: {0}'.format(raw))
# board.start_temperature(new_temp)

# Loop forever printing the temperature every second.
print('Printing temperature (Ctrl-C to quit)...')
while (True):
    # Read the temperature in Celsius.
    temp_c = board.read_temperature()
    # Print out the temperature with two decimal places.
    print('Temperature: {0:.2f} Celsius'.format(temp_c))
    # You can also read the raw thermistor ADC value.  This will be a value from
    # 0 to 1023 which is proportional to the resistance of the thermistor.
    raw = board.read_temperature_raw()
    print('Raw thermistor ADC value: {0}'.format(raw))
    time.sleep(1)  # Pause for a second and repeat.
