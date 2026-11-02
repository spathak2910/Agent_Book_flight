from datetime import date
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams

from common.model import get_model

tools = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8002/mcp"
    )
)
root_agent = LlmAgent(
    name="booking_agent",
    model=get_model(),
    description="Create Booking, Email E-Tickets, show booking history and cancel bookings",
    instruction=(
        f"Today is {date.today().isoformat()},"
        "You are the booking agent. To book you need passenger name, email, flight id and successful payment_ref"
        "After Create_booking succeeds, call send ticket email for that booking reference,"
        "For history use my_booking with customer email."
        "To cancel use cancel_booking"
        "Always report booking_ref values and status exactly as tool return them"
    ),
    tools = [tools]
)