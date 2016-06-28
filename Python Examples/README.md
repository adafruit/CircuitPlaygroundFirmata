These examples use the [PyMata library](https://github.com/MrYsLab/PyMata) to
talk to and control a Circuit Playground board.  You must have PyMata installed,
for example:

    pip install pymata

(use sudo on Linux/Mac OSX)

Then connect the Circuit Playground board and find its serial port.  Run each
example with python and pass in as the command line parameter the name of the
serial port.  For example (running on Linux):

    python buttons.py /dev/ttyACM0

The examples demonstrate:
-   accelerometer_streaming: Display the accelerometer X, Y, Z axis acceleration
    values continuously (this uses a faster streaming interface).
-   accelerometer.py: Display the accelerometer X, Y, Z axis acceleration values
    constantly (this uses a simpler but slower interface).
-   buttons.py: Listening to left button, right button, and switch changes.
-   cap_streaming.py: Detect capacitive touch inputs continuously (this uses a
    faster streaming interface).
-   cap_touch.py: Detect capacitive touch inputs (this uses a simpler but slower
    interface).
-   circuitplayground.py: This is not an example, rather a helper class to simplify
    talking to the Circuit Playground board with PyMata.
-   light.py: Detect light sensor values and print them out.
-   pixels.py: Animate lighting the NeoPixels on the board for 10 seconds.
-   sensecolor.py: Continuously detect and print out the color of an object placed
    in front of the light sensor.
-   sound.py: Print out raw microphone samples.
-   tap_streaming.py: Display the tap detection state continuously (this uses a
    faster streaming interface).
-   tap.py: Display the tap detection state (this uses a slower but simpler interface).
-   temperature.py: Read the temperature sensor value and print it out in degrees Celsius.
-   tones.py: Play a scale of tones on the board's speaker.
