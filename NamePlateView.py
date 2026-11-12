"""
# NamePlateView.py
# View component managing hardware outputs: 16x2 LCD display, NeoPixel light strip, and buzzer.
# Author: Gabriella Hernandez
"""

try:
    import utime as time
except ImportError:
    import time

from Log import *
from Enums import Availability


class MockLCDDisplay:
    """Mock LCD display for verification without hardware."""
    def __init__(self):
        self.lines = [" " * 16, " " * 16]

    def reset(self):
        self.lines = [" " * 16, " " * 16]

    def clear(self, line=-1):
        if line < 0 or line > 1:
            self.lines = [" " * 16, " " * 16]
        else:
            self.lines[line] = " " * 16

    def showText(self, text, row=0, col=0):
        if 0 <= row < 2:
            self.lines[row] = f"{text[:16]:<16}"
        Log.d(f"MockLCDDisplay [Row {row}]: '{text}'")


class MockLightStrip:
    """Mock NeoPixel light strip for verification without hardware."""
    def __init__(self, numleds=8):
        self._numleds = numleds
        self.color = (0, 0, 0)

    def setColor(self, color, numPixels=None):
        self.color = color
        Log.d(f"MockLightStrip: setColor({color})")

    def off(self):
        self.color = (0, 0, 0)


class MockPassiveBuzzer:
    """Mock buzzer for verification without hardware."""
    def __init__(self):
        self.last_tone = 0

    def beep(self, tone=500, duration=150):
        self.last_tone = tone
        Log.d(f"MockPassiveBuzzer: beep({tone}Hz, {duration}ms)")

    def play(self, tone=500):
        self.last_tone = tone

    def stop(self):
        pass


class NamePlateView:
    """
    **NamePlateView** encapsulates all physical output devices of the dynamic nameplate.

    It controls:
    - **LCDDisplay**: Formats and presents text lines on a 2-line x 16-character display.
    - **LightStrip**: Communicates employee availability via colored LED indications.
    - **PassiveBuzzer**: Produces audio chirps and feedback when navigating people.

    Parameters:
    -----------
    display : LCDDisplay, optional
        Pre-configured LCDDisplay instance or None for default GP0/GP1 I2C.
    lightstrip : LightStrip, optional
        Pre-configured LightStrip instance or None for default GP2 with 8 LEDs.
    buzzer : PassiveBuzzer, optional
        Pre-configured PassiveBuzzer instance or None for default GP16.

    Examples:
    ---------
    1. Creating the default view and updating display:
       ```python
       view = NamePlateView()
       view.showPage(["Dr. Smith", "Professor"])
       view.showAvailability(Availability.AVAILABLE)
       view.playSwitchSound()
       ```
    """

    # Color definitions (R, G, B)
    COLOR_AVAILABLE = (0, 255, 0)     # Green
    COLOR_AWAY = (255, 120, 0)        # Amber / Yellow
    COLOR_BUSY = (255, 0, 0)          # Red
    COLOR_OFF = (0, 0, 0)

    def __init__(self, display=None, lightstrip=None, buzzer=None):
        Log.i("NamePlateView: Initializing hardware components...")

        # Initialize LCD Display (Default I2C SDA=GP0, SCL=GP1)
        if display is not None:
            self._display = display
        else:
            try:
                from Displays import LCDDisplay
                self._display = LCDDisplay(sda=0, scl=1)
                Log.i("NamePlateView: LCDDisplay connected on SDA=GP0, SCL=GP1")
            except Exception as e:
                Log.w(f"NamePlateView: Could not initialize hardware LCD ({e}). Using mock.")
                self._display = MockLCDDisplay()

        # Initialize LightStrip (Default GP2, 8 LEDs)
        if lightstrip is not None:
            self._lightstrip = lightstrip
        else:
            try:
                from LightStrip import LightStrip
                self._lightstrip = LightStrip(pin=2, name="StatusStrip", numleds=8, brightness=0.5)
                Log.i("NamePlateView: LightStrip connected on GP2 (8 LEDs)")
            except Exception as e:
                Log.w(f"NamePlateView: Could not initialize hardware LightStrip ({e}). Using mock.")
                self._lightstrip = MockLightStrip(numleds=8)

        # Initialize PassiveBuzzer (Default GP16)
        if buzzer is not None:
            self._buzzer = buzzer
        else:
            try:
                from Buzzer import PassiveBuzzer
                self._buzzer = PassiveBuzzer(pin=16, name="Buzzer")
                Log.i("NamePlateView: PassiveBuzzer connected on GP16")
            except Exception as e:
                Log.w(f"NamePlateView: Could not initialize hardware PassiveBuzzer ({e}). Using mock.")
                self._buzzer = MockPassiveBuzzer()

        Log.i("NamePlateView initialized successfully.")

    def showPage(self, lines: list) -> None:
        """
        Format and write two lines of text to the 2x16 LCD screen.
        Lines are padded or truncated to exactly 16 characters to prevent
        leftover characters from previous pages.

        Parameters:
        -----------
        lines : list
            A sequence containing up to 2 string lines `[line0, line1]`.
        """
        line0 = lines[0] if len(lines) > 0 else ""
        line1 = lines[1] if len(lines) > 1 else ""

        # Pad to 16 characters or truncate to 16
        formatted_line0 = f"{line0[:16]:<16}"
        formatted_line1 = f"{line1[:16]:<16}"

        Log.d(f"NamePlateView.showPage: Line 0: '{formatted_line0}', Line 1: '{formatted_line1}'")
        self._display.showText(formatted_line0, row=0, col=0)
        self._display.showText(formatted_line1, row=1, col=0)

    def showAvailability(self, status: str) -> None:
        """
        Update the LightStrip to indicate availability.

        Parameters:
        -----------
        status : str
            Availability status ('Available', 'Away', or 'Busy').
        """
        if status == Availability.AVAILABLE:
            color = self.COLOR_AVAILABLE
        elif status == Availability.AWAY:
            color = self.COLOR_AWAY
        elif status == Availability.BUSY:
            color = self.COLOR_BUSY
        else:
            color = self.COLOR_OFF

        Log.i(f"NamePlateView.showAvailability: {status} -> color {color}")
        self._lightstrip.setColor(color)

    def playSwitchSound(self) -> None:
        """
        Produce a short notification chirp when switching active employees.
        """
        Log.i("NamePlateView.playSwitchSound: Playing navigation tone")
        try:
            self._buzzer.beep(tone=1000, duration=80)
        except Exception as e:
            Log.w(f"NamePlateView: Could not play switch sound ({e})")


if __name__ == "__main__":
    Log.i("Testing NamePlateView.py...")

    mock_disp = MockLCDDisplay()
    mock_strip = MockLightStrip(numleds=8)
    mock_buz = MockPassiveBuzzer()

    view = NamePlateView(display=mock_disp, lightstrip=mock_strip, buzzer=mock_buz)

    # 1. Test showPage
    view.showPage(["Dr. Jane Doe", "Chair of CS"])
    assert mock_disp.lines[0] == "Dr. Jane Doe    ", f"Line 0 mismatch: '{mock_disp.lines[0]}'"
    assert mock_disp.lines[1] == "Chair of CS     ", f"Line 1 mismatch: '{mock_disp.lines[1]}'"

    # 2. Test showAvailability
    view.showAvailability(Availability.AVAILABLE)
    assert mock_strip.color == NamePlateView.COLOR_AVAILABLE

    view.showAvailability(Availability.AWAY)
    assert mock_strip.color == NamePlateView.COLOR_AWAY

    view.showAvailability(Availability.BUSY)
    assert mock_strip.color == NamePlateView.COLOR_BUSY

    # 3. Test playSwitchSound
    view.playSwitchSound()
    assert mock_buz.last_tone == 1000

    Log.i("Testing complete - all checks passed")
