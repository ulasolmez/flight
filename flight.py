from abc import ABC
from collections.abc import MutableMapping
import csv
from random import randrange
from datetime import datetime, timedelta


class MapBase(MutableMapping, ABC):
    class _Item:
        __slots__ = '_key', '_value'

        def __init__(self, key, value):
            self._key = key
            self._value = value

        def __eq__(self, other):
            return self._key == other._key

        def __ne__(self, other):
            return not self == other

        def __lt__(self, other):
            return self._key < other._key


class SortedTableMap(MapBase):
    """
    Map implementation using a sorted table.
    """

    # nonpublic behaviors
    def _find_index(self, k, low, high):
        """
        Return index of the leftmost item with key greater than or equal to k.
        Return high + 1 if no such item qualifies.
        That is, j will be returned such that:
            all items of slice table[low:j] have key < k
            all items of slice table[j:high+1] have key >= k
        """
        if high < low:
            # no element qualifies
            return high + 1
        else:
            mid = (low + high) // 2
            if k == self._table[mid]._key:
                # found exact match
                return mid
            elif k < self._table[mid]._key:
                # note: may return mid
                return self._find_index(k, low, mid - 1)
            else:
                # answer is right of mid
                return self._find_index(k, mid + 1, high)

    # public behaviors
    def __init__(self):
        """
        Create an empty map.
        """
        self._table = []

    def __len__(self):
        """
        Return number of items in the map.
        """
        return len(self._table)

    def __getitem__(self, k):
        """
        Return value associated with key k (raise KeyError if not found).
        """
        j = self._find_index(k, 0, len(self._table) - 1)
        if j == len(self._table) or self._table[j]._key != k:
            raise KeyError('Key Error:' + repr(k))
        return self._table[j]._value

    def __setitem__(self, k, v):
        """
        Assign value v to key k, overwriting existing value if present.
        """
        j = self._find_index(k, 0, len(self._table) - 1)
        if j < len(self._table) and self._table[j]._key == k:
            # reassign value
            self._table[j]._value = v
        else:
            # adds new item
            self._table.insert(j, self._Item(k, v))

    def __delitem__(self, k):
        """
        Remove item associated with key k (raise KeyError if not found).
        """
        j = self._find_index(k, 0, len(self._table) - 1)
        if j == len(self._table) or self._table[j]._key != k:
            raise KeyError('Key Error: ' + repr(k))
        # delete item
        self._table.pop(j)

    def __iter__(self):
        """
        Generate keys of the map ordered from minimum to maximum.
        """
        for item in self._table:
            yield item._key

    def __reversed__(self):
        """
        Generate keys of the map ordered from maximum to minimum.
        """
        for item in reversed(self._table):
            yield item._key

    def find_min(self):
        """
        Return (key, value) pair with minimum key (or None if empty).
        """
        if len(self._table) > 0:
            return self._table[0]._key, self._table[0]._value
        else:
            return None

    def find_max(self):
        """
        Return (key, value) pair with maximum key (or None if empty).
        """
        if len(self._table) > 0:
            return self._table[-1]._key, self._table[-1]._value
        else:
            return None

    def find_ge(self, k):
        """
        Return (key, value) pair with least key greater than or equal to k.
        """
        # j's key >= k
        j = self._find_index(k, 0, len(self._table) - 1)
        if j < len(self._table):
            return self._table[j]._key, self._table[j]._value
        else:
            return None

    def find_lt(self, k):
        """
        Return (key, value) pair with greatest key strictly less than k.
        """
        # j's key >= k
        j = self._find_index(k, 0, len(self._table) - 1)
        if j > 0:
            # note use of j-1
            return self._table[j - 1]._key, self._table[j - 1]._value
        else:
            return None

    def find_gt(self, k):
        """
        Return (key, value) pair with least key strictly greater than k.
        """
        # j's key >= k
        j = self._find_index(k, 0, len(self._table) - 1)
        if j < len(self._table) and self._table[j]._key == k:
            # advanced past match
            j += 1
        if j < len(self._table):
            return self._table[j]._key, self._table[j]._value
        else:
            return None

    def find_range(self, start, stop):
        """
        Iterate all (key, value) pairs such that start <= key <= stop.
        If start is None, iteration begins with minimum key of map.
        If stop is None, iteration continues through the maximum key of map.
        """
        if start is None:
            j = 0
        else:
            # find first result
            j = self._find_index(start, 0, len(self._table) - 1)
        while j < len(self._table) and (stop is None or self._table[j]._key < stop):
            yield self._table[j]._key, self._table[j]._value
            j += 1

class Flight:
    def __init__(self, origin, destination, date, time, flight_number, seats_first, seats_coach, duration, fare):
        """
        Initializes a new Flight instance with the specified attributes.

        Parameters:
        - origin: The origin airport code.
        - destination: The destination airport code.
        - date: The departure date in the format "ddMon" (e.g., "05May").
        - time: The departure time in the format "hh:mm" (e.g., "09:30").
        - flight_number: The unique identifier for the flight.
        - seats_first: The number of available seats in the first class.
        - seats_coach: The number of available seats in the coach class.
        - duration: The duration of the flight in the format "XhYm" (e.g., "2h30m").
        - fare: The fare for the flight.
        """
        self.origin = origin
        self.destination = destination
        self.date = date
        self.time = time
        self.flight_number = flight_number
        self.seats_first = seats_first
        self.seats_coach = seats_coach
        self.duration = self._convert_to_date_time(duration)
        self.fare = fare

    def __lt__(self, other):
        """
        Implements the less-than comparison for sorting based on origin, destination, date, and time.

        Parameters:
        - other: Another Flight object for comparison.

        Returns:
        - True if the current flight is less than the other flight, False otherwise.
        """
        if self.origin != other.origin:
            return self.origin < other.origin

        if self.destination != other.destination:
            return self.destination < other.destination

        if self.date != other.date:
            self_date = datetime.strptime(self.date, "%d%b")
            other_date = datetime.strptime(other.date, "%d%b")
            return self_date < other_date

        if self.time != other.time:
            return self.time < other.time

        return False

    def check_seat_availability(self, class_type):
        if class_type == 'first':
            return self.seats_first
        elif class_type == 'coach':
            return self.seats_coach
        else:
            return 0

    def book_seat(self, class_type):
        """
        Books a seat for the specified class type and updates the available seats.

        Parameters:
        - class_type: A string indicating the class type ('first' or 'coach').

        Returns:
        - True if booking is successful, False otherwise.
        """
        if class_type == 'first' and self.seats_first > 0:
            self.seats_first -= 1
            return True
        elif class_type == 'coach' and self.seats_coach > 0:
            self.seats_coach -= 1
            return True
        else:
            return False

    def cancel_booking(self, class_type):
        if class_type == 'first':
            self.seats_first += 1
            return True
        elif class_type == 'coach':
            self.seats_coach += 1
            return True
        else:
            return False

    def calculate_flight_duration(self):
        """
        Calculates and returns the total duration of the flight as a timedelta object.
        """
        return self.duration

    def _convert_to_date_time(self, duration):

        hours, minutes = map(int, duration[:-1].split('h'))
        return timedelta(hours=hours, minutes=minutes)


class FlightDatabase:
    def __init__(self):
        """
        Initializes an instance of the FlightDatabase class, creating an internal SortedTableMap to store flights.
        """
        self._flights = SortedTableMap()

    def add_flight(self, flight):
        key = flight.origin, flight.destination, flight.date, flight.time

        flight.seats_first = int(flight.seats_first)
        flight.seats_coach = int(flight.seats_coach)

        if key in self._flights:
            print(f"Warning: Duplicate flight found for {key}. Skipping addition.")
        else:
            self._flights[key] = flight

    def find_flights(self, origin, destination, date, time_start, time_end):
        """
        Finds flights within a specified time range based on origin, destination, date, and time.

        Parameters:
        - origin: The origin airport code.
        - destination: The destination airport code.
        - date: The date of the flights.
        - time_start: The start time of the range.
        - time_end: The end time of the range.

        Returns:
        - A list of Flight objects within the specified time range.
        """
        result_flights = []
        for key, flight in self._flights.items():
            if (
                key[0] == origin
                and key[1] == destination
                and key[2] == date
                and time_start <= key[3] <= time_end
            ):
                result_flights.append(flight)
        return result_flights
    
    def display_all_flights(self):
        """
        Displays all flights in the database.
        """
        print("All Flights in the Database:")
        for flight in self._flights.values():
            print(f"{flight.origin} to {flight.destination} on {flight.date} at {flight.time}")

    def read_flights_from_file(self, filename):
        """
        Reads flight data from a CSV file and adds it to the database.

        Parameters:
        - filename: The name of the CSV file containing flight information.
        """
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                flight = Flight(*row)
                self.add_flight(flight)

    def check_seat_availability(self, origin, destination, date, time, class_type):
        """
        Checks seat availability for a specific flight and class type.

        Parameters:
        - origin: The origin airport code.
        - destination: The destination airport code.
        - date: The date of the flight.
        - time: The departure time of the flight.
        - class_type: A string indicating the class type ('first' or 'coach').

        Returns:
        - The number of available seats for the specified class type, or None if the flight is not found.
        """
        key = origin, destination, date, time
        if key in self._flights:
            return self._flights[key].check_seat_availability(class_type)
        else:
            return None

    def book_seat(self, origin, destination, date, time, class_type):
        """
        Books a seat for a specific flight and class type, updating available seats.

        Parameters:
        - origin: The origin airport code.
        - destination: The destination airport code.
        - date: The date of the flight.
        - time: The departure time of the flight.
        - class_type: A string indicating the class type ('first' or 'coach').

        Returns:
        - True if booking is successful, False otherwise.
        """
        key = origin, destination, date, time
        if key in self._flights:
            return self._flights[key].book_seat(class_type)
        else:
            return False

    def cancel_booking(self, origin, destination, date, time, class_type):
        """
        Cancels a booking for a specific flight and class type, updating available seats.

        Parameters:
        - origin: The origin airport code.
        - destination: The destination airport code.
        - date: The date of the flight.
        - time: The departure time of the flight.
        - class_type: A string indicating the class type ('first' or 'coach').

        Returns:
        - True if cancellation is successful, False otherwise.
        """
        key = origin, destination, date, time
        if key in self._flights:
            return self._flights[key].cancel_booking(class_type)
        else:
            return False

    def calculate_flight_duration(self, origin, destination, date, time):
        """
        Calculates the flight duration for a specific flight.

        Parameters:
        - origin: The origin airport code.
        - destination: The destination airport code.
        - date: The date of the flight.
        - time: The departure time of the flight.

        Returns:
        - A timedelta object representing the flight duration, or None if the flight is not found.
        """
        key = origin, destination, date, time
        if key in self._flights:
            return self._flights[key].calculate_flight_duration()
        else:
            return None


if __name__ == "__main__":
    # Example usage
    flight_db = FlightDatabase()

    # Read flights from a file
    flight_db.read_flights_from_file("flights.csv")

    # Display all flights in the database
    flight_db.display_all_flights()

    # Example usage of additional methods
    print("\nChecking seat availability for UA789 on 09May at 14:45 (First Class):")
    print(f"Available seats: {flight_db.check_seat_availability('LAX', 'SFO', '09May', '14:45', 'first')}")

    print("\nBooking a seat for UA789 on 09May at 14:45 (Coach Class):")
    if flight_db.book_seat('LAX', 'SFO', '09May', '14:45', 'coach'):
        print("Booking successful.")
    else:
        print("Booking failed. No available seats.")

    print("\nCancelling a booking for UA789 on 09May at 14:45 (First Class):")
    if flight_db.cancel_booking('LAX', 'SFO', '09May', '14:45', 'first'):
        print("Cancellation successful.")
    else:
        print("Cancellation failed. No booking found.")

    print("\nCalculating flight duration for UA789 on 09May at 14:45:")
    duration = flight_db.calculate_flight_duration('LAX', 'SFO', '09May', '14:45')
    print(f"Flight duration: {duration}")
