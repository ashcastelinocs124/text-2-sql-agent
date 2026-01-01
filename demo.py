#!/usr/bin/env python3
"""
Quick demo of SQL Agent capabilities
"""
from sql_agent import SQLAgent
import time

def print_header(text):
    """Print a fancy header"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80 + "\n")

def demo():
    """Run a quick demo of the SQL Agent"""
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        🤖 SQL AGENT DEMO                                     ║
║                                                                              ║
║  This demo shows the agent validating, executing, and analyzing queries     ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize agent
    print("🔌 Connecting to database...")
    DATABASE_URL = "postgresql://testuser:testpass@localhost:5432/testdb"
    agent = SQLAgent(DATABASE_URL)
    print("✅ Connected!\n")
    
    time.sleep(1)
    
    # Demo queries
    demos = [
        {
            "title": "Demo 1: Simple Valid Query",
            "query": "SELECT name, email FROM users WHERE age > 30",
            "description": "A basic SELECT query that should pass all validations"
        },
        {
            "title": "Demo 2: Complex JOIN Query",
            "query": """
                SELECT u.name, COUNT(o.id) as order_count, SUM(o.amount) as total_spent
                FROM users u
                LEFT JOIN orders o ON u.id = o.user_id
                GROUP BY u.name
                ORDER BY total_spent DESC
            """,
            "description": "A complex query with JOIN, aggregations, and sorting"
        },
        {
            "title": "Demo 3: Invalid Column (Should Fail)",
            "query": "SELECT invalid_column FROM users",
            "description": "This query references a column that doesn't exist"
        },
        {
            "title": "Demo 4: Unsafe Operation (Should Fail)",
            "query": "DELETE FROM users WHERE id = 1",
            "description": "This dangerous operation should be blocked"
        }
    ]
    
    for i, demo in enumerate(demos, 1):
        print_header(f"{demo['title']}")
        print(f"📝 Description: {demo['description']}")
        print(f"\n💬 Query:\n{demo['query']}\n")
        
        input("Press Enter to execute...")
        
        # Process query
        result = agent.process_query(demo['query'], verbose=True)
        
        # Summary
        print("\n" + "─"*80)
        if result['overall_status'] == 'SUCCESS':
            print("✅ RESULT: Query executed successfully!")
            if result['execution']['rows_returned'] > 0:
                print(f"   Retrieved {result['execution']['rows_returned']} rows")
                print(f"   Execution time: {result['execution']['execution_time_ms']:.2f}ms")
        else:
            print("❌ RESULT: Query was rejected")
            if result['validation']['errors']:
                print(f"   Reason: {result['validation']['errors'][0]}")
        print("─"*80)
        
        if i < len(demos):
            input("\nPress Enter to continue to next demo...")
    
    # Final summary
    print_header("Demo Complete!")
    print("""
🎉 You've seen the SQL Agent in action!

The agent successfully:
  ✅ Validated query syntax
  ✅ Checked for unsafe operations
  ✅ Verified schema (tables and columns)
  ✅ Executed safe queries
  ✅ Analyzed results and performance
  ❌ Blocked dangerous operations

Next steps:
  1. Try the web interface: python3 agent_server.py
  2. Use the interactive CLI: python3 agent_cli.py
  3. Read the docs: README.md and QUICKSTART.md

Happy querying! 🚀
    """)

if __name__ == "__main__":
    try:
        demo()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("  1. Docker is running: docker-compose up -d")
        print("  2. Dependencies are installed: pip3 install -r requirements.txt")
