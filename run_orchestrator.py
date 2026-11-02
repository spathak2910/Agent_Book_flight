import asyncio
import sys
from google.adk.runners import InMemoryRunner
from google.genai import types
from orchestrator.agent import root_agent


async def main():
    runner=InMemoryRunner(agent=root_agent, app_name="flight_desk")
    session =await runner.session_service.create_session(app_name="flight_desk", user_id="u1")
    
    print("Flight Booking assistant")


    while True:
        text = input("\nYou : " )
        msg= types.Content(role="user", parts=[types.Part(text=text)])
        async for event in runner.run_async(user_id="u1",session_id=session.id,new_message=msg):
            if event.get_function_calls():
                for call in event.get_function_calls():
                    print(f"[Calling Agent: ] {call.name}")

            if event.is_final_response() and event.content and event.content.parts:
                print("\nOrchestrator: ", event.content.parts[0].text)


if __name__=="__main__":
    asyncio.run(main())