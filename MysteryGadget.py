"""
# MysteryGadget.py
# Engine simulation gadget integrating an LCD display, buzzer, NeoPixel light strip,
# and potentiometer to model real-time RPM, speed, audio, and visual feedback.
# Author: Gabriella Hernandez
"""

try:
    import utime as time
except ImportError:
    import time

from Log import *


class MockDisplay:
    """Mock LCD display for testing environments without hardware drivers."""

    def __init__(self):
        self.lines = ["", ""]

    def clear(self, line=-1):
        if line < 0 or line > 1:
            self.lines = ["", ""]
        else:
            self.lines[line] = ""
        Log.d("MockDisplay: Screen cleared")

    def reset(self):
        self.clear()

    def showText(self, text, row=0, col=0):
        if 0 <= row < len(self.lines):
            self.lines[row] = text
        Log.d(f"MockDisplay [Row {row}, Col {col}]: {text}")


class MockBuzzer:
    """Mock buzzer for testing environments without PWM hardware."""

    def __init__(self):
        self.playing = False
        self.tone = 0
        self.volume = 0.5

    def play(self, tone=500):
        self.playing = True
        self.tone = tone
        Log.d(f"MockBuzzer: Playing tone {tone} Hz")

    def stop(self):
        self.playing = False
        Log.d("MockBuzzer: Sound stopped")

    def setVolume(self, volume=0.5):
        self.volume = volume
        Log.d(f"MockBuzzer: Volume set to {volume}")


class MockLightStrip:
    """Mock NeoPixel light strip for testing environments without PIO hardware."""

    def __init__(self, numleds=8):
        self._numleds = numleds
        self.pixels = [(0, 0, 0)] * numleds

    def setPixel(self, pixelno, color, show=True):
        if 0 <= pixelno < self._numleds:
            self.pixels[pixelno] = color
        Log.d(f"MockLightStrip: Pixel {pixelno} set to {color}")

    def setColor(self, color, numPixels=None):
        if numPixels is None:
            numPixels = self._numleds
        for i in range(min(numPixels, self._numleds)):
            self.pixels[i] = color
        Log.d(f"MockLightStrip: Set {numPixels} pixels to {color}")

    def show(self):
        Log.d(f"MockLightStrip: Buffer written -> {self.pixels}")

    def off(self):
        self.pixels = [(0, 0, 0)] * self._numleds
        Log.d("MockLightStrip: All LEDs turned off")

    def on(self):
        self.pixels = [(255, 255, 255)] * self._numleds
        Log.d("MockLightStrip: All LEDs turned on")


class MockPotentiometer:
    """Mock potentiometer sensor for testing environments without ADC hardware."""

    def __init__(self, initial_value=0):
        self._value = initial_value

    def rawValue(self):
        return self._value

    def setValue(self, value):
        self._value = max(0, min(65535, value))
        Log.d(f"MockPotentiometer: Value adjusted to {self._value}")


class MysteryGadget:
    """
    **MysteryGadget** simulates an interactive automotive engine system.

    It integrates four hardware components:
    - **LCD Display**: Displays current engine status, RPM, and speed.
    - **Buzzer**: Produces low-frequency engine rumbling sounds that scale dynamically with RPM.
    - **NeoPixel Light Strip**: Visualizes engine RPM as a tachometer bar graph (Green -> Yellow -> Red).
    - **Potentiometer**: Reads throttle input to adjust RPM and speed in real-time.

    Parameters:
    ----------
    display : LCDDisplay, optional
        An instance of `LCDDisplay` (or compatible display). If `None`, attempts to create a default
        `LCDDisplay` or falls back to a test mock.
    buzzer : PassiveBuzzer, optional
        An instance of `PassiveBuzzer` (or compatible buzzer). If `None`, attempts to create a default
        `PassiveBuzzer` or falls back to a test mock.
    light_strip : LightStrip, optional
        An instance of `LightStrip` (or compatible NeoPixel strip). If `None`, attempts to create a default
        `LightStrip` or falls back to a test mock.
    potentiometer : AnalogSensor, optional
        An instance of `AnalogSensor` (or compatible analog sensor). If `None`, attempts to create a default
        `AnalogSensor` or falls back to a test mock.

    Examples:
    ---------
    1. Basic hardware initialization:
       ```python
       from MysteryGadget import MysteryGadget
       from Displays import LCDDisplay
       from Buzzer import PassiveBuzzer
       from LightStrip import LightStrip
       from Sensors import AnalogSensor

       lcd = LCDDisplay(sda=0, scl=1)
       buz = PassiveBuzzer(pin=16)
       strip = LightStrip(pin=2, numleds=8)
       pot = AnalogSensor(pin=26)

       gadget = MysteryGadget(lcd, buz, strip, pot)
       gadget.start()
       gadget.control(iterations=50)
       gadget.stop()
       ```

    2. Default / simulated initialization:
       ```python
       from MysteryGadget import MysteryGadget

       gadget = MysteryGadget()
       gadget.start()
       gadget.control(iterations=10)
       gadget.stop()
       ```
    """

    IDLE_RPM = 800
    MAX_RPM = 7000
    MAX_SPEED = 140
    IDLE_TONE = 360
    MAX_TONE = 1060

    COLOR_OFF = (0, 0, 0)
    COLOR_GREEN = (0, 255, 0)
    COLOR_YELLOW = (255, 200, 0)
    COLOR_RED = (255, 0, 0)

    def __init__(self, display=None, buzzer=None, light_strip=None, potentiometer=None):
        Log.i("MysteryGadget: Initializing engine gadget...")

        # Initialize LCD display
        if display is not None:
            self.display = display
        else:
            try:
                from Displays import LCDDisplay
                self.display = LCDDisplay(sda=0, scl=1)
                Log.i("MysteryGadget: Initialized default LCDDisplay on I2C (SDA=0, SCL=1)")
            except Exception as e:
                Log.d(f"MysteryGadget: Falling back to MockDisplay ({e})")
                self.display = MockDisplay()

        # Initialize Buzzer
        if buzzer is not None:
            self.buzzer = buzzer
        else:
            try:
                from Buzzer import PassiveBuzzer
                self.buzzer = PassiveBuzzer(pin=16, name="EngineBuzzer")
                Log.i("MysteryGadget: Initialized default PassiveBuzzer on pin 16")
            except Exception as e:
                Log.d(f"MysteryGadget: Falling back to MockBuzzer ({e})")
                self.buzzer = MockBuzzer()

        # Initialize NeoPixel light strip
        if light_strip is not None:
            self.light_strip = light_strip
        else:
            try:
                from LightStrip import LightStrip
                self.light_strip = LightStrip(pin=2, name="Tachometer", numleds=8)
                Log.i("MysteryGadget: Initialized default LightStrip on pin 2 (8 LEDs)")
            except Exception as e:
                Log.d(f"MysteryGadget: Falling back to MockLightStrip ({e})")
                self.light_strip = MockLightStrip()

        # Initialize Potentiometer
        if potentiometer is not None:
            self.potentiometer = potentiometer
        else:
            try:
                from Sensors import AnalogSensor
                self.potentiometer = AnalogSensor(pin=26, name="ThrottlePot")
                Log.i("MysteryGadget: Initialized default AnalogSensor on pin 26")
            except Exception as e:
                Log.d(f"MysteryGadget: Falling back to MockPotentiometer ({e})")
                self.potentiometer = MockPotentiometer()

        self._running = False
        self._rpm = 0
        self._speed = 0
        Log.i("MysteryGadget: Initialization complete.")

    @property
    def is_running(self) -> bool:
        """Returns True if the engine is currently running."""
        return self._running

    @property
    def rpm(self) -> int:
        """Returns the current simulated engine RPM."""
        return self._rpm

    @property
    def speed(self) -> int:
        """Returns the current simulated vehicle speed in mph."""
        return self._speed

    def start(self):
        """
        Simulates starting the engine.

        Plays a low-frequency rumbling sound on the buzzer, illuminates the tachometer
        strip to idle status, and displays simulated idle RPM and initial speed on the LCD.

        Examples:
        ---------
        1. Start the engine:
           ```python
           gadget.start()
           ```
        """
        Log.i("MysteryGadget: Starting engine...")
        self._running = True
        self._rpm = self.IDLE_RPM
        self._speed = 0

        # Play low-frequency engine idle sound on buzzer
        try:
            self.buzzer.play(self.IDLE_TONE)
        except Exception as e:
            Log.e(f"MysteryGadget: Error playing start sound: {e}")

        # Show simulated speed and RPM values on the display
        try:
            self.display.clear()
            self.display.showText(f"RPM: {self._rpm:<5}", row=0, col=0)
            self.display.showText(f"Speed: {self._speed:<3} mph", row=1, col=0)
        except Exception as e:
            Log.e(f"MysteryGadget: Error updating display during start: {e}")

        # Visualize idle RPM on light strip
        self._update_light_strip(self._rpm)
        Log.i(f"MysteryGadget: Engine started at idle ({self._rpm} RPM, {self._speed} mph).")

    def stop(self):
        """
        Stops the engine simulation.

        Stops the sound on the buzzer, clears and turns off the light strip, and shows
        'Engine stopped' on the LCD display.

        Examples:
        ---------
        1. Stop the engine:
           ```python
           gadget.stop()
           ```
        """
        Log.i("MysteryGadget: Stopping engine...")
        self._running = False
        self._rpm = 0
        self._speed = 0

        # Stop buzzer sound
        try:
            self.buzzer.stop()
        except Exception as e:
            Log.e(f"MysteryGadget: Error stopping buzzer: {e}")

        # Turn off light strip
        try:
            self.light_strip.off()
        except Exception as e:
            Log.e(f"MysteryGadget: Error turning off light strip: {e}")

        # Show 'Engine stopped' on the display
        try:
            self.display.clear()
            self.display.showText("Engine stopped", row=0, col=0)
        except Exception as e:
            Log.e(f"MysteryGadget: Error updating display during stop: {e}")

        Log.i("MysteryGadget: Engine successfully stopped.")

    def control(self, iterations=None, interval=0.1, duration=None):
        """
        Monitors the potentiometer and uses its raw value to simulate increasing and decreasing engine RPM.

        Visualizes the RPM on the NeoPixel light strip as a tachometer bar graph, updates the
        buzzer frequency to match engine load, and shows simulated RPM and speed on the display.

        Parameters:
        ----------
        iterations : int, optional
            Number of update cycles to execute. If `None` and `duration` is `None`, runs continuously
            until `stop()` is called or a `KeyboardInterrupt` occurs (default: None).
        interval : float, optional
            Delay in seconds between polling cycles (default: 0.1).
        duration : float, optional
            Duration in seconds to run the control loop (default: None).

        Examples:
        ---------
        1. Run control loop for 10 seconds:
           ```python
           gadget.control(duration=10)
           ```
        2. Run control loop for 20 cycles:
           ```python
           gadget.control(iterations=20, interval=0.05)
           ```
        3. Run continuous control loop:
           ```python
           gadget.control()
           ```
        """
        if not self._running:
            Log.i("MysteryGadget: Engine is off. Starting engine before controlling...")
            self.start()

        Log.i("MysteryGadget: Entering control loop...")
        cycle = 0
        start_time = time.time()
        try:
            while self._running:
                self._update_engine_state()
                cycle += 1
                if iterations is not None and cycle >= iterations:
                    break
                if duration is not None and (time.time() - start_time) >= duration:
                    break
                time.sleep(interval)
        except KeyboardInterrupt:
            Log.i("MysteryGadget: Control loop interrupted by user.")

        Log.i("MysteryGadget: Exited control loop.")

    def _update_engine_state(self):
        """Reads potentiometer and updates engine RPM, speed, audio, and visual feedback."""
        try:
            raw_val = self.potentiometer.rawValue()
        except Exception as e:
            Log.e(f"MysteryGadget: Error reading potentiometer: {e}")
            raw_val = 0

        # Normalize potentiometer ADC input (0 to 65535)
        throttle_pct = max(0.0, min(1.0, raw_val / 65535.0))

        # Calculate simulated RPM and speed
        self._rpm = int(self.IDLE_RPM + throttle_pct * (self.MAX_RPM - self.IDLE_RPM))
        self._speed = int(throttle_pct * self.MAX_SPEED)

        # Scale audio frequency with RPM
        engine_tone = int(self.IDLE_TONE + throttle_pct * (self.MAX_TONE - self.IDLE_TONE))
        try:
            self.buzzer.play(engine_tone)
        except Exception as e:
            Log.e(f"MysteryGadget: Error updating buzzer tone: {e}")

        # Update visual display with RPM and Speed
        try:
            self.display.showText(f"RPM: {self._rpm:<5}", row=0, col=0)
            self.display.showText(f"Speed: {self._speed:<3} mph", row=1, col=0)
        except Exception as e:
            Log.e(f"MysteryGadget: Error updating LCD display: {e}")

        # Visualize RPM on the NeoPixel light strip
        self._update_light_strip(self._rpm)

    def _update_light_strip(self, rpm):
        """Visualizes engine RPM on the NeoPixel light strip using a multi-color tachometer bar."""
        try:
            num_leds = getattr(self.light_strip, '_numleds', 8)
            rpm_ratio = (rpm - self.IDLE_RPM) / max(1, (self.MAX_RPM - self.IDLE_RPM))
            rpm_ratio = max(0.0, min(1.0, rpm_ratio))

            # Light up LEDs proportionally to RPM (at least 1 LED at idle when running)
            num_lit = max(1, int(round(rpm_ratio * num_leds))) if self._running else 0

            for i in range(num_leds):
                if i < num_lit:
                    progress = i / float(num_leds)
                    if progress < 0.5:
                        color = self.COLOR_GREEN
                    elif progress < 0.75:
                        color = self.COLOR_YELLOW
                    else:
                        color = self.COLOR_RED
                    self.light_strip.setPixel(i, color, show=False)
                else:
                    self.light_strip.setPixel(i, self.COLOR_OFF, show=False)

            self.light_strip.show()
        except Exception as e:
            Log.e(f"MysteryGadget: Error updating light strip: {e}")


if __name__ == "__main__":
    Log.i("Starting MysteryGadget self-contained test suite...")

    mock_disp = MockDisplay()
    mock_buz = MockBuzzer()
    mock_strip = MockLightStrip(numleds=8)
    mock_pot = MockPotentiometer(initial_value=0)

    # 1. Instantiate the MysteryGadget class
    gadget = MysteryGadget(
        display=mock_disp,
        buzzer=mock_buz,
        light_strip=mock_strip,
        potentiometer=mock_pot
    )
    assert not gadget.is_running, "Engine should not be running immediately after init"

    # 2. Test start()
    Log.i("Testing start() method...")
    gadget.start()
    assert gadget.is_running, "Engine should be running after start()"
    assert gadget.rpm == MysteryGadget.IDLE_RPM, f"Expected {MysteryGadget.IDLE_RPM} RPM, got {gadget.rpm}"
    assert gadget.speed == 0, f"Expected 0 speed, got {gadget.speed}"
    assert mock_buz.playing, "Buzzer should be playing low-frequency sound"
    assert mock_buz.tone == MysteryGadget.IDLE_TONE, f"Expected tone {MysteryGadget.IDLE_TONE}, got {mock_buz.tone}"
    assert "RPM: 800" in mock_disp.lines[0], f"Display row 0 should show RPM: {mock_disp.lines[0]}"
    assert "Speed: 0" in mock_disp.lines[1], f"Display row 1 should show Speed: {mock_disp.lines[1]}"
    assert mock_strip.pixels[0] == MysteryGadget.COLOR_GREEN, "At least 1 idle LED should be green"

    # 3. Test control() with increasing and decreasing throttle
    Log.i("Testing control() method with low throttle (25%)...")
    mock_pot.setValue(16384)
    gadget.control(iterations=1)
    assert 2200 <= gadget.rpm <= 2500, f"Unexpected RPM for 25% throttle: {gadget.rpm}"
    assert 30 <= gadget.speed <= 40, f"Unexpected speed for 25% throttle: {gadget.speed}"

    Log.i("Testing control() method with high throttle (100% / redline)...")
    mock_pot.setValue(65535)
    gadget.control(iterations=1)
    assert gadget.rpm == MysteryGadget.MAX_RPM, f"Expected MAX_RPM {MysteryGadget.MAX_RPM}, got {gadget.rpm}"
    assert gadget.speed == MysteryGadget.MAX_SPEED, f"Expected MAX_SPEED {MysteryGadget.MAX_SPEED}, got {gadget.speed}"
    assert mock_buz.tone == MysteryGadget.MAX_TONE, f"Expected MAX_TONE {MysteryGadget.MAX_TONE}, got {mock_buz.tone}"
    assert mock_strip.pixels[-1] == MysteryGadget.COLOR_RED, "Top LED should be red at redline RPM"

    Log.i("Testing control() method with decreased throttle back to 0%...")
    mock_pot.setValue(0)
    gadget.control(iterations=1)
    assert gadget.rpm == MysteryGadget.IDLE_RPM, f"Expected IDLE_RPM {MysteryGadget.IDLE_RPM}, got {gadget.rpm}"
    assert gadget.speed == 0, f"Expected 0 speed, got {gadget.speed}"

    # 4. Test stop()
    Log.i("Testing stop() method...")
    gadget.stop()
    assert not gadget.is_running, "Engine should be stopped after stop()"
    assert not mock_buz.playing, "Buzzer sound should be stopped"
    assert "Engine stopped" in mock_disp.lines[0], f"Display should show 'Engine stopped', got: {mock_disp.lines[0]}"
    assert all(px == MysteryGadget.COLOR_OFF for px in mock_strip.pixels), "All strip LEDs should be off"

    # 5. Verification completion
    Log.i("Testing complete - all checks passed")
