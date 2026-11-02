import os
from google.adk.agents import LlmAgent
from google.adk.models import LiteLlm
from dotenv import load_dotenv
from datetime import date
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

from common.model import get_model
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset

load_dotenv()
model= get_model()

tools=MCPToolset(connection_params=StreamableHTTPConnectionParams( url="http://localhost:8003/mcp"))
# FLIGHTS= {
#     "goa": "6E-101 Delhi -> Goa 09:00, Rs 5400",
#     "mumbai": "AI-202 Delhi -> Mumbai 07:30, Rs 4100"
# }

# def search_flight(city:str)-> str:
#     """Find flight from delhi to cities available: goa and mumbai"""
#     return FLIGHTS.get(city.lower(), f"No flights fount to the {city}")

root_agent= LlmAgent(
    name="payment_agent",
    model=model,
    description="Take simulated and card payments and refunds. needs",
    instruction=(
        f"Today is {date.today().isoformat()}"
        "You are the payment agent for a SIMULATED payment gateway"
        "To make payment you need the amount, the last 4 digits of the card and payer name; ask if any one is missing"
        "Never ask for full card number, Report the payment_ref and the status exactly as tool returns them"
    ),
    tools=[tools]
)