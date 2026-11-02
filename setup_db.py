"""Create travel.db with tables and sample data.   Run:  python setup_db.py
Running it again resets everything to the starting data.
"""
import random
import sqlite3
from datetime import date, datetime, timedelta

from common.db import DB_PATH

random.seed(7)

SCHEMA = """
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS flights;

CREATE TABLE flights (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_no       TEXT NOT NULL,
    airline         TEXT NOT NULL,
    origin          TEXT NOT NULL,
    destination     TEXT NOT NULL,
    depart_date     TEXT NOT NULL,      -- YYYY-MM-DD
    depart_time     TEXT NOT NULL,      -- HH:MM
    arrive_time     TEXT NOT NULL,      -- HH:MM
    price           REAL NOT NULL,      -- Rs
    seats_available INTEGER NOT NULL
);

CREATE TABLE payments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_ref  TEXT NOT NULL UNIQUE,
    payer_name   TEXT NOT NULL,
    card_last4   TEXT NOT NULL,
    amount       REAL NOT NULL,
    status       TEXT NOT NULL,         -- SUCCESS / DECLINED / REFUNDED
    message      TEXT,
    created_at   TEXT NOT NULL
);

CREATE TABLE bookings (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_ref    TEXT NOT NULL UNIQUE,
    passenger_name TEXT NOT NULL,
    email          TEXT NOT NULL,
    flight_id      INTEGER NOT NULL REFERENCES flights(id),
    payment_ref    TEXT NOT NULL REFERENCES payments(payment_ref),
    status         TEXT NOT NULL,       -- CONFIRMED / CANCELLED
    created_at     TEXT NOT NULL
);
"""

# origin, destination, typical fare, flight time in minutes
ROUTES = [
    ("Delhi", "Mumbai", 4800, 130), ("Mumbai", "Delhi", 4700, 130),
    ("Delhi", "Goa", 5600, 165), ("Goa", "Delhi", 5500, 165),
    ("Delhi", "Bengaluru", 5900, 170), ("Bengaluru", "Delhi", 5800, 170),
    ("Mumbai", "Goa", 3100, 70), ("Goa", "Mumbai", 3000, 70),
    ("Mumbai", "Bengaluru", 3600, 105), ("Bengaluru", "Mumbai", 3500, 105),
    ("Delhi", "Hyderabad", 5200, 150), ("Hyderabad", "Delhi", 5100, 150),
    ("Bengaluru", "Chennai", 2600, 60), ("Chennai", "Bengaluru", 2500, 60),
    ("Delhi", "Kolkata", 5400, 145), ("Kolkata", "Delhi", 5300, 145),
]
AIRLINES = [("6E", "IndiGo"), ("AI", "Air India"), ("QP", "Akasa Air"), ("SG", "SpiceJet")]
TIMES = ["06:15", "09:40", "13:20", "18:05", "21:30"]


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    today = date.today()
    for day in range(1, 15):                                  # the next 14 days
        d = (today + timedelta(days=day)).isoformat()
        for origin, destination, fare, minutes in ROUTES:
            for depart in random.sample(TIMES, 3):            # 3 flights per route per day
                code, airline = random.choice(AIRLINES)
                arrive = (datetime.strptime(depart, "%H:%M") + timedelta(minutes=minutes)).strftime("%H:%M")
                price = round(fare * random.uniform(0.85, 1.35), -1)
                conn.execute(
                    "INSERT INTO flights (flight_no, airline, origin, destination, depart_date, depart_time,"
                    " arrive_time, price, seats_available) VALUES (?,?,?,?,?,?,?,?,?)",
                    (f"{code}-{random.randint(100, 999)}", airline, origin, destination, d, depart,
                     arrive, price, random.randint(5, 40)),
                )

    # A little history so "show my bookings" works on day one.
    now = datetime.now().isoformat(timespec="seconds")
    samples = [
        ("BKDEMO01", "Rahul Sharma", "rahul@example.com", "CONFIRMED"),
        ("BKDEMO02", "Rahul Sharma", "rahul@example.com", "CANCELLED"),
        ("BKDEMO03", "Anita Rao", "anita@example.com", "CONFIRMED"),
    ]
    for number, (ref, name, email, status) in enumerate(samples, start=1):
        flight = conn.execute("SELECT id, price FROM flights WHERE id = ?", (number * 40,)).fetchone()
        pay_ref = f"PAYDEMO0{number}"
        conn.execute(
            "INSERT INTO payments (payment_ref, payer_name, card_last4, amount, status, message, created_at)"
            " VALUES (?,?,?,?,?,?,?)",
            (pay_ref, name, "4242", flight[1], "REFUNDED" if status == "CANCELLED" else "SUCCESS", "Sample data", now),
        )
        conn.execute(
            "INSERT INTO bookings (booking_ref, passenger_name, email, flight_id, payment_ref, status, created_at)"
            " VALUES (?,?,?,?,?,?,?)",
            (ref, name, email, flight[0], pay_ref, status, now),
        )

    conn.commit()
    for table in ("flights", "payments", "bookings"):
        print(f"{table:9} {conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]} rows")
    conn.close()
    print(f"Database ready: {DB_PATH}")


if __name__ == "__main__":
    main()
