import sys
import unittest
from models import PlanType
from planning.factory import PlanningFactory

# Mock dependencies
class MockLLM:
    pass

class MockRAG:
    pass

class TestArchitecture(unittest.TestCase):
    def test_factory_instantiation(self):
        llm = MockLLM()
        rag = MockRAG()
        
        # Test Daily Strategy
        strategy = PlanningFactory.get_strategy(PlanType.DAILY, llm, rag)
        self.assertEqual(strategy.__class__.__name__, "DailyStrategy")
        
        # Test Weekly Strategy
        strategy = PlanningFactory.get_strategy(PlanType.WEEKLY, llm, rag)
        self.assertEqual(strategy.__class__.__name__, "WeeklyStrategy")
        
        # Test Monthly Strategy
        strategy = PlanningFactory.get_strategy(PlanType.MONTHLY, llm, rag)
        self.assertEqual(strategy.__class__.__name__, "MonthlyStrategy")
        
        # Test Finance Strategy
        strategy = PlanningFactory.get_strategy(PlanType.FINANCE, llm, rag)
        self.assertEqual(strategy.__class__.__name__, "FinanceStrategy")
        
        print("SUCCESS: Architecture smoke test passed.")

if __name__ == "__main__":
    unittest.main()
