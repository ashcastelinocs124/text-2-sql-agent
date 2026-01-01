# 🚀 SQL Agent - Quick Start Guide

## What is SQL Agent?

SQL Agent is an intelligent system that:
1. **Validates** your SQL queries for safety and correctness
2. **Executes** them in a secure sandbox environment
3. **Analyzes** the results and performance
4. **Summarizes** everything in an easy-to-understand format

## 3 Ways to Use SQL Agent

### 1. 🌐 Web Interface (Easiest!)

**Start the server:**
```bash
python3 agent_server.py
```

**Open in browser:**
```
http://localhost:5000
```

**Features:**
- Beautiful visual interface
- Click example queries to try them
- See validation, execution, and analysis in real-time
- View data in formatted tables
- Get performance insights

**Example workflow:**
1. Type or click an example query
2. Click "Execute Query" button
3. See results instantly with:
   - ✅/❌ Validation status
   - Query type and tables accessed
   - Execution time
   - Data preview
   - Insights and recommendations

---

### 2. 💻 Interactive CLI

**Start the CLI:**
```bash
python3 agent_cli.py
```

**Commands:**
- Type your SQL query and press Enter
- `examples` - See example queries
- `help` - Show help
- `quit` - Exit

**Example session:**
```
🔍 Enter SQL query: SELECT name FROM users WHERE age > 30

🤖 SQL AGENT - Query Processing
================================

✅ Validation PASSED
   - Query Type: Select
   - Tables: users

✅ Execution SUCCESSFUL
   - Rows returned: 3
   - Execution time: 10.32ms

📄 Data Preview:
Row 1: {'name': 'Bob Smith'}
Row 2: {'name': 'Charlie Brown'}
Row 3: {'name': 'Diana Prince'}

💾 Save report to file? (y/n):
```

---

### 3. 🐍 Python API

**In your Python code:**
```python
from sql_agent import SQLAgent

# Initialize
agent = SQLAgent("postgresql://testuser:testpass@localhost:5432/testdb")

# Execute query
result = agent.process_query("SELECT * FROM users", verbose=True)

# Check status
if result['overall_status'] == 'SUCCESS':
    print(f"Got {result['execution']['rows_returned']} rows")
    print(f"Execution time: {result['execution']['execution_time_ms']}ms")
    
    # Access data
    for row in result['execution']['data']:
        print(row)
    
    # Save report
    agent.save_report(result, "my_report.json")
```

---

## Example Queries to Try

### ✅ These will work:

**1. Simple SELECT**
```sql
SELECT name, email FROM users WHERE age > 30
```

**2. JOIN with aggregation**
```sql
SELECT u.name, COUNT(o.id) as order_count 
FROM users u 
LEFT JOIN orders o ON u.id = o.user_id 
GROUP BY u.name
```

**3. Subquery**
```sql
SELECT name FROM users 
WHERE id IN (SELECT user_id FROM orders WHERE amount > 100)
```

**4. Aggregation**
```sql
SELECT category, AVG(price) as avg_price 
FROM products 
GROUP BY category
```

### ❌ These will be rejected:

**Unsafe DELETE**
```sql
DELETE FROM users WHERE id = 1
```
❌ Error: Unsafe operation detected: delete

**Invalid table**
```sql
SELECT * FROM fake_table
```
❌ Error: Invalid table fake_table

**Invalid column**
```sql
SELECT nonexistent_column FROM users
```
❌ Error: Invalid Column nonexistent_column

---

## Understanding the Output

Every query goes through 4 steps:

### Step 1: 🔒 Safety Check
- Blocks dangerous operations (DELETE, DROP, ALTER, etc.)
- Ensures query is read-only

### Step 2: ✅ Syntax Validation
- Checks SQL syntax is correct
- Parses the query structure

### Step 3: 📋 Schema Validation
- Verifies tables exist in database
- Confirms columns are valid
- Checks table relationships

### Step 4: 🧠 Logic Optimization
- Analyzes query logic
- Suggests optimizations

If all steps pass, the query is executed!

---

## Output Format

```json
{
  "overall_status": "SUCCESS",
  "validation": {
    "is_valid": true,
    "query_type": "Select",
    "tables_accessed": ["users"],
    "columns_accessed": ["name", "email"]
  },
  "execution": {
    "success": true,
    "rows_returned": 3,
    "execution_time_ms": 10.32,
    "data": [...]
  },
  "analysis": {
    "summary": "Query returned 3 row(s) with 2 column(s) in 10.32ms",
    "insights": ["✅ Query executed very quickly"],
    "data_preview": [...]
  }
}
```

---

## Tips for Success

1. **Start with the web interface** - It's the easiest way to learn
2. **Try the example queries** - They show what's possible
3. **Read the insights** - They give performance tips
4. **Save reports** - Great for documentation
5. **Use CLI for automation** - Perfect for scripts

---

## Common Issues

**"Database connection failed"**
→ Make sure Docker is running: `docker-compose up -d`

**"Port 5000 already in use"**
→ Another app is using that port. Stop it or change the port in `agent_server.py`

**"Module not found"**
→ Install dependencies: `pip3 install flask flask-cors sqlalchemy psycopg2-binary sqlglot`

---

## What's in the Database?

### Tables:
- **users** - 4 sample users (Alice, Bob, Charlie, Diana)
- **orders** - 5 sample orders
- **products** - 5 sample products (electronics & furniture)

### You can:
- SELECT data
- JOIN tables
- Use aggregations (COUNT, SUM, AVG)
- Write subqueries
- Filter with WHERE
- Group with GROUP BY
- Sort with ORDER BY

### You cannot:
- DELETE data
- DROP tables
- ALTER schema
- INSERT records
- UPDATE records

This keeps the sandbox safe!

---

## Next Steps

1. **Start the database**: `docker-compose up -d`
2. **Choose your interface**: Web, CLI, or Python
3. **Try example queries**
4. **Experiment with your own queries**
5. **Check the insights for learning**

Happy querying! 🎉
