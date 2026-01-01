"""
SQL Agent - Validates, executes, and summarizes SQL queries in a sandbox environment
"""
import sqlglot
from hallucination import HallucinationDetector
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import json
from datetime import datetime
from typing import Dict, Any, List, Optional


class SQLAgent:
    """
    Agent that validates SQL queries, executes them in a sandbox, and provides summaries
    """
    
    def __init__(self, database_url: str):
        """
        Initialize the SQL Agent
        
        Args:
            database_url: PostgreSQL connection string
        """
        self.database_url = database_url
        self.detector = HallucinationDetector()
        self.detector.schema_inspector = self.detector.schema_inspector.__class__(database_url)
        self.engine = create_engine(database_url)
        
    def validate_query(self, sql: str) -> Dict[str, Any]:
        """
        Validate SQL query for safety and correctness
        
        Returns:
            Dict with validation results
        """
        validation_result = {
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "query_type": None,
            "tables_accessed": [],
            "columns_accessed": []
        }
        
        try:
            # Parse the query to extract metadata
            parsed = sqlglot.parse_one(sql, read="postgres")
            
            # Determine query type
            query_type = type(parsed).__name__
            validation_result["query_type"] = query_type
            
            # Only allow SELECT statements
            if not isinstance(parsed, sqlglot.exp.Select):
                raise ValueError(f"Only SELECT queries are allowed. Got: {query_type}")
            
            # Extract tables
            tables = [t.name for t in parsed.find_all(sqlglot.exp.Table)]
            validation_result["tables_accessed"] = tables
            
            # Ensure at least one table is accessed
            if not tables:
                raise ValueError("Query must reference at least one table")
            
            # Extract columns
            columns = [c.name for c in parsed.find_all(sqlglot.exp.Column) if c.name != '*']
            validation_result["columns_accessed"] = columns
            
            # Run validation
            self.detector.validate_sql(sql)
            validation_result["is_valid"] = True
            
        except ValueError as e:
            validation_result["errors"].append(str(e))
        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
            
        return validation_result
    
    def execute_in_sandbox(self, sql: str, limit: int = 100) -> Dict[str, Any]:
        """
        Execute SQL query in sandbox environment with safety limits
        
        Args:
            sql: SQL query to execute
            limit: Maximum number of rows to return
            
        Returns:
            Dict with execution results
        """
        execution_result = {
            "success": False,
            "rows_returned": 0,
            "columns": [],
            "data": [],
            "execution_time_ms": 0,
            "error": None
        }
        
        try:
            # Add LIMIT to prevent large result sets
            limited_sql = self._add_limit(sql, limit)
            
            # Execute query with timing
            start_time = datetime.now()
            
            with self.engine.connect() as conn:
                result = conn.execute(text(limited_sql))
                
                # Fetch results
                if result.returns_rows:
                    execution_result["columns"] = list(result.keys())
                    execution_result["data"] = [dict(row._mapping) for row in result.fetchall()]
                    execution_result["rows_returned"] = len(execution_result["data"])
                else:
                    execution_result["rows_returned"] = result.rowcount
                
            end_time = datetime.now()
            execution_result["execution_time_ms"] = (end_time - start_time).total_seconds() * 1000
            execution_result["success"] = True
            
        except SQLAlchemyError as e:
            execution_result["error"] = f"Database error: {str(e)}"
        except Exception as e:
            execution_result["error"] = f"Execution error: {str(e)}"
            
        return execution_result
    
    def _add_limit(self, sql: str, limit: int) -> str:
        """Add LIMIT clause if not present"""
        try:
            # Parse the query to check for existing LIMIT
            parsed = sqlglot.parse_one(sql, read="postgres")
            
            # Check if LIMIT already exists
            existing_limit = parsed.find(sqlglot.exp.Limit)
            
            if existing_limit:
                # LIMIT already exists, return as-is
                return sql
            
            # No LIMIT found, add one
            sql = sql.rstrip(';').strip()
            return f"{sql} LIMIT {limit}"
            
        except Exception:
            # If parsing fails, use simple string check as fallback
            sql_lower = sql.lower().strip()
            if 'limit' in sql_lower:
                return sql
            sql = sql.rstrip(';').strip()
            return f"{sql} LIMIT {limit}"
    
    def analyze_results(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze query execution results
        
        Returns:
            Dict with analysis
        """
        analysis = {
            "summary": "",
            "insights": [],
            "data_preview": []
        }
        
        if not execution_result["success"]:
            analysis["summary"] = "Query execution failed"
            return analysis
        
        rows = execution_result["rows_returned"]
        cols = len(execution_result["columns"])
        time_ms = execution_result["execution_time_ms"]
        
        # Generate summary
        analysis["summary"] = f"Query returned {rows} row(s) with {cols} column(s) in {time_ms:.2f}ms"
        
        # Add insights
        if rows == 0:
            analysis["insights"].append("⚠️ Query returned no results")
        elif rows >= 100:
            analysis["insights"].append("⚠️ Results may be truncated (limit: 100 rows)")
        
        if time_ms > 1000:
            analysis["insights"].append("⚠️ Query took longer than 1 second to execute")
        elif time_ms < 10:
            analysis["insights"].append("✅ Query executed very quickly")
        
        # Data preview (first 5 rows)
        if execution_result["data"]:
            analysis["data_preview"] = execution_result["data"][:5]
            
            # Analyze data types
            if execution_result["data"]:
                first_row = execution_result["data"][0]
                for col, val in first_row.items():
                    if val is None:
                        analysis["insights"].append(f"Column '{col}' contains NULL values")
        
        return analysis
    
    def process_query(self, sql: str, verbose: bool = True) -> Dict[str, Any]:
        """
        Main agent workflow: validate -> execute -> analyze -> summarize
        
        Args:
            sql: SQL query to process
            verbose: Whether to print detailed output
            
        Returns:
            Complete results dictionary
        """
        result = {
            "query": sql,
            "timestamp": datetime.now().isoformat(),
            "validation": {},
            "execution": {},
            "analysis": {},
            "overall_status": "FAILED"
        }
        
        if verbose:
            print("=" * 80)
            print("🤖 SQL AGENT - Query Processing")
            print("=" * 80)
            print(f"\n📝 Query:\n{sql}\n")
        
        # Step 1: Validation
        if verbose:
            print("🔍 Step 1: Validating query...")
        
        validation = self.validate_query(sql)
        result["validation"] = validation
        
        if verbose:
            if validation["is_valid"]:
                print("✅ Validation PASSED")
                print(f"   - Query Type: {validation['query_type']}")
                print(f"   - Tables: {', '.join(validation['tables_accessed'])}")
                if validation['columns_accessed']:
                    print(f"   - Columns: {', '.join(validation['columns_accessed'][:5])}")
            else:
                print("❌ Validation FAILED")
                for error in validation["errors"]:
                    print(f"   - {error}")
                return result
        
        # Step 2: Execute in Sandbox
        if verbose:
            print("\n⚙️  Step 2: Executing in sandbox environment...")
        
        execution = self.execute_in_sandbox(sql)
        result["execution"] = execution
        
        if verbose:
            if execution["success"]:
                print(f"✅ Execution SUCCESSFUL")
                print(f"   - Rows returned: {execution['rows_returned']}")
                print(f"   - Execution time: {execution['execution_time_ms']:.2f}ms")
            else:
                print(f"❌ Execution FAILED")
                print(f"   - Error: {execution['error']}")
                return result
        
        # Step 3: Analyze Results
        if verbose:
            print("\n📊 Step 3: Analyzing results...")
        
        analysis = self.analyze_results(execution)
        result["analysis"] = analysis
        
        if verbose:
            print(f"✅ Analysis complete")
            print(f"   - {analysis['summary']}")
            if analysis['insights']:
                print("   - Insights:")
                for insight in analysis['insights']:
                    print(f"     {insight}")
        
        # Step 4: Summary
        result["overall_status"] = "SUCCESS"
        
        if verbose:
            print("\n" + "=" * 80)
            print("📋 SUMMARY")
            print("=" * 80)
            print(f"Status: ✅ {result['overall_status']}")
            print(f"Query Type: {validation['query_type']}")
            print(f"Results: {execution['rows_returned']} rows in {execution['execution_time_ms']:.2f}ms")
            
            if analysis['data_preview']:
                print(f"\n📄 Data Preview (first {len(analysis['data_preview'])} rows):")
                print("-" * 80)
                for i, row in enumerate(analysis['data_preview'], 1):
                    print(f"Row {i}: {row}")
            
            print("=" * 80)
        
        return result
    
    def save_report(self, result: Dict[str, Any], filename: str = "query_report.json"):
        """Save processing report to JSON file"""
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n💾 Report saved to: {filename}")


def main():
    """Demo the SQL Agent"""
    # Initialize agent
    DATABASE_URL = "postgresql://testuser:testpass@localhost:5432/testdb"
    agent = SQLAgent(DATABASE_URL)
    
    # Example queries to test
    test_queries = [
        # Valid queries
        "SELECT name, email FROM users WHERE age > 30",
        "SELECT u.name, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.name",
        
        # Invalid query (bad column)
        "SELECT invalid_column FROM users",
        
        # Unsafe query
        "DELETE FROM users WHERE id = 1"
    ]
    
    print("\n🚀 Starting SQL Agent Demo\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"TEST QUERY {i}/{len(test_queries)}")
        print(f"{'='*80}")
        
        result = agent.process_query(query, verbose=True)
        
        # Save report for first query
        if i == 1:
            agent.save_report(result, f"query_report_{i}.json")
        
        input("\nPress Enter to continue to next query...")


if __name__ == "__main__":
    main()
