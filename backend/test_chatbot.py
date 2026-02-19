#!/usr/bin/env python3
"""
Test chatbot functionality directly
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from sqlmodel import Session, create_engine
from config import settings
from ai_orchestrator import AIOrchestrator
from agents.chatbot_agent import ChatbotAgent

async def test_chatbot():
    """Test chatbot directly"""
    print("=" * 60)
    print("Chatbot Functionality Test")
    print("=" * 60)
    
    print(f"\nConfiguration:")
    print(f"  Model: {settings.AI_MODEL}")
    print(f"  Base URL: {settings.OPENAI_BASE_URL}")
    
    # Create a database session
    engine = create_engine(settings.DATABASE_URL)
    
    with Session(engine) as session:
        orchestrator = AIOrchestrator(session)
        
        # Assemble context for user_id=1
        context = orchestrator.assemble_payload(1, "Hello, how can you help me?")
        
        print(f"\n✓ Context assembled")
        print(f"  Profile keys: {list(context.get('profile', {}).keys())}")
        print(f"  Stats count: {len(context.get('stats', []))}")
        print(f"  Patterns count: {len(context.get('patterns', []))}")
        
        # Initialize chatbot
        agent = ChatbotAgent(context, rag_manager=orchestrator.rag_manager)
        print(f"\n✓ Chatbot agent initialized")
        
        # Test message
        test_message = "Hello! Can you help me plan my day for maximum productivity?"
        print(f"\nSending test message: '{test_message}'")
        
        try:
            response = await agent.send_message(1, test_message)
            
            print(f"\n✅ SUCCESS!")
            print(f"\n  Reply: {response.get('reply', 'N/A')[:200]}...")
            print(f"  Actions: {len(response.get('actions', []))}")
            print(f"  Questions: {len(response.get('clarification_questions', []))}")
            
            if response.get('clarification_questions'):
                print(f"\n  Clarification Questions:")
                for q in response['clarification_questions']:
                    print(f"    - {q}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ FAILED!")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("\n🤖 Chatbot Direct Test\n")
    success = asyncio.run(test_chatbot())
    
    print("\n" + "=" * 60)
    if success:
        print("✅ CHATBOT IS WORKING!")
    else:
        print("❌ CHATBOT FAILED")
    print("=" * 60 + "\n")
