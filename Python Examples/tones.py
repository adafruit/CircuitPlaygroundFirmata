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

# Define a C major scale of frequencies (C4, D4, E4, F4, G4, A4, B4) up & down.
# Tone frequency values from:
#   https://www.arduino.cc/en/Tutorial/ToneMelody?from=Tutorial.Tone
scale = [262, 294, 330, 349, 392, 440, 494, 440, 392, 349, 330, 294, 262]

# Set the duration of each note (in milliseconds)
duration = 500

# Loop through the scale and play each note.
print('Playing scale...')
for note in scale:
    # Play the note using the tone function.
    board.tone(note, duration)
    # Wait for the tone to finish playing, and add a small delay between notes
    # (100 ms).
    time.sleep((duration+100.0)/1000.0)  # time.sleep expects seconds, so divide duration by 1000.

# Demonstrate continuous tone playback and no_tone to stop playback.
print('Playing note, then stopping after 1 second.')
board.tone(scale[0])  # This will start playing the first not forever.
time.sleep(1.0)       # Now wait 1 second.
board.no_tone()       # Stop tone playback.

# Close Firmata board connection when done.
board.close()
