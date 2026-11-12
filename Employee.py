"""
# Employee.py
# Object-Oriented Employee hierarchy supporting Faculty, Staff, StudentWorker, and Administrator roles.
# Author: Gabriella Hernandez
"""

from Log import *
from Enums import Availability, DegreeLevel
from Calendar import Calendar


class Employee:
    """
    **Employee** is the base class for all university building personnel.

    It stores general contact, position, and availability details, and defines
    polymorphic display formatting and availability cycling.

    Parameters:
    -----------
    name : str
        Full name of the employee.
    title : str
        Job position or academic title.
    department : str
        Department name or abbreviation.
    email : str
        University email address.
    phoneNumber : str
        Campus phone number or extension.
    availability : str, optional
        Initial availability state from `Availability` (default: `Availability.AVAILABLE`).

    Examples:
    ---------
    1. Creating a generic employee:
       ```python
       emp = Employee("Alex Smith", "Analyst", "IT Services", "asmith@univ.edu", "x4500")
       status = emp.getAvailability()
       pages = emp.displayInfo()
       ```
    """

    def __init__(self, name: str, title: str, department: str, email: str, phoneNumber: str, availability: str = Availability.AVAILABLE):
        self._name = name
        self._title = title
        self._department = department
        self._email = email
        self._phoneNumber = phoneNumber
        self._availability = availability
        Log.i(f"Employee initialized: {self._name} ({self._title})")

    def getName(self) -> str:
        """Return the employee's name."""
        return self._name

    def getTitle(self) -> str:
        """Return the employee's title."""
        return self._title

    def getDepartment(self) -> str:
        """Return the employee's department."""
        return self._department

    def getEmail(self) -> str:
        """Return the employee's email."""
        return self._email

    def getPhoneNumber(self) -> str:
        """Return the employee's phone number."""
        return self._phoneNumber

    def getAvailability(self) -> str:
        """
        Get current availability status.

        Returns:
        --------
        str : Value from `Availability` (Available, Away, or Busy).
        """
        return self._availability

    def availabilityChange(self) -> None:
        """
        Cycle availability manually: Available -> Away -> Busy -> Available.
        """
        old_status = self._availability
        self._availability = Availability.next(self._availability)
        Log.i(f"{self._name}: Availability changed from {old_status} to {self._availability}")

    def displayInfo(self) -> list:
        """
        Generate paginated information for a 2-line x 16-character LCD.

        Returns:
        --------
        list[tuple[str, str]] : List of 2-line page tuples.
        """
        return [
            (self._name[:16], self._title[:16]),
            (self._department[:16], self._phoneNumber[:16]),
            ("Email:"[:16], self._email[:16]),
        ]


class Staff(Employee):
    """
    **Staff** represents operational and administrative support staff.

    Parameters:
    -----------
    name, title, department, email, phoneNumber, availability :
        Standard employee parameters passed to superclass.
    walkinsAccepted : bool, optional
        Whether walk-in consultations are currently accepted (default: True).

    Examples:
    ---------
    1. Creating a staff member:
       ```python
       staff = Staff("Sarah Connor", "Admin Assistant", "Eng", "sconnor@univ.edu", "x3321", walkinsAccepted=True)
       pages = staff.displayInfo()
       ```
    """

    def __init__(self, name: str, title: str, department: str, email: str, phoneNumber: str,
                 walkinsAccepted: bool = True, availability: str = Availability.AVAILABLE):
        super().__init__(name, title, department, email, phoneNumber, availability)
        self._walkinsAccepted = walkinsAccepted
        Log.i(f"Staff member created: walkinsAccepted={self._walkinsAccepted}")

    def isWalkinsAccepted(self) -> bool:
        """Return whether walk-ins are accepted."""
        return self._walkinsAccepted

    def displayInfo(self) -> list:
        """
        Generate paginated information including walk-in policy.

        Returns:
        --------
        list[tuple[str, str]] : List of 2-line page tuples.
        """
        walk_in_text = "Accepted" if self._walkinsAccepted else "By Appt Only"
        return [
            (self._name[:16], self._title[:16]),
            (self._department[:16], self._phoneNumber[:16]),
            ("Walk-ins:"[:16], walk_in_text[:16]),
            ("Email:"[:16], self._email[:16]),
        ]


class Faculty(Employee):
    """
    **Faculty** represents instructional and research academic staff.

    Parameters:
    -----------
    name, title, department, email, phoneNumber, availability :
        Standard employee parameters passed to superclass.
    courses : list[str], optional
        List of course codes taught (default: empty list).
    officeHours : dict, optional
        Dictionary mapping days to hours strings (default: empty dict).

    Examples:
    ---------
    1. Creating a faculty member:
       ```python
       prof = Faculty("Dr. Turing", "Professor", "CS", "turing@univ.edu", "x1954",
                      courses=["CS101", "CS400"], officeHours={"Mon/Wed": "14-16"})
       pages = prof.displayInfo()
       ```
    """

    def __init__(self, name: str, title: str, department: str, email: str, phoneNumber: str,
                 courses: list = None, officeHours: dict = None, availability: str = Availability.AVAILABLE):
        super().__init__(name, title, department, email, phoneNumber, availability)
        self._courses = courses if courses is not None else []
        self._officeHours = officeHours if officeHours is not None else {}
        Log.i(f"Faculty created: courses={self._courses}, officeHours={self._officeHours}")

    def displayInfo(self) -> list:
        """
        Generate paginated information including courses and office hours.

        Returns:
        --------
        list[tuple[str, str]] : List of 2-line page tuples.
        """
        pages = [
            (self._name[:16], self._title[:16]),
            (self._department[:16], self._phoneNumber[:16]),
        ]

        # Courses page
        if self._courses:
            courses_str = ", ".join(self._courses)
            pages.append(("Courses:"[:16], courses_str[:16]))

        # Office Hours page(s)
        if self._officeHours:
            for day, hours in self._officeHours.items():
                pages.append((f"OH: {day}"[:16], str(hours)[:16]))

        pages.append(("Email:"[:16], self._email[:16]))
        return pages


class StudentWorker(Employee):
    """
    **StudentWorker** represents student assistants working in building offices.

    Parameters:
    -----------
    name, title, department, email, phoneNumber, availability :
        Standard employee parameters passed to superclass.
    major : str
        Student's academic major.
    degreeLevel : str
        Value from `DegreeLevel` (Undergrad, Masters, or PhD).
    supervisor : Employee, optional
        Associated supervising `Employee` instance (default: None).

    Examples:
    ---------
    1. Creating a student worker:
       ```python
       student = StudentWorker("Jordan Lee", "Peer Tutor", "CS", "jlee@univ.edu", "x4990",
                               major="Computer Science", degreeLevel=DegreeLevel.UNDERGRADUATE,
                               supervisor=prof)
       ```
    """

    def __init__(self, name: str, title: str, department: str, email: str, phoneNumber: str,
                 major: str = "Undeclared", degreeLevel: str = DegreeLevel.UNDERGRADUATE,
                 supervisor: Employee = None, availability: str = Availability.AVAILABLE):
        super().__init__(name, title, department, email, phoneNumber, availability)
        self._major = major
        self._degreeLevel = degreeLevel
        self._supervisor = supervisor
        Log.i(f"StudentWorker created: major={self._major}, degreeLevel={self._degreeLevel}")

    def getSupervisor(self):
        """Return the supervising Employee object."""
        return self._supervisor

    def displayInfo(self) -> list:
        """
        Generate paginated information including major, degree level, and supervisor.

        Returns:
        --------
        list[tuple[str, str]] : List of 2-line page tuples.
        """
        sup_name = self._supervisor.getName() if self._supervisor is not None else "None"
        return [
            (self._name[:16], self._title[:16]),
            (f"Major:{self._major}"[:16], f"Lvl:{self._degreeLevel}"[:16]),
            ("Supervisor:"[:16], sup_name[:16]),
            (self._department[:16], self._phoneNumber[:16]),
        ]


class Administrator(Employee):
    """
    **Administrator** represents office directors, department chairs, or deans.

    Availability is derived automatically from an associated `Calendar` instance.
    Manual cycling of availability is disabled.

    Parameters:
    -----------
    name, title, department, email, phoneNumber :
        Standard employee parameters passed to superclass.
    calendar : Calendar, optional
        Associated Calendar instance tracking busy intervals. If None, a new
        empty Calendar is instantiated.

    Examples:
    ---------
    1. Creating an administrator with a calendar:
       ```python
       admin = Administrator("Dr. Vance", "Dean", "Engineering", "vance@univ.edu", "x1000",
                             calendar=Calendar({"Monday": [("09:00", "12:00")]}))
       status = admin.getAvailability()
       ```
    """

    def __init__(self, name: str, title: str, department: str, email: str, phoneNumber: str,
                 calendar: Calendar = None):
        super().__init__(name, title, department, email, phoneNumber, availability=Availability.AVAILABLE)
        self._calendar = calendar if calendar is not None else Calendar()
        Log.i(f"Administrator created with composed Calendar: {self._name}")

    def getAvailability(self) -> str:
        """
        Query the composed Calendar to determine current availability.

        Returns:
        --------
        str : Availability.BUSY if calendar reports busy, else Availability.AVAILABLE.
        """
        if self._calendar.isBusy():
            return Availability.BUSY
        return Availability.AVAILABLE

    def availabilityChange(self) -> None:
        """
        Disabled for administrators: availability is controlled automatically by calendar.
        """
        Log.i(f"{self._name}: Manual availability change ignored (controlled by Calendar)")

    def displayInfo(self) -> list:
        """
        Generate paginated information for administrator.

        Returns:
        --------
        list[tuple[str, str]] : List of 2-line page tuples.
        """
        return [
            (self._name[:16], self._title[:16]),
            (self._department[:16], self._phoneNumber[:16]),
            ("Schedule:"[:16], "Auto-Calendar"[:16]),
            ("Email:"[:16], self._email[:16]),
        ]


if __name__ == "__main__":
    Log.i("Testing Employee.py hierarchy...")

    # 1. Base Employee
    base_emp = Employee("Generic Emp", "Specialist", "Ops", "ops@univ.edu", "x1111")
    assert base_emp.getAvailability() == Availability.AVAILABLE
    base_emp.availabilityChange()
    assert base_emp.getAvailability() == Availability.AWAY
    pages = base_emp.displayInfo()
    assert len(pages) == 3
    assert pages[0][0] == "Generic Emp"

    # 2. Staff
    staff = Staff("Sarah Connor", "Coord", "HR", "hr@univ.edu", "x2222", walkinsAccepted=True)
    staff_pages = staff.displayInfo()
    assert ("Walk-ins:", "Accepted") in staff_pages

    # 3. Faculty
    fac = Faculty("Dr. Turing", "Prof", "CS", "alan@univ.edu", "x3333",
                  courses=["CS101", "CS200"], officeHours={"Mon": "10-12"})
    fac_pages = fac.displayInfo()
    assert any("Courses:" in p[0] for p in fac_pages)

    # 4. StudentWorker with supervisor association
    student = StudentWorker("Alex Student", "Aide", "CS", "alex@univ.edu", "x4444",
                            major="CS", degreeLevel=DegreeLevel.UNDERGRADUATE, supervisor=fac)
    student_pages = student.displayInfo()
    assert student.getSupervisor() == fac
    assert any("Dr. Turing" in p[1] for p in student_pages)

    # 5. Administrator with Calendar composition
    mock_busy_cal = Calendar({"Mon": [("00:00", "23:59")]})
    admin = Administrator("Dean Vance", "Dean", "Admin", "dean@univ.edu", "x5555", calendar=mock_busy_cal)
    # With a 24-hr busy Monday, simulated on Monday:
    mon_time = (2026, 11, 2, 10, 0, 0, 0, 306)
    assert mock_busy_cal.isBusy(mon_time) is True
    # Test manual change override is a no-op:
    admin.availabilityChange()
    admin_pages = admin.displayInfo()
    assert any("Auto-Calendar" in p[1] for p in admin_pages)

    Log.i("Testing complete - all checks passed")
