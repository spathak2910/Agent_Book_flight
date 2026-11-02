import os
import random
import smtplib
import string
from datetime import datetime
from email.message import EmailMessage

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from common.db import ROOT, execute, query

load_dotenv()
mcp = FastMCP("bookings", host="127.0.0.1", port=8002)


# --------------------------------------------------------------------------
#  Helpers
# --------------------------------------------------------------------------
def one_booking(booking_ref: str):
    rows = query(
        "SELECT b.booking_ref, b.passenger_name, b.email, b.status, b.payment_ref, b.created_at, "
        "f.id AS flight_id, f.flight_no, f.airline, f.origin, f.destination, f.depart_date, f.depart_time, f.arrive_time, f.price "
        "FROM bookings b JOIN flights f ON f.id = b.flight_id WHERE b.booking_ref = ?",
        (booking_ref.upper(),),
    )
    return rows[0] if rows else None


def ticket_text(b: dict) -> str:
    return (
        f"E-TICKET   {b['booking_ref']}\n"
        f"Passenger : {b['passenger_name']}\n"
        f"Flight    : {b['airline']} {b['flight_no']}\n"
        f"Route     : {b['origin']} -> {b['destination']}\n"
        f"Date      : {b['depart_date']}\n"
        f"Departs   : {b['depart_time']}     Arrives: {b['arrive_time']}\n"
        f"Fare paid : Rs {b['price']:,.0f}   (payment {b['payment_ref']})\n"
        f"Status    : {b['status']}\n"
    )


def ticket_html(b: dict) -> str:
    rows = [("Passenger", b["passenger_name"]), ("Flight", f"{b['airline']} {b['flight_no']}"),
            ("Route", f"{b['origin']} &rarr; {b['destination']}"), ("Date", b["depart_date"]),
            ("Departs", b["depart_time"]), ("Arrives", b["arrive_time"]), ("Fare paid", f"Rs {b['price']:,.0f}")]
    cells = "".join(f"<tr><td style='padding:6px 14px;color:#555'>{k}</td><td style='padding:6px 14px'><b>{v}</b></td></tr>" for k, v in rows)
    return (f"<div style='font-family:Arial,sans-serif;max-width:480px;border:2px solid #0f1b2d;border-radius:12px'>"
            f"<div style='background:#0f1b2d;color:#fff;padding:14px 18px;border-radius:9px 9px 0 0'>"
            f"<div style='font-size:13px'>E-TICKET</div><div style='font-size:24px'>{b['booking_ref']}</div></div>"
            f"<table>{cells}</table><p style='padding:0 14px;color:#555'>Have a safe flight!</p></div>")


def deliver(to: str, subject: str, text: str, html: str) -> dict:
    """Send the email for real if Gmail is set up; otherwise (or on failure) save it to the outbox folder."""
    user = os.getenv("GMAIL_ADDRESS", "").strip()
    password = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")   # Google shows it with spaces

    msg = EmailMessage()
    msg["From"] = user or "tickets@flightdesk.local"
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    note = ""
    if user and password:
        host, port = os.getenv("SMTP_HOST", "smtp.gmail.com"), int(os.getenv("SMTP_PORT", "465"))
        try:
            if port == 465:
                server = smtplib.SMTP_SSL(host, port, timeout=20)
            else:
                server = smtplib.SMTP(host, port, timeout=20)
                if server.has_extn("starttls"):
                    server.starttls()
            with server:
                server.login(user, password)
                server.send_message(msg)
            return {"delivered": True, "method": "email", "sent_to": to}
        except Exception as error:                                  # blocked network, wrong password, ...
            note = f"Real email failed ({type(error).__name__}: {error}). "

    outbox = ROOT / "outbox"
    outbox.mkdir(exist_ok=True)
    path = outbox / f"{datetime.now():%Y%m%d_%H%M%S}_{to}.eml"
    path.write_bytes(bytes(msg))
    return {"delivered": True, "method": "saved_to_file", "file": str(path),
            "note": note + "Ticket saved in the outbox folder instead of being emailed."}


# --------------------------------------------------------------------------
#  Tools
# --------------------------------------------------------------------------
@mcp.tool()
def create_booking(passenger_name: str, email: str, flight_id: int, payment_ref: str) -> dict:
    """Create a booking AFTER the payment succeeded. Needs the passenger name, email, flight id and payment reference."""
    payment = query("SELECT status, amount FROM payments WHERE payment_ref = ?", (payment_ref,))
    if not payment or payment[0]["status"] != "SUCCESS":
        return {"ok": False, "error": "This payment does not exist or was not successful. No booking made."}
    if query("SELECT 1 FROM bookings WHERE payment_ref = ? AND status = 'CONFIRMED'", (payment_ref,)):
        return {"ok": False, "error": "This payment was already used for a booking."}

    flight = query("SELECT price, seats_available FROM flights WHERE id = ?", (flight_id,))
    if not flight:
        return {"ok": False, "error": f"No flight with id {flight_id}."}
    if flight[0]["seats_available"] < 1:
        return {"ok": False, "error": "No seats left on this flight."}
    if abs(flight[0]["price"] - payment[0]["amount"]) > 0.01:
        return {"ok": False, "error": "The amount paid does not match the fare."}

    ref = "BK" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    execute("UPDATE flights SET seats_available = seats_available - 1 WHERE id = ?", (flight_id,))
    execute(
        "INSERT INTO bookings (booking_ref, passenger_name, email, flight_id, payment_ref, status, created_at) VALUES (?,?,?,?,?,'CONFIRMED',?)",
        (ref, passenger_name, email, flight_id, payment_ref, datetime.now().isoformat(timespec="seconds")),
    )
    return {"ok": True, "booking_ref": ref, "message": "Booking confirmed. Now send the ticket email."}


@mcp.tool()
def send_ticket_email(booking_ref: str) -> dict:
    """E-mail the ticket for a confirmed booking to the passenger."""
    booking = one_booking(booking_ref)
    if not booking:
        return {"ok": False, "error": f"No booking {booking_ref}."}
    if booking["status"] != "CONFIRMED":
        return {"ok": False, "error": f"Booking is {booking['status']}; no ticket to send."}
    result = deliver(booking["email"], f"Your e-ticket {booking['booking_ref']}: {booking['origin']} to {booking['destination']}",
                     ticket_text(booking), ticket_html(booking))
    return {"ok": True, **result}


@mcp.tool()
def my_bookings(email: str) -> list[dict]:
    """Show the booking history of a customer, newest first. Needs the customer's email."""
    return query(
        "SELECT b.booking_ref, b.passenger_name, b.status, f.flight_no, f.origin, f.destination, f.depart_date, f.price "
        "FROM bookings b JOIN flights f ON f.id = b.flight_id WHERE lower(b.email) = lower(?) ORDER BY b.id DESC",
        (email,),
    )


@mcp.tool()
def cancel_booking(booking_ref: str) -> dict:
    """Cancel a confirmed booking and give the seat back. Tell the user that the payment still needs a refund."""
    booking = one_booking(booking_ref)
    if not booking:
        return {"ok": False, "error": f"No booking {booking_ref}."}
    if booking["status"] != "CONFIRMED":
        return {"ok": False, "error": f"Booking is already {booking['status']}."}
    execute("UPDATE bookings SET status = 'CANCELLED' WHERE booking_ref = ?", (booking["booking_ref"],))
    execute("UPDATE flights SET seats_available = seats_available + 1 WHERE id = ?", (booking["flight_id"],))
    return {"ok": True, "booking_ref": booking["booking_ref"], "payment_ref": booking["payment_ref"],
            "message": "Booking cancelled. The payment agent should now refund this payment_ref."}


# --------------------------------------------------------------------------
#  Resources
# --------------------------------------------------------------------------
@mcp.resource("booking://{booking_ref}")
def booking_ticket(booking_ref: str) -> str:
    """The e-ticket text of one booking."""
    booking = one_booking(booking_ref)
    return ticket_text(booking) if booking else f"No booking {booking_ref}"


@mcp.resource("policy://cancellation")
def cancellation_policy() -> str:
    """Our cancellation policy."""
    return "Free cancellation up to 24 hours before departure. The fare is refunded to the original card."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")