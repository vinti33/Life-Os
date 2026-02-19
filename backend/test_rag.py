from rag.manager import RAGManager
import json

def test_rag():
    print("--- RAG Local Test ---")
    manager = RAGManager(
        data_path="rag/data.json",
        index_path="rag/data.index",
        texts_path="rag/texts.json"
    )
    
    # Rebuild index to be sure
    manager.rebuild_index()
    
    # Test query
    question = "I spent too much money this month"
    print(f"\nQuestion: {question}")
    
    context = manager.query(question)
    print(f"Retrieved Rule: {context}")
    
    if "discretionary spending" in context.lower():
        print("\n✅ SUCCESS: The RAG retrieved the correct spending rule!")
    else:
        print("\n❌ FAILURE: Could not retrieve the correct rule.")

if __name__ == "__main__":
    test_rag()
