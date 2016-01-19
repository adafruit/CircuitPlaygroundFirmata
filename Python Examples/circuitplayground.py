# Circuit Playground PyMata helper class.
#
# This is not an example, rather it's a class to add Circuit Playground-specific
# commands to PyMata.  Make sure this file is in the same directory as the
# examples!
#
# Author: Tony DiCola
#
# The MIT License (MIT)
#
# Copyright 2016 Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:  The above copyright
# notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from PyMata.pymata import PyMata


# Constants that define the Circuit Playground Firmata command values.
CP_COMMAND     = 0x40
CP_PIXEL_SET   = 0x10
CP_PIXEL_SHOW  = 0x11
CP_PIXEL_CLEAR = 0x12
CP_TONE        = 0x20
CP_NO_TONE     = 0x21


class CircuitPlayground(PyMata):

    def __init__(self, port_id='/dev/ttyACM0', bluetooth=True, verbose=True):
        # PyMata is an old style class so you can't use super.
        PyMata.__init__(self, port_id, bluetooth, verbose)

    def set_pixel(self, pixel, red, green, blue):
        """Set the specified pixel (0-9) of the Circuit Playground board to the
        provided red, green, blue value.  Each red, green, blue value should be
        a byte (0-255).  Note you must call show_pixels() after set_pixel() to
        see the actual pixel colors change!
        """
        assert 0 <= pixel <= 9, 'pixel must be a value between 0-9!'
        # Pack the pixel and RGB values into a string of 7-bit bytes for the command.
        red &= 0xFF
        green &= 0xFF
        blue &= 0xFF
        pixel &= 0x7F
        b1 = red >> 1
        b2 = ((red & 0x01) << 6) | (green >> 2)
        b3 = ((green & 0x03) << 5) | (blue >> 3)
        b4 = (blue & 0x07) << 4
        self._command_handler.send_sysex(CP_COMMAND, [CP_PIXEL_SET, pixel, b1, b2, b3, b4])

    def clear_pixels(self):
        """Clear all the pixels on the Circuit Playground board.  Make sure to
        call show_pixels to push the change out to the pixels!
        """
        self._command_handler.send_sysex(CP_COMMAND, [CP_PIXEL_CLEAR])

    def show_pixels(self):
        """Send the previously set pixel color data to the 10 pixels on the
        Circuit Playground board.
        """
        self._command_handler.send_sysex(CP_COMMAND, [CP_PIXEL_SHOW])

    def tone(self, frequency_hz, duration_ms=0):
        """Play a tone with the specified frequency (in hz) for the specified
        duration (in milliseconds) using the Circuit Playground board speaker.
        Both frequency and duration can be at most 16,384.  Duration is optional
        and if not specified the tone will continue to play forever (or until
        no_tone is called).
        """
        # Pack 14-bits into 2 7-bit bytes.
        frequency_hz &= 0x3FFF
        f1 = frequency_hz & 0x7F
        f2 = frequency_hz >> 7
        # Again pack 14-bits into 2 7-bit bytes.
        duration_ms &= 0x3FFF
        d1 = duration_ms & 0x7F
        d2 = duration_ms >> 7
        self._command_handler.send_sysex(CP_COMMAND, [CP_TONE, f1, f2, d1, d2])

    def no_tone(self):
        """Stop all tone playback on the Circuit Playground board speaker."""
        self._command_handler.send_sysex(CP_COMMAND, [CP_NO_TONE])
