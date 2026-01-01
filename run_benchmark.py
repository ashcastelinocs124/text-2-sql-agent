"""
Benchmark Runner - Executes multiple SQL queries from a file against the SQLAgent.
Uses sqlglot to parse multiple statements from a single file.
"""
import sqlglot
import sys
from run_evaluation_pipeline import run_evaluation_pipeline

def run_benchmark(filepath="complex_benchmarks.sql"):
    print(f"\n📂 Loading benchmark suite: {filepath}")
    
    with open(filepath, 'r') as f:
        sql_content = f.read()

    # Parse multiple statements using sqlglot
    try:
        expressions = sqlglot.parse(sql_content, read="postgres")
    except Exception as e:
        print(f"❌ Failed to parse SQL file: {e}")
        sys.exit(1)

    print(f"🔍 Found {len(expressions)} queries to execute.\n")
    
    results = []
    
    for i, expression in enumerate(expressions, 1):
        # Convert back to SQL string
        query = expression.sql(dialect="postgres")
        
        print(f"\n{'-'*80}")
        print(f"🧪 BENCHMARK QUERY #{i}")
        print(f"{'-'*80}")
        print(f"SQL: {query[:100]}..." if len(query) > 100 else f"SQL: {query}")
        
        # Run pipeline
        # Note: We don't have expected results for these dynamic queries in this simple test,
        # so correctness will be based on self-validation (syntax/execution success).
        result = run_evaluation_pipeline(
            sql=query,
            database_url="postgresql://testuser:testpass@localhost:5432/testdb"
        )
        
        results.append({
            "id": i,
            "query": query,
            "score": result['scores']['overall'],
            "status": result['execution_result']['success']
        })

    # Final Report
    print(f"\n{'='*80}")
    print("🏁 BENCHMARK SUMMARY")
    print(f"{'='*80}")
    
    avg_score = sum(r['score'] for r in results) / len(results) if results else 0
    success_count = sum(1 for r in results if r['status'])
    
    print(f"Total Queries: {len(results)}")
    print(f"Successful:    {success_count}")
    print(f"Average Score: {avg_score:.2%}")
    print("-" * 40)
    
    for r in results:
        status_icon = "✅" if r['status'] else "❌"
        print(f"{status_icon} Query #{r['id']}: Score {r['score']:.2%}")

if __name__ == "__main__":
    run_benchmark()
