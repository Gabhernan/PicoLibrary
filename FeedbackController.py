"""
# FeedbackController.py
# State machine controller for the customer satisfaction kiosk
# Author: Gabriella Hernandez
"""

import time
from Log import *
from StateModel import StateModel
from Counters import SoftwareTimer
from Sensors_advanced import UltrasonicSensor
from Button import Button
from Displays import LCDDisplay
from LightStrip import LightStrip
from Lights import GREEN, YELLOW, RED, BLACK
from Buzzer import PassiveBuzzer
from FeedbackStats import FeedbackStats

class FeedbackController:
    """
    FeedbackController is the controller and StateModel handler for the Satisfaction Kiosk.
    It manages the finite state machine transitions, controls the hardware peripherals
    (LCD display, NeoPixel light strip, passive buzzer, ultrasonic sensor, and buttons),
    and coordinates customer feedback recording and manager alarm escalation.

    Examples
    --------
    >>> controller = FeedbackController()
    >>> controller.run()
    """

    def __init__(self):
        Log.i("FeedbackController __init__: initializing hardware and models")

        # 1. Initialize hardware drivers with specified Wokwi pins
        self._display = LCDDisplay(sda=0, scl=1)
        self._buzzer = PassiveBuzzer(pin=16, name="PassiveBuzzer")
        self._sensor = UltrasonicSensor(trigger=14, echo=15, name="uss", lowActive=True, threshold=10.0)
        self._green_button = Button(21, "green", handler=None, lowActive=True)
        self._yellow_button = Button(20, "yellow", handler=None, lowActive=True)
        self._red_button = Button(19, "red", handler=None, lowActive=True)
        self._lightstrip = LightStrip(pin=2, name="LightStrip", numleds=8, brightness=0.5)

        # 2. Initialize timer and stats model
        self._timer = SoftwareTimer(name="timer", handler=None)
        self._stats = FeedbackStats(threshold=30.0, startlevel=50.0, minVotes=5)

        # 3. State management variables
        self._voteTime = 0
        self._alarm_sound_muted = False
        self._meter_restored = False

        # Non-blocking animation tracking for stateDo
        self._last_flash_time = 0
        self._flash_state = False
        self._last_tone_time = 0
        self._tone_index = 0

        # 4. Initialize StateModel with 6 states (0: Welcome, 1: Rate, 2: Happy, 3: Neutral, 4: Unhappy, 5: Alarm)
        self._model = StateModel(6, self, debug=True)

        # 5. Register buttons, sensors, and timer with StateModel
        self._model.addButton(self._green_button)
        self._model.addButton(self._yellow_button)
        self._model.addButton(self._red_button)
        self._model.addSensor(self._sensor)
        self._model.addTimer(self._timer)

        # 6. Configure static transitions
        # State 0 (Welcome) -> State 1 (Rate) when someone approaches within 10cm
        self._model.addTransition(0, ["uss_trip"], 1)

        # State 1 (Rate) transitions
        self._model.addTransition(1, ["timer_timeout"], 0)
        self._model.addTransition(1, ["green_press"], 2)
        self._model.addTransition(1, ["yellow_press"], 3)
        self._model.addTransition(1, ["red_press"], 4)

        # State 2 (Happy) -> State 0 on timeout
        self._model.addTransition(2, ["timer_timeout"], 0)

        # Note: States 3 (Neutral) and 4 (Unhappy) omit static timer_timeout transitions;
        # their timeout branching is handled dynamically in stateEvent() per Approach 1.

        # State 5 (Alarm) -> State 0 on green_press (manager reset)
        self._model.addTransition(5, ["green_press"], 0)

    def update_meter(self) -> None:
        """
        Update the NeoPixel light strip to display the satisfaction meter.
        The number of lit LEDs reflects the positive percentage, and the color
        reflects the satisfaction band (Green >= 50%, Yellow 30-49%, Red < 30%).
        """
        level = self._stats.get_light_level()
        color = self._stats.get_meter_color()
        self._lightstrip.setColor(color, level)
        Log.i(f"Satisfaction meter updated: {level}/8 LEDs lit with color {color}")

    def stateEntered(self, state: int, event: str) -> None:
        """
        Perform entry actions for the newly entered state.
        """
        Log.d(f"Entering State {state} on event '{event}'")

        if state == 0:
            # 0 - Welcome: Display greeting and show the satisfaction meter
            self._buzzer.stop()
            self._display.reset()
            self._display.showText("Welcome to", 0, 0)
            self._display.showText("Home Depot", 1, 0)
            self.update_meter()

        elif state == 1:
            # 1 - Rate: Prompt the customer and start the 5-second inactivity timer
            self._display.reset()
            self._display.showText("How was your", 0, 0)
            self._display.showText("visit?", 1, 0)
            self._timer.start(5)

        elif state == 2:
            # 2 - Happy: Record happy vote, show green, play high tone, start 5s timer
            self._display.reset()
            self._display.showText("Thank you!", 0, 0)
            self._stats.add_happy()
            self._lightstrip.setColor(GREEN)
            self._voteTime = time.ticks_ms()
            self._meter_restored = False
            self._buzzer.beep(1046, 150)  # High C (1046 Hz)
            self._timer.start(5)

        elif state == 3:
            # 3 - Neutral: Record neutral vote, show yellow, play neutral tone, start 5s timer
            self._display.reset()
            self._display.showText("Thank you!", 0, 0)
            self._display.showText("Hope for better", 1, 0)
            self._stats.add_neutral()
            self._lightstrip.setColor(YELLOW)
            self._voteTime = time.ticks_ms()
            self._meter_restored = False
            self._buzzer.beep(523, 150)  # Middle C (523 Hz)
            self._timer.start(5)

        elif state == 4:
            # 4 - Unhappy: Record sad vote, show red, play sad tone, start 5s timer
            self._display.reset()
            self._display.showText("Sorry to hear", 0, 0)
            self._display.showText("that", 1, 0)
            self._stats.add_sad()
            self._lightstrip.setColor(RED)
            self._voteTime = time.ticks_ms()
            self._meter_restored = False
            self._buzzer.beep(261, 250)  # Low C (261 Hz)
            self._timer.start(5)

        elif state == 5:
            # 5 - Alarm: Display alert, start flashing red light & 2-tone alarm
            self._alarm_sound_muted = False
            self._display.reset()
            self._display.showText("Calling", 0, 0)
            self._display.showText("Manager!", 1, 0)
            now = time.ticks_ms()
            self._last_flash_time = now
            self._flash_state = True
            self._lightstrip.setColor(RED)
            self._last_tone_time = now
            self._tone_index = 0
            self._buzzer.play(880)

    def stateLeft(self, state: int, event: str) -> None:
        """
        Perform exit actions when leaving a state.
        """
        Log.d(f"Leaving State {state} on event '{event}'")

        if state == 5:
            # Exiting Alarm state (on green_press): reset statistics and mute alarm
            self._buzzer.stop()
            self._stats.reset()
            self._alarm_sound_muted = False
        elif state in (1, 2, 3, 4):
            # Leaving interaction states: cancel timer and stop any active sound
            self._timer.cancel()
            self._buzzer.stop()

    def stateDo(self, state: int) -> None:
        """
        Execute non-blocking periodic activity for the current active state.
        Never use sleep() here so button interrupts and polling remain responsive.
        """
        now = time.ticks_ms()

        # States 2, 3, 4: Revert light strip to satisfaction meter after 1 second
        if state in (2, 3, 4):
            if not self._meter_restored and time.ticks_diff(now, self._voteTime) >= 1000:
                self.update_meter()
                self._meter_restored = True

        # State 5: Non-blocking flashing red light and 2-tone alarm
        elif state == 5:
            # Toggle light every 250ms
            if time.ticks_diff(now, self._last_flash_time) >= 250:
                self._last_flash_time = now
                self._flash_state = not self._flash_state
                self._lightstrip.setColor(RED if self._flash_state else BLACK)

            # Alternate buzzer between 880Hz and 440Hz every 250ms if not muted
            if not self._alarm_sound_muted:
                if time.ticks_diff(now, self._last_tone_time) >= 250:
                    self._last_tone_time = now
                    self._tone_index = 1 - self._tone_index
                    tone = 880 if self._tone_index == 1 else 440
                    self._buzzer.play(tone)
            else:
                self._buzzer.stop()

    def stateEvent(self, state: int, event: str) -> bool:
        """
        Handle dynamic in-state events and guarded branching without modifying StateModel.
        - States 3 & 4: Evaluates [is_below_threshold()] on timer_timeout.
        - State 5: Handles red_press to mute alarm sound while staying in Alarm state.
        """
        # Guarded timeout branching for Neutral (3) and Unhappy (4)
        if state in (3, 4) and event == "timer_timeout":
            if self._stats.is_below_threshold():
                Log.i(f"State {state} timeout: Feedback below threshold -> Transitioning to State 5 (Alarm)")
                self._model.gotoState(5, "timer_timeout")
            else:
                Log.i(f"State {state} timeout: Feedback above threshold -> Transitioning to State 0 (Welcome)")
                self._model.gotoState(0, "timer_timeout")
            return True

        # State 5: Manager button (red) mutes the alarm sound
        elif state == 5 and event == "red_press":
            Log.i("State 5 internal event: Manager pressed RED button. Silencing alarm sound.")
            self._alarm_sound_muted = True
            self._buzzer.stop()
            return True

        return False

    def run(self) -> None:
        """
        Start the state model loop. Starts at State 0 (Welcome).
        """
        Log.i("FeedbackController starting state model loop")
        self._model.run()

    def stop(self) -> None:
        """
        Stop the state model loop and turn off peripherals.
        """
        Log.i("FeedbackController stopping")
        self._model.stop()
        self._buzzer.stop()
        self._lightstrip.off()
        self._display.reset()


if __name__ == "__main__":
    Log.i("Running FeedbackController self-contained test instantiation...")
    try:
        controller = FeedbackController()
        Log.i("FeedbackController instantiated successfully!")
    except Exception as e:
        Log.e(f"Instantiation failed (expected if running off-board without hardware): {e}")
