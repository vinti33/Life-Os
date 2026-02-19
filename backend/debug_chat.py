
import asyncio
import time
from agents.chatbot_agent import ChatbotAgent
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    message = "make the morning rutine and evening wind down more precise break in to small tasks"
    context = {"current_plan": [{"id": "1", "title": "Example Task"}]}
    agent = ChatbotAgent(context)

    print(f"Sending request: '{message}'...")
    start = time.time()
    try:
        response = await agent.send_message(user_id="benchmark", message=message)
        elapsed = time.time() - start
        print(f"SUCCESS: Response received in {elapsed:.2f}s")
        print(response)
        
        if "out of memory" in response.get("reply", "").lower():
            print("FAILURE: Still OOM")
        elif "trouble connecting" in response.get("reply", "").lower():
            print("FAILURE: Still connection trouble")
        else:
            print("VERIFIED: Request processed successfully.")
            
    except Exception as e:
        elapsed = time.time() - start
        print(f"FAILURE: Request failed after {elapsed:.2f}s: {e}")

if __name__ == "__main__":
    asyncio.run(main())
