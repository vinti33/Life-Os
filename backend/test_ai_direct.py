#!/usr/bin/env python3
"""
Simple direct test of the AI orchestrator without authentication.
This tests the core AI functionality directly.
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from sqlmodel import Session, create_engine
from config import settings
from ai_orchestrator import AIOrchestrator

async def test_ai_directly():
    """Test AI orchestrator directly"""
    print("=" * 60)
    print("Direct AI Orchestrator Test")
    print("=" * 60)
    
    print(f"\nConfiguration:")
    print(f"  Model: {settings.AI_MODEL}")
    print(f"  Base URL: {settings.OPENAI_BASE_URL}")
    print(f"  API Key: {settings.OPENAI_API_KEY[:10]}...")
    
    # Create a database session
    engine = create_engine(settings.DATABASE_URL)
    
    with Session(engine) as session:
        orchestrator = AIOrchestrator(session)
        
        print(f"\n✓ AIOrchestrator initialized")
        print(f"✓ RAG Manager: {orchestrator.rag_manager is not None}")
        print(f"✓ Planner Agent: {orchestrator.planner is not None}")
        print(f"✓ Review Agent: {orchestrator.reviewer is not None}")
        
        # Test with a mock user ID (1)
        print(f"\nTesting plan generation for user_id=1...")
        try:
            plan, questions = await orchestrator.generate_plan_draft(
                user_id=1,
                context="Plan my day for maximum productivity"
            )
            
            print(f"\n✅ SUCCESS!")
            print(f"  Plan ID: {plan.id}")
            print(f"  Summary: {plan.summary}")
            print(f"  Status: {plan.status}")
            print(f"  Clarification Questions: {len(questions)}")
            
            if questions:
                print(f"\n  Questions:")
                for q in questions:
                    print(f"    - {q}")
            
            # Get tasks
            session.refresh(plan)
            print(f"\n  Tasks Generated: {len(plan.tasks)}")
            for i, task in enumerate(plan.tasks[:5], 1):
                print(f"    {i}. {task.title} ({task.category})")
            
            return True
            
        except Exception as e:
            print(f"\n❌ FAILED!")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("\n🤖 Direct AI Test (No Authentication)\n")
    success = asyncio.run(test_ai_directly())
    
    print("\n" + "=" * 60)
    if success:
        print("✅ AI PLAN FORMATION IS WORKING!")
    else:
        print("❌ AI PLAN FORMATION FAILED")
    print("=" * 60 + "\n")
