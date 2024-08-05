import os
from dotenv import load_dotenv
import sys

load_dotenv()
WORKDIR = os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

import csv
from datetime import datetime, timedelta
import random

# Define the data structure
data = [
    {"specialization": "general_dentist", "dentists": [{"name": "john doe"}, {"name": "emily johnson"}]},
    {"specialization": "cosmetic_dentist", "dentists": [{"name": "jane smith"}, {"name": "lisa brown"}]},
    {"specialization": "prosthodontist", "dentists": [{"name": "michael green"}]},
    {"specialization": "pediatric_dentist", "dentists": [{"name": "sarah wilson"}]},
    {"specialization": "emergency_dentist", "dentists": [{"name": "daniel miller"}, {"name": "susan davis"}]},
    {"specialization": "oral_surgeon", "dentists": [{"name": "robert martinez"}]},
    {"specialization": "orthodontist", "dentists": [{"name": "kevin anderson"}]},
]


# Function to generate time slots
def generate_time_slots(start_time, end_time, interval_minutes):
    current_time = start_time
    time_slots = []
    while current_time < end_time:
        time_slots.append(current_time.strftime("%Y-%m-%d %H:%M"))
        current_time += timedelta(minutes=interval_minutes)
    return time_slots


# Generate CSV data
def generate_csv(filename):
    # Get the current date
    current_date = datetime.now().date()
    start_date = datetime(current_date.year, current_date.month, current_date.day)

    # Define the time slots for the month
    time_slots = []
    for day in range(30):  # Covering one month
        date = start_date + timedelta(days=day)
        if date.weekday() < 5:  # Monday to Friday
            time_slots += generate_time_slots(
                datetime(date.year, date.month, date.day, 8, 0),
                datetime(date.year, date.month, date.day, 17, 0),
                30,
            )
        elif date.weekday() == 5:  # Saturday
            time_slots += generate_time_slots(
                datetime(date.year, date.month, date.day, 9, 0),
                datetime(date.year, date.month, date.day, 13, 0),
                30,
            )

    # Mark the first two days as unavailable
    unavailable_slots = []
    for day in range(2):
        unavailable_date = start_date + timedelta(days=day)
        for slot in time_slots:
            if unavailable_date.strftime("%Y-%m-%d") in slot:
                unavailable_slots.append(slot)

    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["date_slot", "specialization", "doctor_name", "is_available", "patient_to_attend"])

        for specialization in data:
            for dentist in specialization["dentists"]:
                for slot in time_slots:
                    if slot in unavailable_slots:
                        is_available = False  # Unavailable for the first two days
                    else:
                        # Randomly assign availability (70% chance of being available)
                        is_available = random.choice([True] * 7 + [False] * 3)

                    patient_to_attend = None if is_available else random.randint(1000000, 1000100)
                    writer.writerow([slot, specialization["specialization"], dentist["name"], is_available, patient_to_attend])

if __name__ == '__main__':
    generate_csv(f"{WORKDIR}/data/syntetic_data/availability.csv")