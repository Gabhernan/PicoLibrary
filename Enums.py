"""
# Enums.py
# Enumerations for Employee Availability status and Student Worker Degree Levels.
# Author: Gabriella Hernandez
"""

from Log import *


class Availability:
    """
    **Availability** defines the valid availability states for an office employee.

    States:
    -------
    - `AVAILABLE`: Employee is present and available in the office.
    - `AWAY`: Employee is temporarily away from the desk/office.
    - `BUSY`: Employee is in a meeting, class, or do-not-disturb mode.

    Examples:
    ---------
    1. Check status:
       ```python
       current = Availability.AVAILABLE
       if current == Availability.AVAILABLE:
           Log.i("Employee is available")
       ```
    2. Cycle status:
       ```python
       next_status = Availability.next(Availability.AVAILABLE)
       # Returns Availability.AWAY
       ```
    """

    AVAILABLE = "Available"
    AWAY = "Away"
    BUSY = "Busy"

    @classmethod
    def next(cls, current):
        """
        Cycle through availability states in order:
        Available -> Away -> Busy -> Available.

        Parameters:
        -----------
        current : str
            The current availability string.

        Returns:
        --------
        str : The next availability state in sequence.
        """
        cycle = {
            cls.AVAILABLE: cls.AWAY,
            cls.AWAY: cls.BUSY,
            cls.BUSY: cls.AVAILABLE,
        }
        return cycle.get(current, cls.AVAILABLE)


class DegreeLevel:
    """
    **DegreeLevel** defines the academic standing of student workers.

    Levels:
    -------
    - `UNDERGRADUATE`: Undergraduate student worker.
    - `MASTERS`: Master's degree student worker.
    - `PHD`: Doctoral degree student worker.

    Examples:
    ---------
    1. Assign degree level:
       ```python
       level = DegreeLevel.UNDERGRADUATE
       ```
    """

    UNDERGRADUATE = "Undergrad"
    MASTERS = "Masters"
    PHD = "PhD"


if __name__ == "__main__":
    Log.i("Testing Enums.py...")

    # Test Availability constants
    assert Availability.AVAILABLE == "Available"
    assert Availability.AWAY == "Away"
    assert Availability.BUSY == "Busy"

    # Test Availability cycle
    status = Availability.AVAILABLE
    status = Availability.next(status)
    assert status == Availability.AWAY, f"Expected AWAY, got {status}"

    status = Availability.next(status)
    assert status == Availability.BUSY, f"Expected BUSY, got {status}"

    status = Availability.next(status)
    assert status == Availability.AVAILABLE, f"Expected AVAILABLE, got {status}"

    # Test invalid fallback
    assert Availability.next("Unknown") == Availability.AVAILABLE

    # Test DegreeLevel constants
    assert DegreeLevel.UNDERGRADUATE == "Undergrad"
    assert DegreeLevel.MASTERS == "Masters"
    assert DegreeLevel.PHD == "PhD"

    Log.i("Testing complete - all checks passed")
