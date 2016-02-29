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
import atexit
from binascii import hexlify
import math
import struct

from PyMata.pymata import PyMata


# Constants that define the Circuit Playground Firmata command values.
CP_COMMAND     = 0x40
CP_PIXEL_SET   = 0x10
CP_PIXEL_SHOW  = 0x11
CP_PIXEL_CLEAR = 0x12
CP_TONE        = 0x20
CP_NO_TONE     = 0x21
CP_ACCEL_READ       = 0x30
CP_ACCEL_TAP        = 0x31
CP_ACCEL_ON         = 0x32
CP_ACCEL_OFF        = 0x33
CP_ACCEL_TAP_ON     = 0x34
CP_ACCEL_TAP_OFF    = 0x35
CP_ACCEL_READ_REPLY = 0x36
CP_ACCEL_TAP_REPLY  = 0x37
CP_ACCEL_TAP_STREAM_ON  = 0x38
CP_ACCEL_TAP_STREAM_OFF = 0x39
CP_ACCEL_STREAM_ON   = 0x3A
CP_ACCEL_STREAM_OFF  = 0x3B

# Constants for some of the board peripherals
THERM_PIN          = 0        # Analog input connected to the thermistor.
THERM_SERIES_OHMS  = 10000.0  # Resistor value in series with thermistor.
THERM_NOMINAL_OHMS = 10000.0  # Thermistor resistance at 25 degrees C.
THERM_NOMIMAL_C    = 25.0     # Thermistor temperature at nominal resistance.
THERM_BETA         = 3950.0   # Thermistor beta coefficient.


class CircuitPlayground(PyMata):

    def __init__(self, port_id='/dev/ttyACM0', bluetooth=True, verbose=True):
        # PyMata is an old style class so you can't use super.
        PyMata.__init__(self, port_id, bluetooth, verbose)
        # Setup handler for response data.
        # Note that the data length (1) appears to be unused for these sysex
        # responses.
        self._command_handler.command_dispatch.update({CP_COMMAND: [self._response_handler, 1]})
        # Setup configured callbacks to null.
        self._accel_callback = None
        self._tap_callback = None
        self._temp_callback = None

    def _therm_value_to_temp(self, adc_value):
        """Convert a thermistor ADC value to a temperature in Celsius."""
        # Use Steinhart-Hart thermistor equation to convert thermistor resistance to
        # temperature.  See: https://learn.adafruit.com/thermistor/overview
        # Handle a zero value which has no meaning (and would cause a divide by zero).
        if adc_value == 0:
            return float('NaN')
        # First calculate the resistance of the thermistor based on its ADC value.
        resistance = ((1023.0 * THERM_SERIES_OHMS)/adc_value)
        resistance -= THERM_SERIES_OHMS
        # Now apply Steinhart-Hart equation.
        steinhart = resistance / THERM_NOMINAL_OHMS
        steinhart = math.log(steinhart)
        steinhart /= THERM_BETA
        steinhart += 1.0 / (THERM_NOMIMAL_C + 273.15)
        steinhart = 1.0 / steinhart
        steinhart -= 273.15
        return steinhart

    def _therm_handler(self, data):
        """Callback invoked when the thermistor analog input has a new value.
        """
        # Get the raw ADC value and convert to temperature.
        raw = data[2]
        temp_c = self._therm_value_to_temp(raw)
        # Call any user callback
        if self._temp_callback is not None:
            self._temp_callback(temp_c, raw)

    def _parse_firmata_byte(self, data):
        """Parse a byte value from two 7-bit byte firmata response bytes."""
        if len(data) != 2:
            raise ValueError('Expected 2 bytes of firmata repsonse for a byte value!')
        return (data[0] & 0x7F) | ((data[1] & 0x01) << 7)

    def _parse_firmata_float(self, data):
        """Parse a 4 byte floating point value from a 7-bit byte firmata response
        byte array.  Each pair of firmata 7-bit response bytes represents a single
        byte of float data so there should be 8 firmata response bytes total.
        """
        if len(data) != 8:
            raise ValueError('Expected 8 bytes of firmata response for floating point value!')
        # Convert 2 7-bit bytes in little endian format to 1 8-bit byte for each
        # of the four floating point bytes.
        raw_bytes = bytearray(4)
        for i in range(4):
            raw_bytes[i] = self._parse_firmata_byte(data[i*2:i*2+2])
        # Use struct unpack to convert to floating point value.
        return struct.unpack('<f', raw_bytes)[0]

    def _tap_register_to_clicks(self, register):
        """Convert accelerometer tap register value to booleans that indicate
        if a single and/or double tap have been detected.  Returns a tuple
        of bools with single click boolean and double click boolean.
        """
        single = False
        double = False
        # Check if there is a good tap register value and check the single and
        # double tap bits to set the appropriate bools.
        if register & 0x30 > 0:
            single = True if register & 0x10 > 0 else False
            double = True if register & 0x20 > 0 else False
        return (single, double)

    def _response_handler(self, data):
        """Callback invoked when a circuit playground sysex command is received.
        """
        #print('CP response: 0x{0}'.format(hexlify(bytearray(data))))
        if len(data) < 1:
            return
        # Check what type of response has been received.
        command = data[0] & 0x7F
        if command == CP_ACCEL_READ_REPLY:
            # Parse accelerometer response.
            if len(data) < 26:
                return
            x = self._parse_firmata_float(data[2:10])
            y = self._parse_firmata_float(data[10:18])
            z = self._parse_firmata_float(data[18:26])
            if self._accel_callback is not None:
                self._accel_callback(x, y ,z)
        elif command == CP_ACCEL_TAP_REPLY:
            # Parse accelerometer tap response.
            if len(data) < 4:
                # TODO: Log errors in some way for debugging.
                return
            tap = self._parse_firmata_byte(data[2:4])
            if self._tap_callback is not None:
                self._tap_callback(*self._tap_register_to_clicks(tap))
        else:
            print('Unknown response received!')

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

    def read_accel(self, callback):
        """Request an accelerometer reading.  The result will be returned by
        calling the provided callback function and passing it 3 parameters:
         - X acceleration
         - Y acceleration
         - Z acceleration
        """
        self._accel_callback = callback
        self._command_handler.send_sysex(CP_COMMAND, [CP_ACCEL_READ])

    def read_tap(self, callback):
        """Request a tap state reading.  The result will be returned by
        calling the provided callback function and passing it the tap state byte.
        """
        self._tap_callback = callback
        self._command_handler.send_sysex(CP_COMMAND, [CP_ACCEL_TAP])

    def start_tap(self, callback):
        """Request to start streaming tap data from the board.  Will call the
        provided callback with tap data."""
        self._tap_callback = callback
        self._command_handler.send_sysex(CP_COMMAND, [CP_ACCEL_TAP_STREAM_ON])

    def stop_tap(self):
        """Stop streaming tap data from the board."""
        self._tap_callback = None
        self._command_handler.send_sysex(CP_COMMAND, [CP_ACCEL_TAP_STREAM_OFF])

    def start_accel(self, callback):
        """Request to start streaming accelerometer data from the board.  Will
        call the provided callback with tap data."""
        self._accel_callback = callback
        self._command_handler.send_sysex(CP_COMMAND, [CP_ACCEL_STREAM_ON])

    def stop_accel(self):
        """Stop streaming tap data from the board."""
        self._accel_callback = None
        self._command_handler.send_sysex(CP_COMMAND, [CP_ACCEL_STREAM_OFF])

    def start_temperature(self, callback=None):
        """Enable reading data from the thermistor.  Callback is an optional
        callback function to provide which will be called when a new value
        is received from the thermistor.  The callback should take two arguments,
        the temperature in celsius, and the raw ADC value of the thermistor.

        Instead of providing a callback you can call read_temperature to grab
        the most recent temperature measurement (but you must still call
        start_temperature once to initialize it!).
        """
        self._temp_callback = callback
        self.set_pin_mode(THERM_PIN, self.INPUT, self.ANALOG, self._therm_handler)

    def stop_temperature(self):
        """Stop streaming temperature data from the thermistor."""
        self._temp_callback = None
        self.disable_analog_reporting(THERM_PIN)

    def read_temperature(self):
        """Read the temperature from the thermistor and return its value in
        degrees Celsius.
        """
        raw = self.analog_read(THERM_PIN)
        return self._therm_value_to_temp(raw)

    def read_temperature_raw(self):
        """Read the raw ADC conversion value from the thermistor.  This is a value
        that has no units and is instead a number from 0-1023.  Use the
        read_temperature function if you want a nice temperature value in degrees
        Celsius!
        """
        raw = self.analog_read(THERM_PIN)
        return raw
