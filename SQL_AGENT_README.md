# 🤖 SQL Agent - Intelligent Query Validator & Executor

An intelligent agent that validates SQL queries, executes them in a sandbox environment, and provides comprehensive analysis and summaries.

## 🌟 Features

### 4-Step Validation Pipeline
1. **🔒 Safety Check** - Blocks dangerous operations (DELETE, DROP, ALTER, etc.)
2. **✅ Syntax Validation** - Ensures SQL is properly formatted
3. **📋 Schema Validation** - Verifies tables and columns exist
4. **🧠 Logic Optimization** - Checks query logic and optimizations

### Execution & Analysis
- **Sandbox Execution** - Safe query execution with result limits
- **Performance Metrics** - Execution time tracking
- **Data Preview** - First 5 rows of results
- **Intelligent Insights** - Automatic analysis and recommendations
- **JSON Reports** - Exportable query reports

## 🚀 Quick Start

### 1. Start the Database
```bash
docker-compose up -d
```

### 2. Choose Your Interface

#### Option A: Web Interface (Recommended)
```bash
python3 agent_server.py
```
Then open: **http://localhost:5000**

#### Option B: Interactive CLI
```bash
python3 agent_cli.py
```

#### Option C: Python API
```python
from sql_agent import SQLAgent

agent = SQLAgent("postgresql://testuser:testpass@localhost:5432/testdb")
result = agent.process_query("SELECT * FROM users")
print(result)
```

## 📁 Project Structure

```
Hackathon/
├── sql_agent.py          # Main agent class
├── agent_server.py       # Flask web server
├── agent_cli.py          # Interactive CLI
├── agent_web.html        # Web interface
├── hallucination.py      # Query validator
├── schema.py             # Schema inspector
├── test_hallucination.py # Unit tests
├── test_with_db.py       # Integration tests
├── docker-compose.yml    # PostgreSQL setup
└── init.sql             # Sample database
```

## 🎯 Usage Examples

### Web Interface
1. Start server: `python3 agent_server.py`
2. Open browser: http://localhost:5000
3. Enter query and click "Execute Query"
4. View validation, execution, and analysis results

### CLI Interface
```bash
$ python3 agent_cli.py

🔍 Enter SQL query: SELECT name, email FROM users WHERE age > 30

🤖 SQL AGENT - Query Processing
================================

✅ Validation PASSED
   - Query Type: Select
   - Tables: users
   - Columns: name, email, age

✅ Execution SUCCESSFUL
   - Rows returned: 3
   - Execution time: 10.32ms

📊 Analysis complete
   - Query returned 3 row(s) with 2 column(s) in 10.32ms

📄 Data Preview:
Row 1: {'name': 'Bob Smith', 'email': 'bob@example.com'}
Row 2: {'name': 'Charlie Brown', 'email': 'charlie@example.com'}
Row 3: {'name': 'Diana Prince', 'email': 'diana@example.com'}
```

### Python API
```python
from sql_agent import SQLAgent

# Initialize agent
agent = SQLAgent("postgresql://testuser:testpass@localhost:5432/testdb")

# Process query
result = agent.process_query(
    "SELECT u.name, COUNT(o.id) FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.name",
    verbose=True
)

# Access results
print(f"Status: {result['overall_status']}")
print(f"Rows: {result['execution']['rows_returned']}")
print(f"Time: {result['execution']['execution_time_ms']}ms")

# Save report
agent.save_report(result, "my_query_report.json")
```

## 🗄️ Database Connection

### Default Configuration
- **Host**: localhost
- **Port**: 5432
- **Database**: testdb
- **Username**: testuser
- **Password**: testpass
- **Connection String**: `postgresql://testuser:testpass@localhost:5432/testdb`

### Sample Schema
```sql
-- Users table
users (id, name, email, age, created_at)

-- Orders table
orders (id, user_id, amount, status, created_at)

-- Products table
products (id, name, price, stock, category)
```

## 🧪 Testing

### Unit Tests (Mocked)
```bash
python3 test_hallucination.py
```
**Result**: 11/11 tests passed ✅

### Integration Tests (Real Database)
```bash
python3 test_with_db.py
```
**Result**: 8/8 tests passed ✅

### Test Coverage
- ✅ Valid SELECT queries
- ✅ JOIN queries with multiple tables
- ✅ Aggregations (COUNT, SUM, AVG)
- ✅ Subqueries
- ✅ Invalid table detection
- ✅ Invalid column detection
- ✅ Unsafe operation blocking
- ✅ Syntax error handling

## 📊 Example Queries

### ✅ Valid Queries

**Simple SELECT:**
```sql
SELECT name, email FROM users WHERE age > 30
```

**JOIN with Aggregation:**
```sql
SELECT u.name, COUNT(o.id) as order_count, SUM(o.amount) as total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.name
```

**Subquery:**
```sql
SELECT name FROM users 
WHERE id IN (SELECT user_id FROM orders WHERE amount > 100)
```

**Aggregation by Category:**
```sql
SELECT category, COUNT(*) as product_count, AVG(price) as avg_price
FROM products
GROUP BY category
```

### ❌ Rejected Queries

**Unsafe DELETE:**
```sql
DELETE FROM users WHERE id = 1
-- Error: Unsafe operation detected: delete
```

**Invalid Table:**
```sql
SELECT * FROM invalid_table
-- Error: Invalid table invalid_table
```

**Invalid Column:**
```sql
SELECT invalid_column FROM users
-- Error: Invalid Column invalid_column
```

## 🐳 Docker Commands

**Start database:**
```bash
docker-compose up -d
```

**Stop database:**
```bash
docker-compose down
```

**View logs:**
```bash
docker-compose logs -f postgres
```

**Connect to PostgreSQL CLI:**
```bash
docker exec -it hackathon_postgres psql -U testuser -d testdb
```

**Reset database (delete all data):**
```bash
docker-compose down -v
docker-compose up -d
```

## 🔌 API Endpoints

### POST /api/execute
Execute a SQL query

**Request:**
```json
{
  "query": "SELECT * FROM users"
}
```

**Response:**
```json
{
  "query": "SELECT * FROM users",
  "timestamp": "2025-12-12T19:40:05",
  "validation": {
    "is_valid": true,
    "query_type": "Select",
    "tables_accessed": ["users"],
    "columns_accessed": ["*"]
  },
  "execution": {
    "success": true,
    "rows_returned": 4,
    "execution_time_ms": 10.32,
    "data": [...]
  },
  "analysis": {
    "summary": "Query returned 4 row(s) with 5 column(s) in 10.32ms",
    "insights": ["✅ Query executed very quickly"],
    "data_preview": [...]
  },
  "overall_status": "SUCCESS"
}
```

### GET /api/health
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

## 🎨 Web Interface Features

- **Beautiful gradient design** with animations
- **Real-time query execution**
- **Interactive example queries**
- **Detailed validation feedback**
- **Performance metrics**
- **Data table preview**
- **Insights and recommendations**
- **Responsive design**

## 📝 Output Report Format

Each query generates a comprehensive JSON report:

```json
{
  "query": "SELECT ...",
  "timestamp": "2025-12-12T19:40:05",
  "validation": {
    "is_valid": true,
    "errors": [],
    "warnings": [],
    "query_type": "Select",
    "tables_accessed": ["users"],
    "columns_accessed": ["name", "email"]
  },
  "execution": {
    "success": true,
    "rows_returned": 3,
    "columns": ["name", "email"],
    "data": [...],
    "execution_time_ms": 10.32,
    "error": null
  },
  "analysis": {
    "summary": "Query returned 3 row(s)...",
    "insights": ["✅ Query executed very quickly"],
    "data_preview": [...]
  },
  "overall_status": "SUCCESS"
}
```

## 🛡️ Security Features

- **Forbidden Operations**: Blocks DELETE, DROP, ALTER, TRUNCATE, INSERT, UPDATE, CREATE, GRANT, REVOKE, COPY
- **Result Limits**: Automatic LIMIT clause (max 100 rows)
- **Sandbox Execution**: Read-only query execution
- **Schema Validation**: Prevents SQL injection via non-existent tables/columns
- **Syntax Validation**: Catches malformed queries before execution

## 🚦 Status Indicators

- ✅ **SUCCESS** - Query validated and executed successfully
- ❌ **FAILED** - Query failed validation or execution
- ⚠️ **WARNING** - Query succeeded with warnings

## 💡 Tips

1. **Use the web interface** for the best visual experience
2. **Try example queries** to understand capabilities
3. **Check insights** for performance recommendations
4. **Save reports** for documentation and debugging
5. **Use CLI** for quick testing and automation

## 🔧 Troubleshooting

**Database connection failed:**
```bash
# Make sure Docker is running
docker-compose up -d

# Check container status
docker ps
```

**Web server won't start:**
```bash
# Install dependencies
pip3 install flask flask-cors sqlalchemy psycopg2-binary sqlglot

# Check if port 5000 is available
lsof -i :5000
```

**Query validation fails:**
- Check table and column names match the schema
- Ensure query syntax is valid PostgreSQL
- Avoid forbidden operations (DELETE, DROP, etc.)

## 📚 Dependencies

- **sqlglot** - SQL parsing and optimization
- **sqlalchemy** - Database ORM and connection
- **psycopg2-binary** - PostgreSQL driver
- **flask** - Web server framework
- **flask-cors** - CORS support

## 🎯 Use Cases

1. **Query Validation** - Test SQL before production
2. **Learning SQL** - Safe environment to practice
3. **API Development** - Validate user-generated queries
4. **Data Analysis** - Quick data exploration
5. **Security Testing** - Prevent SQL injection
6. **Performance Testing** - Measure query execution time

---

**Built with ❤️ for safe and intelligent SQL query processing**
