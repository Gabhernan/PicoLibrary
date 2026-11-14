"""
# FeedbackStats.py
# Customer satisfaction statistics tracker and threshold monitor
# Author: Gabriella Hernandez
"""

from Log import *

try:
    from Lights import GREEN, YELLOW, RED
except ImportError:
    GREEN = (0, 255, 0)
    YELLOW = (255, 200, 0)
    RED = (255, 0, 0)

class FeedbackStats:
    """
    FeedbackStats maintains customer satisfaction voting data, calculates
    positive feedback percentages, determines whether feedback has fallen below
    the minimum threshold, and maps satisfaction metrics to light meter levels.

    Parameters
    ----------
    threshold : float, optional
        Minimum percentage of positive votes before triggering an alarm (default: 30.0)
    startlevel : float, optional
        Default percentage shown on meter when no votes have been cast (default: 50.0)
    minVotes : int, optional
        Minimum total votes required before the alarm threshold is enforced (default: 5)

    Examples
    --------
    >>> stats = FeedbackStats()
    >>> stats.add_happy()
    >>> stats.calculate_percentage()
    100.0
    """

    def __init__(self, threshold: float = 30.0, startlevel: float = 50.0, minVotes: int = 5):
        Log.i("FeedbackStats constructor: initializing counters")
        self._happy_count = 0
        self._sad_count = 0
        self._neutral_count = 0
        self._threshold = threshold
        self._startlevel = startlevel
        self._minVotes = minVotes

    def get_total_count(self) -> int:
        """
        Return the total number of feedback votes recorded across all categories.
        """
        return self._happy_count + self._sad_count + self._neutral_count

    def calculate_percentage(self) -> float:
        """
        Calculate and return the positive (happy) feedback percentage.
        If no votes have been recorded, returns startlevel (default: 50.0%).
        """
        total = self.get_total_count()
        if total == 0:
            return self._startlevel
        return (self._happy_count / total) * 100.0

    def add_happy(self) -> None:
        """
        Record a positive (happy) customer feedback vote.
        """
        self._happy_count += 1
        Log.i(f"Recorded Happy vote (Total Happy: {self._happy_count}, Total: {self.get_total_count()})")

    def add_sad(self) -> None:
        """
        Record a negative (sad/unhappy) customer feedback vote.
        """
        self._sad_count += 1
        Log.i(f"Recorded Sad vote (Total Sad: {self._sad_count}, Total: {self.get_total_count()})")

    def add_neutral(self) -> None:
        """
        Record a neutral customer feedback vote.
        """
        self._neutral_count += 1
        Log.i(f"Recorded Neutral vote (Total Neutral: {self._neutral_count}, Total: {self.get_total_count()})")

    def reset(self) -> None:
        """
        Reset all feedback counters to zero.
        """
        Log.i("FeedbackStats reset: clearing all vote tallies")
        self._happy_count = 0
        self._sad_count = 0
        self._neutral_count = 0

    def is_below_threshold(self) -> bool:
        """
        Check if positive feedback has fallen strictly below the threshold.
        Returns False if total votes is less than minVotes to avoid early false alarms.
        """
        total = self.get_total_count()
        if total < self._minVotes:
            Log.i(f"Threshold check deferred: only {total}/{self._minVotes} minimum votes cast")
            return False
        below = self.calculate_percentage() < self._threshold
        Log.i(f"Threshold check: Positive {self.calculate_percentage():.1f}% < {self._threshold}% is {below}")
        return below

    def get_light_level(self) -> int:
        """
        Map the current satisfaction percentage to an integer number of LEDs (0 to 8).
        Clamped between 0 and 8.
        """
        pct = self.calculate_percentage()
        leds = round((pct / 100.0) * 8)
        if leds < 0:
            leds = 0
        elif leds > 8:
            leds = 8
        return leds

    def get_meter_color(self) -> tuple:
        """
        Determine the color tuple for the satisfaction meter based on percentage.
        - Green at 50% and above
        - Yellow from 30% to 49%
        - Red below 30%
        """
        pct = self.calculate_percentage()
        if pct >= 50.0:
            return GREEN
        elif pct >= 30.0:
            return YELLOW
        else:
            return RED


if __name__ == "__main__":
    Log.i("Testing FeedbackStats...")
    stats = FeedbackStats()
    assert stats.get_total_count() == 0
    assert stats.calculate_percentage() == 50.0
    assert stats.get_light_level() == 4
    assert stats.get_meter_color() == GREEN
    assert not stats.is_below_threshold()

    # Cast 4 votes (below minVotes threshold of 5)
    stats.add_sad()
    stats.add_sad()
    stats.add_sad()
    stats.add_sad()
    assert stats.get_total_count() == 4
    assert stats.calculate_percentage() == 0.0
    assert not stats.is_below_threshold()  # still False because total < 5

    # 5th vote: neutral (5 votes total, 0% positive) -> triggers threshold
    stats.add_neutral()
    assert stats.get_total_count() == 5
    assert stats.is_below_threshold()  # Now True!
    assert stats.get_meter_color() == RED
    assert stats.get_light_level() == 0

    # Add happy votes to recover
    stats.add_happy()
    stats.add_happy()
    stats.add_happy()
    # Now: 3 happy, 1 neutral, 4 sad -> 3/8 = 37.5% -> YELLOW, not below 30%
    assert not stats.is_below_threshold()
    assert stats.get_meter_color() == YELLOW
    assert stats.get_light_level() == 3

    # Reset
    stats.reset()
    assert stats.get_total_count() == 0
    assert stats.calculate_percentage() == 50.0
    assert stats.get_light_level() == 4
    Log.i("All FeedbackStats tests passed successfully!")
