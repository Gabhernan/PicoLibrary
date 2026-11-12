"""
# NamePlate.py
# Controller for the dynamic office nameplate system coordinating model, view, and input buttons.
# Author: Gabriella Hernandez
"""

try:
    import utime as time
except ImportError:
    import time

from Log import *
from Enums import Availability
from Employee import Employee
from NamePlateView import NamePlateView


class NamePlate:
    """
    **NamePlate** is the central controller for the dynamic nameplate system.

    It coordinates:
    - **Model**: A collection of `Employee` objects representing office occupants.
    - **View**: A `NamePlateView` instance managing the LCD, light strip, and buzzer.
    - **Buttons**: Hardware buttons for Next, Previous, and Availability toggling.

    Parameters:
    -----------
    employees : list[Employee]
        A list of one or more Employee instances.
    view : NamePlateView, optional
        A NamePlateView instance (if None, a new NamePlateView is instantiated).
    buttons : list, optional
        A list of Button instances (if None, default buttons are instantiated on GP19, GP20, GP21).
    next_pin : int, optional
        GPIO pin for Next button (default: 19).
    prev_pin : int, optional
        GPIO pin for Previous button (default: 20).
    avail_pin : int, optional
        GPIO pin for Availability button (default: 21).

    Examples:
    ---------
    1. Instantiating and running NamePlate:
       ```python
       nameplate = NamePlate(employees=[prof, staff])
       nameplate.run()
       ```
    """

    def __init__(self, employees: list, view: NamePlateView = None, buttons: list = None,
                 next_pin: int = 19, prev_pin: int = 20, avail_pin: int = 21):
        if not employees:
            raise ValueError("NamePlate must be initialized with at least one Employee.")

        self._employees = employees
        self._currentPerson = 0
        self._currentPage = 0

        # Initialize View
        if view is not None:
            self._view = view
        else:
            self._view = NamePlateView()

        # Initialize Buttons
        if buttons is not None:
            self._buttons = buttons
        else:
            try:
                from Button import Button
                self._buttons = [
                    Button(next_pin, "Next", handler=self, lowActive=True),
                    Button(prev_pin, "Previous", handler=self, lowActive=True),
                    Button(avail_pin, "Availability", handler=self, lowActive=True),
                ]
                Log.i(f"NamePlate: Initialized 3 buttons on pins GP{next_pin}, GP{prev_pin}, GP{avail_pin}")
            except Exception as e:
                Log.w(f"NamePlate: Could not initialize hardware Buttons ({e}). Using mock/empty buttons.")
                self._buttons = []

        Log.i(f"NamePlate controller initialized with {len(self._employees)} employees")

    def _updateDisplay(self) -> None:
        """Helper to sync view with the current employee's info and availability."""
        emp = self._employees[self._currentPerson]
        pages = emp.displayInfo()

        # Set availability light
        self._view.showAvailability(emp.getAvailability())

        # Render current page
        if pages:
            self._currentPage = self._currentPage % len(pages)
            self._view.showPage(pages[self._currentPage])

    def previousEmployee(self) -> None:
        """
        Switch to the previous employee in the roster, wrap around, play sound,
        and update display.
        """
        self._currentPerson = (self._currentPerson - 1) % len(self._employees)
        self._currentPage = 0
        Log.i(f"NamePlate: Switched to previous employee index {self._currentPerson} ({self._employees[self._currentPerson].getName()})")
        self._view.playSwitchSound()
        self._updateDisplay()

    def nextEmployee(self) -> None:
        """
        Switch to the next employee in the roster, wrap around, play sound,
        and update display.
        """
        self._currentPerson = (self._currentPerson + 1) % len(self._employees)
        self._currentPage = 0
        Log.i(f"NamePlate: Switched to next employee index {self._currentPerson} ({self._employees[self._currentPerson].getName()})")
        self._view.playSwitchSound()
        self._updateDisplay()

    def nextPage(self) -> None:
        """
        Rotate to the next information page for the currently displayed employee.
        """
        emp = self._employees[self._currentPerson]
        pages = emp.displayInfo()
        if pages:
            self._currentPage = (self._currentPage + 1) % len(pages)
            Log.d(f"NamePlate: Rotating to page {self._currentPage + 1}/{len(pages)} for {emp.getName()}")
            self._view.showPage(pages[self._currentPage])

    def buttonPressed(self, name: str) -> None:
        """
        Handle button push event dispatched from a Button instance.

        Parameters:
        -----------
        name : str
            Name of the button pressed ('Next', 'Previous', or 'Availability').
        """
        Log.i(f"NamePlate.buttonPressed: '{name}'")
        if name == "Next":
            self.nextEmployee()
        elif name == "Previous":
            self.previousEmployee()
        elif name == "Availability":
            current_emp = self._employees[self._currentPerson]
            current_emp.availabilityChange()
            self._view.showAvailability(current_emp.getAvailability())
        else:
            Log.w(f"NamePlate.buttonPressed: Unrecognized button '{name}'")

    def buttonReleased(self, name: str) -> None:
        """
        Handle button release event dispatched from a Button instance.

        Parameters:
        -----------
        name : str
            Name of the button released.
        """
        Log.d(f"NamePlate.buttonReleased: '{name}'")

    def run(self, max_rotations: int = None, rotation_delay_ms: int = 2500) -> None:
        """
        Start the dynamic nameplate controller execution loop.

        Rotates LCD pages every `rotation_delay_ms` milliseconds without blocking
        interrupt-driven button callbacks.

        Parameters:
        -----------
        max_rotations : int, optional
            Maximum page rotations before returning (useful for self-testing).
            If None (default), runs continuously until interrupted.
        rotation_delay_ms : int, optional
            Milliseconds between automatic page rotations (default: 2500ms).
        """
        Log.i("NamePlate: Starting run loop...")
        self._updateDisplay()

        rotations = 0
        try:
            # Check if time.ticks_ms is available (MicroPython)
            has_ticks = hasattr(time, "ticks_ms")
            last_rotation = time.ticks_ms() if has_ticks else time.time()

            while max_rotations is None or rotations < max_rotations:
                time.sleep(0.05)  # Yield CPU to allow IRQ callbacks to process

                if has_ticks:
                    now = time.ticks_ms()
                    diff = time.ticks_diff(now, last_rotation)
                else:
                    now = time.time()
                    diff = (now - last_rotation) * 1000

                if diff >= rotation_delay_ms:
                    self.nextPage()
                    last_rotation = now
                    rotations += 1

        except KeyboardInterrupt:
            Log.i("NamePlate: Execution stopped by user.")


if __name__ == "__main__":
    Log.i("Testing NamePlate.py...")
    from NamePlateView import MockLCDDisplay, MockLightStrip, MockPassiveBuzzer
    from Employee import Staff, Faculty

    # Create mock view
    mock_disp = MockLCDDisplay()
    mock_strip = MockLightStrip(numleds=8)
    mock_buz = MockPassiveBuzzer()
    test_view = NamePlateView(display=mock_disp, lightstrip=mock_strip, buzzer=mock_buz)

    # Create test employees
    e1 = Faculty("Prof. Smith", "Professor", "CS", "smith@univ.edu", "x1000", courses=["CS101"])
    e2 = Staff("Jane Jones", "Staff Coord", "CS", "jones@univ.edu", "x2000", walkinsAccepted=True)

    controller = NamePlate(employees=[e1, e2], view=test_view, buttons=[])

    # Initial state
    assert controller._currentPerson == 0
    assert controller._currentPage == 0
    controller._updateDisplay()
    assert "Prof. Smith" in mock_disp.lines[0]
    assert mock_strip.color == NamePlateView.COLOR_AVAILABLE

    # 1. Test nextPage
    controller.nextPage()
    assert controller._currentPage == 1

    # 2. Test nextEmployee
    controller.buttonPressed("Next")
    assert controller._currentPerson == 1
    assert controller._currentPage == 0
    assert "Jane Jones" in mock_disp.lines[0]
    assert mock_buz.last_tone == 1000

    # 3. Test Availability button
    controller.buttonPressed("Availability")
    assert e2.getAvailability() == Availability.AWAY
    assert mock_strip.color == NamePlateView.COLOR_AWAY

    # 4. Test previousEmployee
    controller.buttonPressed("Previous")
    assert controller._currentPerson == 0
    assert "Prof. Smith" in mock_disp.lines[0]

    # 5. Test buttonReleased
    controller.buttonReleased("Next")

    # 6. Test short run loop
    Log.i("Testing run() with 2 rotations...")
    controller.run(max_rotations=2, rotation_delay_ms=100)

    Log.i("Testing complete - all checks passed")
