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
-   buttons.py: Listening to left button, right button, and switch changes.
-   circuitplayground.py: This is not an example, rather a helper class to simplify
    talking to the Circuit Playground board with PyMata.
-   pixels.py: Animate lighting the NeoPixels on the board for 10 seconds.
-   templight.py: Read the temperature & light sensors and print their values.
-   tones.py: Play a scale of tones on the board's speaker.
