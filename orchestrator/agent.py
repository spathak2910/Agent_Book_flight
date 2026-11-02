import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.models import LiteLlm
from google.adk.tools.agent_tool import AgentTool
from datetime import date
from common.model import get_model

load_dotenv()
model=get_model()

flight=RemoteA2aAgent(
    name="flight_agent",
    description="Searches flights between indian cities and show fares, times and price",
    agent_card="http://localhost:9001/.well-known/agent-card.json"
)

# hotel=RemoteA2aAgent(
#     name="hotel_agent",
#     description="Find hotel to stay in a city",
#     agent_card="http://localhost:8011/.well-known/agent-card.json"
# )

booking=RemoteA2aAgent(
    name="booking_agent",
    description="Create bookings, email e-ticket, show booking history and cancel bookings ",
    agent_card="http://localhost:9002/.well-known/agent-card.json"
)

payment=RemoteA2aAgent(
    name="payment_agent",
    description="Take simulated card payments and refunds, needs amount , last 4 digits of card number and payer name",
    agent_card="http://localhost:9003/.well-known/agent-card.json"
)

root_agent=LlmAgent(
    name="orchestrator_agent",
    model=model,
    description="Flight booking desk: search flight, make payments, email the tickets and show history",
    instruction=f"""Today is {date.today().isoformat()}. 
                You are flight booking desk and talk to the customer.\n
                You have one agent: flight_agent, when you call one, put all details it needs 
                in your message (ids, amount,names, emails, references).
                "When you call one, put all details it needs in your message (ids, amount,names, emails, references)."
                To book a flight follow these steps:\n
                1. Ask flight agent for options and show them to customers, let the customer choose
                2. Ask for passenger name, email and last 4 digit of card(never the)
                3. Say the fare and ask Shall i charge Rs X to the card ending NNNN? (YES/NO). Never charge before clear yes
                4. After Yes: call payment agent , if it is not success, tell the customer and stop. do not book.
                5. If Success call booking agent with passenger name, email, flight id and booking reference
                History: for 'my bookings' ask for email address and call booking agent
                Cancel: call booking agent to cancel, then payment agent to refund the payment and return the payment_ref
                Keep answers short and friendly.""",
    tools=[
        AgentTool(flight),
        AgentTool(booking),
        AgentTool(payment)
    ]
)