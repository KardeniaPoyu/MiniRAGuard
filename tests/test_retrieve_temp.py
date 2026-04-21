import sys, os
sys.path.insert(0, os.path.abspath('backend'))
import sys
from pathlib import Path

# Add repo root to path
sys.path.append(str(Path(__file__).resolve().parent))

from test_rag_tool import _ensure_vector_store_exists, _import_retrieve_legal_context

def main():
    print("Ensuring vector store exists...")
    _ensure_vector_store_exists()
    
    print("Importing retrieve_legal_context...")
    retrieve_legal_context = _import_retrieve_legal_context()
    
    query = "租客若提前退租，押金概不退还，房东有权没收全部押金"
    print(f"Querying: {query}")
    
    result = retrieve_legal_context(query)
    
    Path("retrieve_result.txt").write_text(result, encoding="utf-8")
    print("Result saved to retrieve_result.txt")

if __name__ == "__main__":
    main()
