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

tools=MCPToolset(connection_params=StreamableHTTPConnectionParams( url="http://localhost:8001/mcp"))
# FLIGHTS= {
#     "goa": "6E-101 Delhi -> Goa 09:00, Rs 5400",
#     "mumbai": "AI-202 Delhi -> Mumbai 07:30, Rs 4100"
# }

# def search_flight(city:str)-> str:
#     """Find flight from delhi to cities available: goa and mumbai"""
#     return FLIGHTS.get(city.lower(), f"No flights fount to the {city}")

root_agent= LlmAgent(
    name="flight_agent",
    model=model,
    description="Searches flights between indian cities and show fares, times and price",
    instruction=(
        f"Today is {date.today().isoformat()}"
        "You are the flight search agent. use the tools to find the flights"
        "Never invent flights, show each options with its flight id, airline, flight number, date, times, price and seat left"
        "If the user gives no date, search without date"
    ),
    tools=[tools]
)