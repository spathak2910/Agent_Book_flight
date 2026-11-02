#python -m flight_agent.server
 
import uvicorn
from google.adk.a2a.utils.agent_to_a2a import to_a2a
# from a2a.flight_agent.agent import root_agent 
from .agent import root_agent 

PORT = 9002

a2a_app= to_a2a(root_agent, host="localhost", port=PORT)

if __name__=="__main__":
    uvicorn.run(a2a_app, host="127.0.0.1", port=PORT)