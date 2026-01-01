"""
Test script to validate SQL queries against real PostgreSQL database
"""
from hallucination import HallucinationDetector

# Database connection string
DATABASE_URL = "postgresql://testuser:testpass@localhost:5432/testdb"

def test_queries():
    """Test various SQL queries against the database"""
    
    # Initialize detector with database connection
    detector = HallucinationDetector()
    detector.schema_inspector = detector.schema_inspector.__class__(DATABASE_URL)
    
    print("=" * 60)
    print("Testing SQL Validation with Real Database")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        {
            "name": "Valid SELECT query",
            "sql": "SELECT name, email FROM users WHERE age > 30",
            "should_pass": True
        },
        {
            "name": "Valid JOIN query",
            "sql": "SELECT u.name, o.amount FROM users u JOIN orders o ON u.id = o.user_id",
            "should_pass": True
        },
        {
            "name": "Invalid table name",
            "sql": "SELECT * FROM invalid_table",
            "should_pass": False
        },
        {
            "name": "Invalid column name",
            "sql": "SELECT invalid_column FROM users",
            "should_pass": False
        },
        {
            "name": "Unsafe DELETE operation",
            "sql": "DELETE FROM users WHERE id = 1",
            "should_pass": False
        },
        {
            "name": "Unsafe DROP operation",
            "sql": "DROP TABLE users",
            "should_pass": False
        },
        {
            "name": "Complex valid query",
            "sql": """
                SELECT u.name, COUNT(o.id) as order_count, SUM(o.amount) as total_spent
                FROM users u
                LEFT JOIN orders o ON u.id = o.user_id
                GROUP BY u.name
                HAVING COUNT(o.id) > 0
            """,
            "should_pass": True
        },
        {
            "name": "Subquery test",
            "sql": "SELECT name FROM users WHERE id IN (SELECT user_id FROM orders WHERE amount > 100)",
            "should_pass": True
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[Test {i}] {test['name']}")
        print(f"SQL: {test['sql'][:100]}{'...' if len(test['sql']) > 100 else ''}")
        
        try:
            result = detector.validate_sql(test['sql'])
            if test['should_pass']:
                print(f"✅ PASSED: {result}")
                passed += 1
            else:
                print(f"❌ FAILED: Expected error but query passed")
                failed += 1
        except ValueError as e:
            if not test['should_pass']:
                print(f"✅ PASSED: Correctly rejected - {e}")
                passed += 1
            else:
                print(f"❌ FAILED: {e}")
                failed += 1
        except Exception as e:
            print(f"❌ ERROR: Unexpected error - {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 60)

if __name__ == "__main__":
    import time
    print("Waiting for database to be ready...")
    time.sleep(2)  # Give database time to initialize
    
    try:
        test_queries()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("\nMake sure the Docker container is running:")
        print("  docker-compose up -d")
