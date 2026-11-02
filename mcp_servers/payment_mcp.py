"""MCP server 2 - PAYMENTS (port 8002). Used only by the Payment Agent.
A SIMULATED payment gateway: no real money moves.   Run:  python -m mcp_servers.payments_mcp

Test cards (last 4 digits):   0000 -> declined      anything else -> success
"""
import random
import string
from datetime import datetime

from mcp.server.fastmcp import FastMCP

from common.db import execute, query

mcp = FastMCP("payments", host="127.0.0.1", port=8003)


def new_ref() -> str:
    return "PAY" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


@mcp.tool()
def charge_card(amount: float, card_last4: str, payer_name: str) -> dict:
    """Charge a card (simulated). Needs the amount in Rs, the last 4 digits of the card, and the payer's name."""
    if len(card_last4) != 4 or not card_last4.isdigit():
        return {"status": "DECLINED", "message": "Card last 4 digits must be exactly 4 numbers."}

    if card_last4 == "0000":
        status, message = "DECLINED", "Card declined: insufficient funds."
    elif amount <= 0 or amount > 200000:
        status, message = "DECLINED", "Amount is outside the allowed limit."
    else:
        status, message = "SUCCESS", "Payment approved."

    ref = new_ref()
    execute(
        "INSERT INTO payments (payment_ref, payer_name, card_last4, amount, status, message, created_at) VALUES (?,?,?,?,?,?,?)",
        (ref, payer_name, card_last4, amount, status, message, datetime.now().isoformat(timespec="seconds")),
    )
    return {"payment_ref": ref, "status": status, "amount": amount, "message": message}


@mcp.tool()
def get_payment(payment_ref: str) -> dict:
    """Look up a payment by its reference."""
    rows = query("SELECT payment_ref, payer_name, card_last4, amount, status, message, created_at FROM payments WHERE payment_ref = ?", (payment_ref,))
    return rows[0] if rows else {"error": f"No payment {payment_ref}"}


@mcp.tool()
def refund_payment(payment_ref: str) -> dict:
    """Refund a successful payment (simulated)."""
    rows = query("SELECT status FROM payments WHERE payment_ref = ?", (payment_ref,))
    if not rows:
        return {"error": f"No payment {payment_ref}"}
    if rows[0]["status"] != "SUCCESS":
        return {"error": f"Only SUCCESS payments can be refunded (this one is {rows[0]['status']})."}
    execute("UPDATE payments SET status = 'REFUNDED' WHERE payment_ref = ?", (payment_ref,))
    return {"payment_ref": payment_ref, "status": "REFUNDED"}


@mcp.resource("payments://test-cards")
def test_cards() -> str:
    """How to test the simulated gateway."""
    return "Card last 4 = 0000 -> declined (insufficient funds)\nAny other 4 digits -> approved\nAmounts above Rs 2,00,000 are declined."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
