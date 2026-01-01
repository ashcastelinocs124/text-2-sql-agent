#!/usr/bin/env python3
"""
Query Decomposition and Comparison System
Breaks complex queries into sub-queries and compares performance
"""

import json
import re
from typing import List, Dict, Any, Optional
from run_evaluation_pipeline import run_evaluation_pipeline

class QueryDecomposer:
    """Decomposes complex SQL queries into simpler sub-queries"""
    
    def decompose_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Decompose a complex query into sub-queries
        
        Args:
            query: Complex SQL query
            
        Returns:
            List of sub-query dictionaries with metadata
        """
        subqueries = []
        
        # Strategy 1: Extract CTEs
        if 'WITH' in query.upper():
            cte_subqueries = self._extract_cte_subqueries(query)
            subqueries.extend(cte_subqueries)
        
        # Strategy 2: Extract sub-queries from FROM/WHERE clauses
        from_subqueries = self._extract_from_subqueries(query)
        subqueries.extend(from_subqueries)
        
        # Strategy 3: For JOIN queries, extract individual table queries
        if 'JOIN' in query.upper():
            table_queries = self._extract_table_queries(query)
            subqueries.extend(table_queries)
        
        # Always include the original query
        subqueries.append({
            "sql": query,
            "type": "original",
            "order": len(subqueries),
            "description": "Original complex query"
        })
        
        return subqueries
    
    def _extract_cte_subqueries(self, query: str) -> List[Dict[str, Any]]:
        """Extract CTE definitions as separate queries"""
        subqueries = []
        
        # Find WITH clause and extract CTEs
        with_match = re.search(r'WITH\s+(.+?)\s+SELECT', query, re.IGNORECASE | re.DOTALL)
        if with_match:
            with_clause = with_match.group(1)
            
            # Split CTEs by comma (but not within parentheses)
            ctes = self._split_ctes(with_clause)
            
            for i, cte in enumerate(ctes):
                # Extract the SELECT part of the CTE
                cte_select_match = re.search(r'(\w+)\s+AS\s*\((.+)\)', cte, re.IGNORECASE | re.DOTALL)
                if cte_select_match:
                    cte_name = cte_select_match.group(1)
                    cte_query = cte_select_match.group(2)
                    
                    subqueries.append({
                        "sql": f"SELECT * FROM ({cte_query}) AS {cte_name} LIMIT 10",
                        "type": "cte",
                        "order": i,
                        "description": f"CTE: {cte_name}"
                    })
        
        return subqueries
    
    def _split_ctes(self, with_clause: str) -> List[str]:
        """Split CTE definitions by comma, respecting parentheses"""
        ctes = []
        current_cte = ""
        paren_count = 0
        in_paren = False
        
        for char in with_clause:
            if char == '(':
                paren_count += 1
                in_paren = True
            elif char == ')':
                paren_count -= 1
                if paren_count == 0:
                    in_paren = False
            
            current_cte += char
            
            if char == ',' and not in_paren:
                ctes.append(current_cte.strip())
                current_cte = ""
        
        if current_cte.strip():
            ctes.append(current_cte.strip())
        
        return ctes
    
    def _extract_from_subqueries(self, query: str) -> List[Dict[str, Any]]:
        """Extract sub-queries from FROM clause"""
        subqueries = []
        
        # Find sub-queries in FROM clause
        from_pattern = r'FROM\s*\(\s*(SELECT\s+.+?)\)\s*(?:AS\s+\w+)?'
        matches = re.findall(from_pattern, query, re.IGNORECASE | re.DOTALL)
        
        for i, subq in enumerate(matches):
            subqueries.append({
                "sql": subq + " LIMIT 10",
                "type": "from_subquery",
                "order": i,
                "description": f"FROM subquery {i+1}"
            })
        
        return subqueries
    
    def _extract_table_queries(self, query: str) -> List[Dict[str, Any]]:
        """Extract individual table queries from JOINs"""
        subqueries = []
        
        # Find table names in FROM and JOIN clauses
        table_pattern = r'(?:FROM|JOIN)\s+(\w+)'
        matches = re.findall(table_pattern, query, re.IGNORECASE)
        
        # Remove duplicates and create sample queries
        unique_tables = list(set(matches))
        for i, table in enumerate(unique_tables):
            subqueries.append({
                "sql": f"SELECT * FROM {table} LIMIT 5",
                "type": "table_sample",
                "order": i,
                "description": f"Sample from {table}"
            })
        
        return subqueries

class QueryComparison:
    """Compare performance of original vs decomposed queries"""
    
    def __init__(self):
        self.decomposer = QueryDecomposer()
    
    def compare_query_approaches(self, original_query: str, expected_results: List[Dict], 
                                query_id: str = "test") -> Dict[str, Any]:
        """
        Compare original query vs decomposed sub-queries
        
        Args:
            original_query: Complex SQL query
            expected_results: Expected output for comparison
            query_id: Identifier for the query
            
        Returns:
            Comparison results with performance metrics
        """
        print(f"\n🔍 Comparing Query Approaches: {query_id}")
        print("=" * 60)
        
        # 1. Evaluate original query
        print("1️⃣  Evaluating ORIGINAL complex query...")
        original_result = self._evaluate_single_query(
            original_query, expected_results, f"{query_id}_original"
        )
        
        # 2. Decompose and evaluate sub-queries
        print("\n2️⃣  Decomposing into SUB-QUERIES...")
        subqueries = self.decomposer.decompose_query(original_query)
        
        subquery_results = []
        total_time = 0
        
        for i, subq in enumerate(subqueries):
            if subq['type'] == 'original':
                continue  # Skip the original, we already evaluated it
                
            print(f"   {i+1}. Evaluating: {subq['description']}")
            
            # For sub-queries, we don't always have expected results
            sub_expected = expected_results if subq['type'] in ['cte', 'from_subquery'] else None
            
            result = self._evaluate_single_query(
                subq['sql'], sub_expected or [], f"{query_id}_sub_{i}"
            )
            
            subquery_results.append(result)
            total_time += result['execution']['execution_time_ms']
        
        # 3. Compare approaches
        comparison = self._compare_approaches(
            original_result, subquery_results
        )
        
        return {
            "query_id": query_id,
            "original_query": original_query,
            "original_result": original_result,
            "subqueries": subqueries,
            "subquery_results": subquery_results,
            "comparison": comparison
        }
    
    def _evaluate_single_query(self, sql: str, expected_results: List[Dict], 
                              query_id: str) -> Dict[str, Any]:
        """Evaluate a single query using the pipeline"""
        try:
            return run_evaluation_pipeline(
                sql=sql,
                database_url='postgresql://testuser:testpass@localhost:5432/testdb',
                expected_results=expected_results
            )
        except Exception as e:
            return {
                "query_id": query_id,
                "execution": {
                    "success": False,
                    "error": str(e),
                    "execution_time_ms": 0,
                    "rows_returned": 0
                },
                "scores": {
                    "overall": 0.0,
                    "dimensions": {
                        "correctness": 0.0,
                        "efficiency": 0.0,
                        "safety": 0.0,
                        "result_completeness": 0.0
                    }
                }
            }
    
    def _compare_approaches(self, original_result: Dict, subquery_results: List[Dict]) -> Dict[str, Any]:
        """Compare different query approaches"""
        
        if not subquery_results:
            return {
                "winner": "original",
                "scores": {"original": original_result['scores']['overall'], "subqueries_avg": 0.0},
                "performance": {"original_time": original_result['execution']['execution_time_ms'], "subqueries_total_time": 0},
                "success_rates": {"original": 1.0 if original_result['execution']['success'] else 0.0, "subqueries": 0.0},
                "analysis": "No sub-queries to compare"
            }
        
        comparison = {
            "winner": "original",
            "scores": {
                "original": original_result['scores']['overall'],
                "subqueries_avg": sum(r['scores']['overall'] for r in subquery_results) / len(subquery_results)
            },
            "performance": {
                "original_time": original_result['execution']['execution_time_ms'],
                "subqueries_total_time": sum(r['execution']['execution_time_ms'] for r in subquery_results)
            },
            "success_rates": {
                "original": 1.0 if original_result['execution']['success'] else 0.0,
                "subqueries": sum(1 for r in subquery_results if r['execution']['success']) / len(subquery_results)
            },
            "analysis": ""
        }
        
        # Determine winner
        scores = comparison['scores']
        if scores['subqueries_avg'] > scores['original']:
            comparison['winner'] = "subqueries"
        
        # Generate analysis
        winner_score = scores[comparison['winner']]
        original_score = scores['original']
        
        if winner_score > original_score * 1.1:  # 10% improvement
            comparison['analysis'] = f"🏆 {comparison['winner'].title()} approach wins by {((winner_score/original_score - 1) * 100):.1f}%"
        elif winner_score < original_score * 0.9:  # 10% degradation
            comparison['analysis'] = f"⚠️  Original approach better by {((original_score/winner_score - 1) * 100):.1f}%"
        else:
            comparison['analysis'] = f"🤝 Approaches are comparable ({abs(winner_score - original_score):.1%} difference)"
        
        return comparison

def main():
    """Run comparison on complex queries"""
    
    # Load gold queries
    with open('gold_queries.json', 'r') as f:
        gold_queries = json.load(f)
    
    # Filter for complex queries (hard + enterprise)
    complex_queries = [q for q in gold_queries if q['difficulty'] in ['hard', 'enterprise']]
    
    print("🚀 QUERY DECOMPOSITION COMPARISON")
    print("=" * 60)
    print(f"Testing {len(complex_queries)} complex queries...")
    
    comparison_results = []
    comparator = QueryComparison()
    
    for query in complex_queries[:3]:  # Test first 3 for demo
        result = comparator.compare_query_approaches(
            query['gold_sql'],
            query['expected_result'],
            query['id']
        )
        comparison_results.append(result)
        
        # Print summary
        print(f"\n📊 SUMMARY for {query['id']}:")
        print(f"   Original Score: {result['comparison']['scores']['original']:.2%}")
        print(f"   Sub-queries Avg: {result['comparison']['scores']['subqueries_avg']:.2%}")
        print(f"   Winner: {result['comparison']['winner'].upper()}")
        print(f"   {result['comparison']['analysis']}")
        print("-" * 60)
    
    # Overall analysis
    print("\n🎯 OVERALL ANALYSIS")
    print("=" * 60)
    
    winners = {"original": 0, "subqueries": 0}
    total_original = 0
    total_decomposed = 0
    
    for result in comparison_results:
        winners[result['comparison']['winner']] += 1
        total_original += result['comparison']['scores']['original']
        total_decomposed += result['comparison']['scores']['subqueries_avg']
    
    print(f"Winners by approach:")
    for approach, count in winners.items():
        print(f"  {approach.title()}: {count}/{len(comparison_results)} queries")
    
    print(f"\nAverage scores:")
    print(f"  Original: {total_original/len(comparison_results):.2%}")
    print(f"  Decomposed: {total_decomposed/len(comparison_results):.2%}")
    
    # Save results
    with open('query_decomposition_comparison.json', 'w') as f:
        json.dump(comparison_results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: query_decomposition_comparison.json")

if __name__ == "__main__":
    main()