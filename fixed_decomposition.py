#!/usr/bin/env python3
"""
Fixed Query Decomposition and Comparison
"""

import json
import re
from run_evaluation_pipeline import run_evaluation_pipeline

def decompose_query(query: str) -> list:
    """Simple decomposition of complex queries"""
    subqueries = []
    
    # Extract table names for sampling
    table_pattern = r'(?:FROM|JOIN)\s+(\w+)'
    tables = re.findall(table_pattern, query, re.IGNORECASE)
    unique_tables = list(set(tables))
    
    # Create sample queries for each table
    for i, table in enumerate(unique_tables[:3]):  # Limit to 3 tables
        subqueries.append({
            "sql": f"SELECT * FROM {table} LIMIT 5",
            "type": "table_sample",
            "description": f"Sample from {table}"
        })
    
    return subqueries

def compare_approaches(original_query: str, expected_results: list, query_id: str):
    """Compare original vs decomposed approaches"""
    print(f"\n🔍 Comparing: {query_id}")
    print("=" * 50)
    
    # Test original query
    print("1️⃣ ORIGINAL:")
    try:
        original_result = run_evaluation_pipeline(
            sql=original_query,
            database_url='postgresql://testuser:testpass@localhost:5432/testdb',
            expected_results=expected_results
        )
        original_score = original_result.get('scores', {}).get('overall', 0)
        original_time = original_result.get('execution', {}).get('execution_time_ms', 0)
        print(f"   Score: {original_score:.2%}, Time: {original_time:.2f}ms")
    except Exception as e:
        print(f"   ERROR: {e}")
        original_score = 0
        original_time = 0
    
    # Test decomposed queries
    print("\n2️⃣ DECOMPOSED:")
    subqueries = decompose_query(original_query)
    sub_scores = []
    sub_times = []
    
    for i, subq in enumerate(subqueries):
        print(f"   {i+1}. {subq['description']}")
        try:
            result = run_evaluation_pipeline(
                sql=subq['sql'],
                database_url='postgresql://testuser:testpass@localhost:5432/testdb',
                expected_results=[]
            )
            score = result.get('scores', {}).get('overall', 0)
            time = result.get('execution', {}).get('execution_time_ms', 0)
            sub_scores.append(score)
            sub_times.append(time)
            print(f"      Score: {score:.2%}, Time: {time:.2f}ms")
        except Exception as e:
            print(f"      ERROR: {e}")
            sub_scores.append(0)
            sub_times.append(0)
    
    # Calculate averages
    avg_sub_score = sum(sub_scores) / len(sub_scores) if sub_scores else 0
    total_sub_time = sum(sub_times)
    
    # Comparison
    print(f"\n📊 COMPARISON:")
    print(f"   Original: {original_score:.2%} ({original_time:.2f}ms)")
    print(f"   Decomposed: {avg_sub_score:.2%} ({total_sub_time:.2f}ms total)")
    
    if avg_sub_score > original_score * 1.1:
        print(f"   🏆 DECOMPOSED wins by {((avg_sub_score/original_score - 1) * 100):.1f}%")
    elif original_score > avg_sub_score * 1.1:
        print(f"   🎯 ORIGINAL wins by {((original_score/avg_sub_score - 1) * 100):.1f}%")
    else:
        print(f"   🤝 Approaches are comparable")
    
    return {
        "query_id": query_id,
        "original_score": original_score,
        "original_time": original_time,
        "decomposed_score": avg_sub_score,
        "decomposed_time": total_sub_time,
        "subquery_count": len(subqueries)
    }

def main():
    """Run comparison on complex queries"""
    
    # Load gold queries
    with open('gold_queries.json', 'r') as f:
        gold_queries = json.load(f)
    
    # Filter for complex queries
    complex_queries = [q for q in gold_queries if q['difficulty'] in ['hard', 'enterprise']]
    
    print("🚀 QUERY DECOMPOSITION COMPARISON")
    print("=" * 60)
    print(f"Testing {len(complex_queries)} complex queries...")
    
    results = []
    
    for query in complex_queries[:3]:  # Test first 3
        result = compare_approaches(
            query['gold_sql'],
            query['expected_result'],
            query['id']
        )
        results.append(result)
        print("-" * 60)
    
    # Overall analysis
    print("\n🎯 OVERALL ANALYSIS")
    print("=" * 60)
    
    if results:
        avg_original = sum(r['original_score'] for r in results) / len(results)
        avg_decomposed = sum(r['decomposed_score'] for r in results) / len(results)
        
        print(f"Average Original Score: {avg_original:.2%}")
        print(f"Average Decomposed Score: {avg_decomposed:.2%}")
        
        if avg_decomposed > avg_original:
            print("🏆 DECOMPOSITION approach wins overall")
        else:
            print("🎯 ORIGINAL approach wins overall")
        
        # Save results
        with open('decomposition_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: decomposition_results.json")

if __name__ == "__main__":
    main()