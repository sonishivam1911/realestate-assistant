from langchain_community.tools import DuckDuckGoSearchRun
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
import time

class DuckDuckGoSearcher:
    def __init__(self, max_results_per_query: int = 10):
        self.max_results = max_results_per_query
        self.search_tool = DuckDuckGoSearchRun()
    
    def search_single_query(self, query: str) -> List[Dict]:
        """Execute a single DuckDuckGo search using LangChain"""
        try:
            print(f"  🔍 Searching: {query[:50]}...")
            result = self.search_tool.run(query)
            print(f"  ✓ Results:\n{result[:200]}...\n")
            return result if result else []
        except Exception as e:
            print(f"  ✗ Error searching '{query}': {e}")
            return []
    
    def search_parallel(self, queries: List[str]) -> Dict[str, str]:
        """Execute multiple searches in parallel"""
        results = {}
        
        # Use ThreadPoolExecutor for parallel execution
        with ThreadPoolExecutor(max_workers=min(len(queries), 5)) as executor:
            future_to_query = {
                executor.submit(self.search_single_query, query): query 
                for query in queries
            }
            
            for future in future_to_query:
                query = future_to_query[future]
                try:
                    results[query] = future.result()
                except Exception as e:
                    print(f"✗ Failed search '{query}': {e}")
                    results[query] = ""
        
        return results
    
    def get_all_search_results(self, search_plan: dict) -> dict:
        """Main method to execute all searches from search plan"""
        queries = search_plan.get('search_queries', [])
        
        print(f"\n🔍 Starting {len(queries)} searches with DuckDuckGo...")
        start_time = time.time()
        
        results = self.search_parallel(queries)
        
        elapsed = time.time() - start_time
        total_results = sum(len(str(r)) for r in results.values())
        print(f"\n✓ Completed all searches in {elapsed:.2f}s")
        print(f"📊 Total data retrieved: {total_results} characters")
        
        return {
            "search_results": results,
            "metadata": {
                "total_queries": len(queries),
                "total_results": total_results,
                "elapsed_time": elapsed
            }
        }