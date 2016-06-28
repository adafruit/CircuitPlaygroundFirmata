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
import logging
import math
import struct

from PyMata.pymata import PyMata


# Constants that define the Circuit Playground Firmata command values.
CP_COMMAND              = 0x40  # Byte that identifies all Circuit Playground commands.
CP_PIXEL_SET            = 0x10  # Set NeoPixel, expects the following bytes as data:
                                #  - Pixel ID (0-9)
                                #  - Pixel RGB color data as 4 7-bit bytes.  The upper
                                #    24 bits will be mapped to the R, G, B bytes.
CP_PIXEL_SHOW           = 0x11  # Update NeoPixels with their current color values.
CP_PIXEL_CLEAR          = 0x12  # Clear all NeoPixels to black/off.  Must call show pixels after this to see the change!
CP_PIXEL_BRIGHTNESS     = 0x13  # Set the brightness of the NeoPixels, just like calling the
                                # NeoPixel library setBrightness function.  Takes one parameter
                                # which is a single byte with a value 0-100.
CP_TONE                 = 0x20  # Play a tone on the speaker, expects the following bytes as data:
                                #  - Frequency (hz) as 2 7-bit bytes (up to 2^14 hz, or about 16khz)
                                #  - Duration (ms) as 2 7-bit bytes.
CP_NO_TONE              = 0x21  # Stop playing anything on the speaker.
CP_ACCEL_READ           = 0x30  # Return the current x, y, z accelerometer values.
CP_ACCEL_TAP            = 0x31  # Return the current accelerometer tap state.
CP_ACCEL_READ_REPLY     = 0x36  # Result of an acceleromete read.  Includes 3 floating point values (4 bytes each) with x, y, z
                                # acceleration in meters/second^2.
CP_ACCEL_TAP_REPLY      = 0x37  # Result of the tap sensor read.  Includes a byte with the tap register value.
CP_ACCEL_TAP_STREAM_ON  = 0x38  # Turn on continuous streaming of tap data.
CP_ACCEL_TAP_STREAM_OFF = 0x39  # Turn off streaming of tap data.
CP_ACCEL_STREAM_ON      = 0x3A  # Turn on continuous streaming of accelerometer data.
CP_ACCEL_STREAM_OFF     = 0x3B  # Turn off streaming of accelerometer data.
CP_ACCEL_RANGE          = 0x3C  # Set the range of the accelerometer, takes one byte as a parameter.
                                # Use a value 0=+/-2G, 1=+/-4G, 2=+/-8G, 3=+/-16G
CP_ACCEL_TAP_CONFIG     = 0x3D  # Set the sensitivity of the tap detection, takes 4 bytes of 7-bit firmata
                                # data as parameters which expand to 2 unsigned 8-bit bytes value to set:
                                #   - Type of click: 0 = no click detection, 1 = single click, 2 = single & double click (default)
                                #   - Click threshold: 0-255, the higher the value the less sensitive.  Depends on the accelerometer
                                #     range, good values are: +/-16G = 5-10, +/-8G = 10-20, +/-4G = 20-40, +/-2G = 40-80
                                #     80 is the default value (goes well with default of +/-2G)
CP_CAP_READ             = 0x40  # Read a single capacitive input.  Expects a byte as a parameter with the
                                # cap touch input to read (0, 1, 2, 3, 6, 9, 10, 12).  Will respond with a
                                # CP_CAP_REPLY message.
CP_CAP_ON               = 0x41  # Turn on continuous cap touch reads for the specified input (sent as a byte parameter).
CP_CAP_OFF              = 0x42  # Turn off continuous cap touch reads for the specified input (sent as a byte parameter).
CP_CAP_REPLY            = 0x43  # Capacitive input read response.  Includes a byte with the pin # of the cap input, then
                                # four bytes of data which represent an int32_t value read from the cap input.
CP_SENSECOLOR           = 0x50  # Perform a color sense using the NeoPixel and light sensor.
CP_SENSECOLOR_REPLY     = 0x51  # Result of a color sense, will return the red, green, blue color
                                # values that were read from the light sensor.  This will return
                                # 6 bytes of data:
                                #  - red color (unsigned 8 bit value, split across 2 7-bit bytes)
                                #  - green color (unsigned 8 bit value, split across 2 7-bit bytes)
                                #  - blue color (unsigned 8 bit value, split across 2 7-bit bytes)



# Accelerometer constants to be passed to set_accel_range.
ACCEL_2G  = 0
ACCEL_4G  = 1
ACCEL_8G  = 2
ACCEL_16G = 3

# Constants for some of the board peripherals
THERM_PIN          = 0        # Analog input connected to the thermistor.
THERM_SERIES_OHMS  = 10000.0  # Resistor value in series with thermistor.
THERM_NOMINAL_OHMS = 10000.0  # Thermistor resistance at 25 degrees C.
THERM_NOMIMAL_C    = 25.0     # Thermistor temperature at nominal resistance.
THERM_BETA         = 3950.0   # Thermistor beta coefficient.
CAP_THRESHOLD      = 300      # Threshold for considering a cap touch input pressed.
                              # If the cap touch value is above this value it is
                              # considered touched.

logger = logging.getLogger(__name__)


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
        self._cap_callback = None
        self._sensecolor_callback = None

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

    def _parse_firmata_long(self, data):
        """Parse a 4 byte signed long integer value from a 7-bit byte firmata response
        byte array.  Each pair of firmata 7-bit response bytes represents a single
        byte of long data so there should be 8 firmata response bytes total.
        """
        if len(data) != 8:
            raise ValueError('Expected 8 bytes of firmata response for long value!')
        # Convert 2 7-bit bytes in little endian format to 1 8-bit byte for each
        # of the four floating point bytes.
        raw_bytes = bytearray(4)
        for i in range(4):
            raw_bytes[i] = self._parse_firmata_byte(data[i*2:i*2+2])
        # Use struct unpack to convert to floating point value.
        return struct.unpack('<l', raw_bytes)[0]

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
        logger.debug('CP response: 0x{0}'.format(hexlify(bytearray(data))))
        if len(data) < 1:
            logger.warning('Received response with no data!')
            return
        # Check what type of response has been received.
        command = data[0] & 0x7F
        if command == CP_ACCEL_READ_REPLY:
            # Parse accelerometer response.
            if len(data) < 26:
                logger.warning('Received accelerometer response with not enough data!')
                return
            x = self._parse_firmata_float(data[2:10])
            y = self._parse_firmata_float(data[10:18])
            z = self._parse_firmata_float(data[18:26])
            if self._accel_callback is not None:
                self._accel_callback(x, y ,z)
        elif command == CP_ACCEL_TAP_REPLY:
            # Parse accelerometer tap response.
            if len(data) < 4:
                logger.warning('Received tap response with not enough data!')
                return
            tap = self._parse_firmata_byte(data[2:4])
            if self._tap_callback is not None:
                self._tap_callback(*self._tap_register_to_clicks(tap))
        elif command == CP_CAP_REPLY:
            # Parse capacitive sensor response.
            if len(data) < 12:
                logger.warning('Received cap touch response with not enough data!')
                return
            input_pin = self._parse_firmata_byte(data[2:4])
            value = self._parse_firmata_long(data[4:12])
            if self._cap_callback is not None:
                self._cap_callback(input_pin, value > CAP_THRESHOLD, value)
        elif command == CP_SENSECOLOR_REPLY:
            # Parse sense color response.
            if len(data) < 8:
                logger.warning('Received color sense response with not enough data!')
                return
            # Parse out the red, green, blue color bytes.
            red = self._parse_firmata_byte(data[2:4])
            green = self._parse_firmata_byte(data[4:6])
            blue = self._parse_firmata_byte(data[6:8])
            if self._sensecolor_callback is not None:
                self._sensecolor_callback(red, green, blue)
        else:
            logger.warning('Received unexpected response!')

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

    def set_pixel_brightness(self, brightness):
        """Set the brightness of all the NeoPixels.  Brightness will be a value
        from 0-100 where 0 means completely dark/no brightness and 100 is full
        brightness.  Note that animating the brightness won't work the way you
        might expect!  If you go down to 0 brightness you will 'lose' information
        and not be able to go back up to higher brightness levels.  Instead
        this is meant to be called once at the start to limit the brightness
        of pixels that are later set.
        """
        assert brightness >= 0 and brightness <= 100, 'Brightness must be a value of 0-100!'
        self._command_handler.send_sysex(CP_COMMAND, [CP_PIXEL_BRIGHTNESS, brightness & 0x7F])

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

    def read_cap_touch(self, input_pin, callback=None):
        """Read the specified input pin as a capacitive touch sensor.  Will
        invoke the provided callback when the result is available (note this
        callback is global and will override any previously specified callback).
        The callback should take three parameters, one that is the cap touch input
        pin, the next that is a boolean if the cap input was 'pressed' (i.e. above
        a large enough threshold), and a signed integer value that's the raw cap
        touch library result (bigger values mean more capacitance, i.e. something
        is touching the input).
        """
        assert input_pin in [0, 1, 2, 3, 6, 9, 10, 12], 'Input pin must be a capacitive input (0,1,2,3,6,9,10,12)!'
        self._cap_callback = callback
        # Construct a cap read command and send it.
        self._command_handler.send_sysex(CP_COMMAND, [CP_CAP_READ, input_pin & 0x7F])

    def start_cap_touch(self, input_pin, callback=None):
        """Start continuous capacitive touch queries for the specified input
        pin.  Will invoke the provided callback each time a new cap touch result
        is available (note this callback is global and will override any other
        instances previously specified).  See read_cap_touch for a description of
        the callback parameters.
        """
        assert input_pin in [0, 1, 2, 3, 6, 9, 10, 12], 'Input pin must be a capacitive input (0,1,2,3,6,9,10,12)!'
        self._cap_callback = callback
        # Construct a continuous cap read start command and send it.
        self._command_handler.send_sysex(CP_COMMAND, [CP_CAP_ON, input_pin & 0x7F])

    def stop_cap_touch(self, input_pin):
        """Stop continuous capacitive touch queries for the specified input
        pin.
        """
        assert input_pin in [0, 1, 2, 3, 6, 9, 10, 12], 'Input pin must be a capacitive input (0,1,2,3,6,9,10,12)!'
        self._cap_callback = None
        # Construct a continuous cap read stop command and send it.
        self._command_handler.send_sysex(CP_COMMAND, [CP_CAP_OFF, input_pin & 0x7F])

    def set_accel_range(self, accel_range=0):
        """Set the range of the accelerometer.  Accel_range should be a value of:
          - 0 = +/-2G (default)
          - 1 = +/-4G
          - 2 = +/-8G
          - 3 = +/-16G
        """
        assert accel_range in [0, 1, 2, 3], 'Accel range must be one of 0, 1, 2, 3!'
        self._command_handler.send_sysex(CP_COMMAND, [CP_ACCEL_RANGE, accel_range & 0x7F])

    def set_tap_config(self, tap_type=0, threshold=80):
        """Set the tap detection configuration.  Tap_type should be a value of:
          - 0 = no tap detection
          - 1 = single tap detection
          - 2 = single & double tap detection (default)
        Threshold controls the sensitivity of the detection and is a value FROM
        0 to 255, the higher the value the less sensitive the detection.  This
        value depends on the accelerometer range and good values are:
          - Accel range +/-16G = 5-10
          - Accel range +/-8G  = 10-20
          - Accel range +/-4G  = 20-40
          - Accel range +/-2G  = 40-80 (80 is the default)
        """
        assert tap_type in [0, 1, 2], 'Type must be one of 0, 1, 2!'
        assert threshold >= 0 and threshold <= 255, 'Threshold must be a value 0-255!'
        # Assemble data to send by turning each unsigned 8 bit values into two
        # 7-bit values that firmata can understand.  The most significant bits
        # are first and the least significant (7th) bit follows.
        tap_type_low  = tap_type & 0x7F
        tap_type_high = (tap_type & 0xFF) >> 7
        threshold_low  = threshold & 0x7F
        threshold_high = (threshold & 0xFF) >> 7
        # Send command.
        self._command_handler.send_sysex(CP_COMMAND, [CP_ACCEL_TAP_CONFIG,
            tap_type_low, tap_type_high, threshold_low, threshold_high])

    def sense_color(self, callback=None):
        """Perform a color sense using NeoPixel #1 and the light sensor. Callback
        should be a function that will be called when a color response is received
        from the board.  This function should take three parameters, the red,
        green, blue byte values that define the color (values that range from
        0 to 255, i.e. minimum to maximum intensity).
        """
        # Save the passed in callback and then invoke the sense color command.
        self._sensecolor_callback = callback
        self._command_handler.send_sysex(CP_COMMAND, [CP_SENSECOLOR])
