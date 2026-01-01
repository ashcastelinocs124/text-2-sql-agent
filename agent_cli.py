#!/usr/bin/env python3
"""
Interactive SQL Agent CLI
Run queries interactively and get instant feedback
"""
from sql_agent import SQLAgent
import sys


def print_banner():
    """Print welcome banner"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                          🤖 SQL AGENT - Interactive Mode                     ║
║                                                                              ║
║  Validate → Execute → Analyze → Summarize                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)


def print_help():
    """Print help information"""
    print("""
Commands:
  - Type or paste your SQL query and press Enter
  - Type 'examples' to see example queries
  - Type 'help' for this message
  - Type 'quit' or 'exit' to exit
  - Type 'clear' to clear screen
  
Features:
  ✅ Safety validation (blocks DELETE, DROP, etc.)
  ✅ Schema validation (checks tables and columns exist)
  ✅ Syntax validation
  ✅ Sandbox execution with result limits
  ✅ Performance analysis
  ✅ Data preview
    """)


def print_examples():
    """Print example queries"""
    print("""
📚 Example Queries:

1. Simple SELECT:
   SELECT name, email FROM users WHERE age > 30

2. JOIN with aggregation:
   SELECT u.name, COUNT(o.id) as order_count, SUM(o.amount) as total_spent
   FROM users u
   LEFT JOIN orders o ON u.id = o.user_id
   GROUP BY u.name

3. Subquery:
   SELECT name FROM users WHERE id IN (SELECT user_id FROM orders WHERE amount > 100)

4. Products by category:
   SELECT category, COUNT(*) as product_count, AVG(price) as avg_price
   FROM products
   GROUP BY category

5. Top spenders:
   SELECT u.name, SUM(o.amount) as total_spent
   FROM users u
   JOIN orders o ON u.id = o.user_id
   GROUP BY u.name
   ORDER BY total_spent DESC
   LIMIT 5

Try these or create your own!
    """)


def main():
    """Main interactive loop"""
    DATABASE_URL = "postgresql://testuser:testpass@localhost:5432/testdb"
    
    print_banner()
    
    try:
        agent = SQLAgent(DATABASE_URL)
        print("✅ Connected to database successfully!\n")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        print("\nMake sure Docker is running:")
        print("  docker-compose up -d")
        sys.exit(1)
    
    print_help()
    
    query_count = 0
    
    while True:
        try:
            # Get input
            print("\n" + "─" * 80)
            user_input = input("🔍 Enter SQL query (or 'help'): ").strip()
            
            # Handle commands
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == 'help':
                print_help()
                continue
            
            if user_input.lower() == 'examples':
                print_examples()
                continue
            
            if user_input.lower() == 'clear':
                print("\033[2J\033[H")  # Clear screen
                print_banner()
                continue
            
            # Process query
            query_count += 1
            result = agent.process_query(user_input, verbose=True)
            
            # Ask if user wants to save report
            if result["overall_status"] == "SUCCESS":
                save = input("\n💾 Save report to file? (y/n): ").strip().lower()
                if save == 'y':
                    filename = f"query_report_{query_count}.json"
                    agent.save_report(result, filename)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue


if __name__ == "__main__":
    main()
