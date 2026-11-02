import uvicorn
from google.adk.a2a.utils.agent_to_a2a import to_a2a

from agent import root_agent 

a2a_app= to_a2a(root_agent, host="localhost", port=8011)

if __name__=="__main__":
    uvicorn.run(a2a_app, host="127.0.0.1", port=8011)