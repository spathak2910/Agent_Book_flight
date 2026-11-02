import os
from google.adk.agents import LlmAgent
from google.adk.models import LiteLlm
from dotenv import load_dotenv
from common.model import get_model

load_dotenv()
model= get_model()

HOTEL= {
    "goa": "Sea Breeza Resort, Calangute - Rs 3200/night",
    "mumbai": "Marine View Inn, Colaba - Rs 4500/night"
}

def search_hotel(city:str)-> str:
    """Find hotel in a city available: goa and mumbai"""
    return HOTEL.get(city.lower(), f"No hotel fount in the {city}")

root_agent= LlmAgent(
    name="hotel_agent",
    model=model,
    description="Find hotel in a city",
    instruction="You are a hotel assistant, use search_hotel tool to find hotel",
    tools=[search_hotel]
)