import os
from dotenv import load_dotenv
from google.adk.models import LiteLlm

def get_model():
    return LiteLlm(model="us.anthropic.claude-haiku-4-5-20251001-v1:0",aws_region_name="us-east-1")