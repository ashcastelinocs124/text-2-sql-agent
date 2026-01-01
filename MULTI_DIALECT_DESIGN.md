# Multi-Dialect SQL Evaluation Architecture

## Goal
Make AgentX database-agnostic, supporting SQLite, BigQuery, PostgreSQL, DuckDB, Snowflake, and any SQL dialect.

---

## 1. Dialect Registry & Configuration

```python
# src/agentx/dialects/registry.py

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Set, Callable

class Dialect(Enum):
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    BIGQUERY = "bigquery"
    SNOWFLAKE = "snowflake"
    DUCKDB = "duckdb"
    MYSQL = "mysql"
    CLICKHOUSE = "clickhouse"

@dataclass
class DialectConfig:
    """Configuration for a specific SQL dialect."""
    name: Dialect
    sqlglot_dialect: str  # sqlglot dialect name
    sqlalchemy_driver: str  # SQLAlchemy connection string prefix

    # Schema introspection
    default_schema: Optional[str]  # "public" for PG, None for SQLite, dataset for BQ
    supports_schemas: bool
    information_schema_query: str  # How to get table/column info

    # Dialect-specific features
    supports_cte: bool
    supports_window_functions: bool
    supports_json: bool
    supports_arrays: bool

    # Valid functions for this dialect
    builtin_functions: Set[str]

    # Connection factory
    connection_factory: Optional[Callable] = None


# Pre-defined dialect configurations
DIALECT_CONFIGS = {
    Dialect.SQLITE: DialectConfig(
        name=Dialect.SQLITE,
        sqlglot_dialect="sqlite",
        sqlalchemy_driver="sqlite",
        default_schema=None,
        supports_schemas=False,
        information_schema_query="""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """,
        supports_cte=True,
        supports_window_functions=True,
        supports_json=True,  # SQLite 3.38+
        supports_arrays=False,
        builtin_functions={
            "ABS", "AVG", "COUNT", "MAX", "MIN", "SUM", "TOTAL",
            "LENGTH", "LOWER", "UPPER", "SUBSTR", "TRIM", "REPLACE",
            "COALESCE", "IFNULL", "NULLIF", "IIF",
            "DATE", "TIME", "DATETIME", "JULIANDAY", "STRFTIME",
            "TYPEOF", "CAST", "INSTR", "PRINTF", "RANDOM",
            "ROW_NUMBER", "RANK", "DENSE_RANK", "LAG", "LEAD",
            "JSON", "JSON_EXTRACT", "JSON_ARRAY", "JSON_OBJECT",
            "GROUP_CONCAT", "HEX", "QUOTE", "ZEROBLOB",
        }
    ),

    Dialect.BIGQUERY: DialectConfig(
        name=Dialect.BIGQUERY,
        sqlglot_dialect="bigquery",
        sqlalchemy_driver="bigquery",
        default_schema=None,  # Uses project.dataset.table
        supports_schemas=True,  # Datasets act as schemas
        information_schema_query="""
            SELECT table_name, column_name, data_type
            FROM `{dataset}.INFORMATION_SCHEMA.COLUMNS`
        """,
        supports_cte=True,
        supports_window_functions=True,
        supports_json=True,
        supports_arrays=True,
        builtin_functions={
            # Standard SQL
            "COUNT", "SUM", "AVG", "MIN", "MAX", "ABS", "ROUND", "CEIL", "FLOOR",
            "UPPER", "LOWER", "TRIM", "CONCAT", "LENGTH", "SUBSTR", "REPLACE",
            "COALESCE", "NULLIF", "IFNULL", "IF", "CASE",
            # BigQuery-specific
            "SAFE_DIVIDE", "SAFE_MULTIPLY", "SAFE_NEGATE", "SAFE_ADD", "SAFE_SUBTRACT",
            "DATE_DIFF", "DATE_ADD", "DATE_SUB", "DATE_TRUNC", "DATETIME_DIFF",
            "TIMESTAMP_DIFF", "TIMESTAMP_ADD", "TIMESTAMP_SUB", "TIMESTAMP_TRUNC",
            "PARSE_DATE", "PARSE_DATETIME", "PARSE_TIMESTAMP", "FORMAT_DATE",
            "ARRAY_AGG", "ARRAY_LENGTH", "ARRAY_TO_STRING", "GENERATE_ARRAY",
            "STRUCT", "UNNEST", "ARRAY", "CURRENT_DATE", "CURRENT_TIMESTAMP",
            "REGEXP_CONTAINS", "REGEXP_EXTRACT", "REGEXP_REPLACE",
            "JSON_EXTRACT", "JSON_EXTRACT_SCALAR", "JSON_QUERY", "JSON_VALUE",
            "ST_GEOGPOINT", "ST_DISTANCE", "ST_CONTAINS", "ST_INTERSECTS",
            "APPROX_COUNT_DISTINCT", "APPROX_QUANTILES", "APPROX_TOP_COUNT",
            "FARM_FINGERPRINT", "MD5", "SHA256", "SHA512",
            "NET.IP_FROM_STRING", "NET.SAFE_IP_FROM_STRING", "NET.IP_TO_STRING",
            "ROW_NUMBER", "RANK", "DENSE_RANK", "LAG", "LEAD", "FIRST_VALUE", "LAST_VALUE",
            "NTILE", "PERCENT_RANK", "CUME_DIST",
        }
    ),

    Dialect.POSTGRESQL: DialectConfig(
        name=Dialect.POSTGRESQL,
        sqlglot_dialect="postgres",
        sqlalchemy_driver="postgresql",
        default_schema="public",
        supports_schemas=True,
        information_schema_query="""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = '{schema}'
        """,
        supports_cte=True,
        supports_window_functions=True,
        supports_json=True,
        supports_arrays=True,
        builtin_functions={
            "COUNT", "SUM", "AVG", "MIN", "MAX", "ABS", "ROUND", "CEIL", "FLOOR",
            "UPPER", "LOWER", "TRIM", "CONCAT", "LENGTH", "SUBSTR", "REPLACE",
            "COALESCE", "NULLIF", "NOW", "CURRENT_DATE", "CURRENT_TIMESTAMP",
            "EXTRACT", "DATE_TRUNC", "TO_CHAR", "TO_DATE", "TO_TIMESTAMP",
            "STRING_AGG", "ARRAY_AGG", "JSON_AGG", "JSONB_AGG",
            "ROW_NUMBER", "RANK", "DENSE_RANK", "LAG", "LEAD", "FIRST_VALUE", "LAST_VALUE",
            "NTILE", "PERCENT_RANK", "CUME_DIST",
            "JSON_EXTRACT_PATH", "JSONB_EXTRACT_PATH", "JSON_BUILD_OBJECT",
            "REGEXP_MATCH", "REGEXP_REPLACE", "REGEXP_SPLIT_TO_ARRAY",
            "GENERATE_SERIES", "UNNEST", "ANY", "ALL",
        }
    ),

    Dialect.DUCKDB: DialectConfig(
        name=Dialect.DUCKDB,
        sqlglot_dialect="duckdb",
        sqlalchemy_driver="duckdb",
        default_schema="main",
        supports_schemas=True,
        information_schema_query="""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = '{schema}'
        """,
        supports_cte=True,
        supports_window_functions=True,
        supports_json=True,
        supports_arrays=True,
        builtin_functions={
            "COUNT", "SUM", "AVG", "MIN", "MAX", "ABS", "ROUND", "CEIL", "FLOOR",
            "UPPER", "LOWER", "TRIM", "CONCAT", "LENGTH", "SUBSTR", "REPLACE",
            "COALESCE", "NULLIF", "NOW", "CURRENT_DATE", "CURRENT_TIMESTAMP",
            "STRFTIME", "DATE_TRUNC", "DATE_PART", "DATE_DIFF",
            "LIST_AGG", "ARRAY_AGG", "STRING_AGG",
            "ROW_NUMBER", "RANK", "DENSE_RANK", "LAG", "LEAD",
            "READ_CSV", "READ_PARQUET", "READ_JSON",  # DuckDB-specific
            "UNNEST", "GENERATE_SERIES", "RANGE",
        }
    ),

    Dialect.SNOWFLAKE: DialectConfig(
        name=Dialect.SNOWFLAKE,
        sqlglot_dialect="snowflake",
        sqlalchemy_driver="snowflake",
        default_schema="PUBLIC",
        supports_schemas=True,
        information_schema_query="""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = '{schema}'
        """,
        supports_cte=True,
        supports_window_functions=True,
        supports_json=True,
        supports_arrays=True,
        builtin_functions={
            "COUNT", "SUM", "AVG", "MIN", "MAX", "ABS", "ROUND", "CEIL", "FLOOR",
            "UPPER", "LOWER", "TRIM", "CONCAT", "LENGTH", "SUBSTR", "REPLACE",
            "COALESCE", "NULLIF", "NVL", "NVL2", "ZEROIFNULL",
            "DATEADD", "DATEDIFF", "DATE_TRUNC", "DATE_PART", "DAYNAME", "MONTHNAME",
            "TO_DATE", "TO_TIMESTAMP", "TO_TIME", "TO_CHAR", "TO_VARCHAR",
            "TRY_TO_DATE", "TRY_TO_TIMESTAMP", "TRY_TO_NUMBER",
            "ARRAY_AGG", "ARRAY_SIZE", "ARRAY_SLICE", "ARRAY_CAT", "ARRAY_COMPACT",
            "OBJECT_CONSTRUCT", "OBJECT_KEYS", "OBJECT_AGG",
            "PARSE_JSON", "TRY_PARSE_JSON", "GET_PATH", "FLATTEN",
            "IFF", "IFNULL", "DECODE", "CASE",
            "REGEXP_LIKE", "REGEXP_REPLACE", "REGEXP_SUBSTR", "REGEXP_COUNT",
            "SPLIT", "SPLIT_PART", "STRTOK", "STRTOK_TO_ARRAY",
            "HASH", "MD5", "SHA1", "SHA2",
            "LISTAGG", "QUALIFY",
            "ROW_NUMBER", "RANK", "DENSE_RANK", "LAG", "LEAD",
            "RATIO_TO_REPORT", "CUME_DIST", "PERCENT_RANK", "NTILE",
        }
    ),
}

def get_dialect_config(dialect: str) -> DialectConfig:
    """Get configuration for a dialect by name."""
    dialect_enum = Dialect(dialect.lower())
    return DIALECT_CONFIGS[dialect_enum]
```

---

## 2. Database Abstraction Layer

```python
# src/agentx/infrastructure/database.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import sqlite3

@dataclass
class ColumnInfo:
    name: str
    dtype: str
    nullable: bool
    primary_key: bool = False
    foreign_key: Optional[str] = None

@dataclass
class TableInfo:
    name: str
    columns: List[ColumnInfo]
    row_count: Optional[int] = None

@dataclass
class SchemaSnapshot:
    dialect: str
    database: str
    tables: Dict[str, TableInfo]

    def has_table(self, name: str) -> bool:
        return name.lower() in {t.lower() for t in self.tables}

    def has_column(self, table: str, column: str) -> bool:
        table_info = self.tables.get(table.lower()) or self.tables.get(table)
        if not table_info:
            return False
        return column.lower() in {c.name.lower() for c in table_info.columns}


class DatabaseAdapter(ABC):
    """Abstract base for database-specific operations."""

    @abstractmethod
    def connect(self, connection_string: str) -> Any:
        """Create a database connection."""
        pass

    @abstractmethod
    def get_schema_snapshot(self) -> SchemaSnapshot:
        """Get complete schema information."""
        pass

    @abstractmethod
    def execute(self, sql: str) -> List[Dict[str, Any]]:
        """Execute SQL and return results as list of dicts."""
        pass

    @abstractmethod
    def get_dialect(self) -> str:
        """Return the sqlglot dialect name."""
        pass


class SQLiteAdapter(DatabaseAdapter):
    """SQLite-specific database adapter."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = None

    def connect(self, connection_string: str = None) -> sqlite3.Connection:
        path = connection_string or self.db_path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def get_dialect(self) -> str:
        return "sqlite"

    def get_schema_snapshot(self) -> SchemaSnapshot:
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        tables = {}

        # Get all tables
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)

        for (table_name,) in cursor.fetchall():
            # Get columns for each table
            cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns = []
            for row in cursor.fetchall():
                columns.append(ColumnInfo(
                    name=row[1],  # name
                    dtype=row[2],  # type
                    nullable=not row[3],  # notnull
                    primary_key=bool(row[5]),  # pk
                ))

            tables[table_name] = TableInfo(name=table_name, columns=columns)

        return SchemaSnapshot(
            dialect="sqlite",
            database=self.db_path,
            tables=tables
        )

    def execute(self, sql: str) -> List[Dict[str, Any]]:
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute(sql)

        if cursor.description:
            columns = [d[0] for d in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        return []


class BigQueryAdapter(DatabaseAdapter):
    """BigQuery-specific database adapter."""

    def __init__(self, project: str, dataset: str):
        self.project = project
        self.dataset = dataset
        self.client = None

    def connect(self, connection_string: str = None) -> Any:
        from google.cloud import bigquery
        self.client = bigquery.Client(project=self.project)
        return self.client

    def get_dialect(self) -> str:
        return "bigquery"

    def get_schema_snapshot(self) -> SchemaSnapshot:
        if not self.client:
            self.connect()

        tables = {}
        dataset_ref = self.client.dataset(self.dataset)

        for table in self.client.list_tables(dataset_ref):
            table_ref = dataset_ref.table(table.table_id)
            table_obj = self.client.get_table(table_ref)

            columns = []
            for field in table_obj.schema:
                columns.append(ColumnInfo(
                    name=field.name,
                    dtype=field.field_type,
                    nullable=(field.mode != "REQUIRED"),
                ))

            tables[table.table_id] = TableInfo(
                name=table.table_id,
                columns=columns,
                row_count=table_obj.num_rows
            )

        return SchemaSnapshot(
            dialect="bigquery",
            database=f"{self.project}.{self.dataset}",
            tables=tables
        )

    def execute(self, sql: str) -> List[Dict[str, Any]]:
        if not self.client:
            self.connect()

        query_job = self.client.query(sql)
        results = query_job.result()

        return [dict(row) for row in results]


class DuckDBAdapter(DatabaseAdapter):
    """DuckDB-specific database adapter."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = None

    def connect(self, connection_string: str = None) -> Any:
        import duckdb
        path = connection_string or self.db_path
        self.conn = duckdb.connect(path)
        return self.conn

    def get_dialect(self) -> str:
        return "duckdb"

    def get_schema_snapshot(self) -> SchemaSnapshot:
        if not self.conn:
            self.connect()

        tables = {}

        # Get all tables
        result = self.conn.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
        """).fetchall()

        for (table_name,) in result:
            # Get columns
            cols = self.conn.execute(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
            """).fetchall()

            columns = [
                ColumnInfo(
                    name=col[0],
                    dtype=col[1],
                    nullable=(col[2] == 'YES')
                )
                for col in cols
            ]

            tables[table_name] = TableInfo(name=table_name, columns=columns)

        return SchemaSnapshot(
            dialect="duckdb",
            database=self.db_path,
            tables=tables
        )

    def execute(self, sql: str) -> List[Dict[str, Any]]:
        if not self.conn:
            self.connect()

        result = self.conn.execute(sql)
        columns = [desc[0] for desc in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]


# Factory function
def create_adapter(dialect: str, **kwargs) -> DatabaseAdapter:
    """Create appropriate database adapter for dialect."""
    adapters = {
        "sqlite": SQLiteAdapter,
        "bigquery": BigQueryAdapter,
        "duckdb": DuckDBAdapter,
        # Add more as needed
    }

    adapter_class = adapters.get(dialect.lower())
    if not adapter_class:
        raise ValueError(f"Unsupported dialect: {dialect}")

    return adapter_class(**kwargs)
```

---

## 3. Dialect-Aware SQL Parser

```python
# src/agentx/validation/sql_parser.py

import sqlglot
from typing import List, Set, Dict, Any, Optional
from dataclasses import dataclass
from .dialect_registry import get_dialect_config, Dialect

@dataclass
class IdentifierSet:
    tables: List[str]
    columns: List[str]
    functions: List[str]
    aliases: Dict[str, str]

@dataclass
class ParsedSQL:
    ast: Any
    dialect: str
    identifiers: IdentifierSet
    raw_sql: str


class MultiDialectSQLParser:
    """SQL parser that handles multiple dialects using sqlglot."""

    def __init__(self, default_dialect: str = "sqlite"):
        self.default_dialect = default_dialect

    def parse(self, sql: str, dialect: str = None) -> ParsedSQL:
        """Parse SQL for the specified dialect."""
        dialect = dialect or self.default_dialect
        config = get_dialect_config(dialect)

        try:
            ast = sqlglot.parse_one(sql, read=config.sqlglot_dialect)
        except Exception as e:
            # Try with fallback dialects
            ast = self._parse_with_fallback(sql, dialect)

        identifiers = self._extract_identifiers(ast)

        return ParsedSQL(
            ast=ast,
            dialect=dialect,
            identifiers=identifiers,
            raw_sql=sql
        )

    def _parse_with_fallback(self, sql: str, primary_dialect: str) -> Any:
        """Try parsing with multiple dialects."""
        fallbacks = ["sqlite", "postgres", "bigquery", None]

        for dialect in fallbacks:
            try:
                return sqlglot.parse_one(sql, read=dialect)
            except:
                continue

        # Last resort: ignore errors
        return sqlglot.parse_one(sql, error_level=sqlglot.ErrorLevel.IGNORE)

    def _extract_identifiers(self, ast: Any) -> IdentifierSet:
        """Extract tables, columns, functions from AST."""
        tables = []
        columns = []
        functions = []
        aliases = {}

        # Tables
        for table in ast.find_all(sqlglot.exp.Table):
            name = table.name
            if table.db:
                name = f"{table.db}.{name}"
            tables.append(name)

        # Columns
        for col in ast.find_all(sqlglot.exp.Column):
            name = col.name
            if col.table:
                name = f"{col.table}.{name}"
            columns.append(name)

        # Functions
        for func in ast.find_all(sqlglot.exp.Func):
            func_name = func.__class__.__name__.upper()
            if hasattr(func, 'sql_name'):
                func_name = func.sql_name().upper()
            functions.append(func_name)

        # Aliases
        for alias in ast.find_all(sqlglot.exp.Alias):
            if hasattr(alias.this, 'name'):
                aliases[alias.alias] = alias.this.name

        return IdentifierSet(
            tables=list(set(tables)),
            columns=list(set(columns)),
            functions=list(set(functions)),
            aliases=aliases
        )

    def validate_functions(self, sql: str, dialect: str) -> List[str]:
        """Check if functions in SQL are valid for dialect."""
        parsed = self.parse(sql, dialect)
        config = get_dialect_config(dialect)

        invalid_functions = []
        for func in parsed.identifiers.functions:
            if func.upper() not in config.builtin_functions:
                invalid_functions.append(func)

        return invalid_functions

    def transpile(self, sql: str, from_dialect: str, to_dialect: str) -> str:
        """Convert SQL from one dialect to another."""
        from_config = get_dialect_config(from_dialect)
        to_config = get_dialect_config(to_dialect)

        return sqlglot.transpile(
            sql,
            read=from_config.sqlglot_dialect,
            write=to_config.sqlglot_dialect,
            pretty=True
        )[0]
```

---

## 4. Updated Hallucination Detector

```python
# src/agentx/validation/hallucination_detector.py

from dataclasses import dataclass
from typing import List, Optional
from .sql_parser import MultiDialectSQLParser
from .dialect_registry import get_dialect_config
from ..infrastructure.database import SchemaSnapshot

@dataclass
class HallucinationReport:
    phantom_tables: List[str]
    phantom_columns: List[str]
    phantom_functions: List[str]
    dialect: str
    hallucination_score: float = 0.0

    @property
    def total_hallucinations(self) -> int:
        return len(self.phantom_tables) + len(self.phantom_columns) + len(self.phantom_functions)


class HallucinationDetector:
    """Dialect-aware hallucination detection."""

    def __init__(self, dialect: str = "sqlite"):
        self.dialect = dialect
        self.parser = MultiDialectSQLParser(default_dialect=dialect)
        self.config = get_dialect_config(dialect)

    def detect(self, sql: str, schema: SchemaSnapshot) -> HallucinationReport:
        """Detect phantom identifiers in SQL."""
        parsed = self.parser.parse(sql, self.dialect)

        # Detect phantom tables
        phantom_tables = self._detect_phantom_tables(
            parsed.identifiers.tables, schema
        )

        # Detect phantom columns
        phantom_columns = self._detect_phantom_columns(
            parsed.identifiers.columns,
            parsed.identifiers.tables,
            parsed.identifiers.aliases,
            schema
        )

        # Detect phantom functions (dialect-aware)
        phantom_functions = self._detect_phantom_functions(
            parsed.identifiers.functions
        )

        # Calculate score
        total_ids = (
            len(parsed.identifiers.tables) +
            len(parsed.identifiers.columns) +
            len(parsed.identifiers.functions)
        )
        total_phantoms = (
            len(phantom_tables) +
            len(phantom_columns) +
            len(phantom_functions)
        )
        score = total_phantoms / max(1, total_ids)

        return HallucinationReport(
            phantom_tables=phantom_tables,
            phantom_columns=phantom_columns,
            phantom_functions=phantom_functions,
            dialect=self.dialect,
            hallucination_score=score
        )

    def _detect_phantom_tables(self, tables: List[str], schema: SchemaSnapshot) -> List[str]:
        """Find tables that don't exist."""
        phantom = []
        for table in tables:
            # Handle qualified names
            table_name = table.split(".")[-1]
            if not schema.has_table(table_name) and not schema.has_table(table):
                phantom.append(table)
        return phantom

    def _detect_phantom_columns(
        self,
        columns: List[str],
        tables: List[str],
        aliases: dict,
        schema: SchemaSnapshot
    ) -> List[str]:
        """Find columns that don't exist."""
        phantom = []

        # Build set of valid columns
        valid_columns = set()
        for table in tables:
            table_name = table.split(".")[-1]
            table_info = schema.tables.get(table_name)
            if table_info:
                for col in table_info.columns:
                    valid_columns.add(col.name.lower())
                    valid_columns.add(f"{table_name.lower()}.{col.name.lower()}")

        # Check each column
        for col in columns:
            col_lower = col.lower()
            col_name = col.split(".")[-1].lower()

            # Skip if found
            if col_lower in valid_columns or col_name in valid_columns:
                continue

            # Check if it's an alias
            if col_name in {a.lower() for a in aliases}:
                continue

            phantom.append(col)

        return phantom

    def _detect_phantom_functions(self, functions: List[str]) -> List[str]:
        """Find functions not valid for this dialect."""
        phantom = []
        valid_functions = self.config.builtin_functions

        for func in functions:
            if func.upper() not in valid_functions:
                # Check if it's a common alias
                if not self._is_common_function_alias(func):
                    phantom.append(func)

        return phantom

    def _is_common_function_alias(self, func: str) -> bool:
        """Check for common AST function name variations."""
        common = {"ANONYMOUS", "PAREN", "BRACKET"}
        return func.upper() in common
```

---

## 5. Multi-Dialect Gold Query Generator

```python
# src/agentx/tasks/gold_query_generator.py

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import json
from .sql_parser import MultiDialectSQLParser

@dataclass
class GoldQuery:
    id: str
    question: str
    dialect: str
    sql: str
    expected_result: Optional[List[Dict[str, Any]]]
    difficulty: str
    tags: List[str]


class GoldQueryGenerator:
    """Generate gold queries for multiple dialects."""

    # Base queries that work across dialects
    BASE_QUERIES = [
        {
            "id": "simple_select",
            "question": "Get all customers",
            "sql": {
                "sqlite": "SELECT * FROM customers LIMIT 10",
                "postgresql": "SELECT * FROM customers LIMIT 10",
                "bigquery": "SELECT * FROM customers LIMIT 10",
                "duckdb": "SELECT * FROM customers LIMIT 10",
            },
            "difficulty": "easy",
            "tags": ["select", "basic"]
        },
        {
            "id": "count_aggregation",
            "question": "Count total orders",
            "sql": {
                "sqlite": "SELECT COUNT(*) as total FROM orders",
                "postgresql": "SELECT COUNT(*) as total FROM orders",
                "bigquery": "SELECT COUNT(*) as total FROM orders",
                "duckdb": "SELECT COUNT(*) as total FROM orders",
            },
            "difficulty": "easy",
            "tags": ["aggregation", "count"]
        },
        {
            "id": "date_filtering",
            "question": "Get orders from last 30 days",
            "sql": {
                "sqlite": """
                    SELECT * FROM orders
                    WHERE order_date >= date('now', '-30 days')
                """,
                "postgresql": """
                    SELECT * FROM orders
                    WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
                """,
                "bigquery": """
                    SELECT * FROM orders
                    WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                """,
                "duckdb": """
                    SELECT * FROM orders
                    WHERE order_date >= CURRENT_DATE - INTERVAL 30 DAY
                """,
            },
            "difficulty": "medium",
            "tags": ["date", "filtering"]
        },
        {
            "id": "string_functions",
            "question": "Get customers with names starting with 'J'",
            "sql": {
                "sqlite": """
                    SELECT * FROM customers
                    WHERE name LIKE 'J%'
                """,
                "postgresql": """
                    SELECT * FROM customers
                    WHERE name LIKE 'J%'
                """,
                "bigquery": """
                    SELECT * FROM customers
                    WHERE STARTS_WITH(name, 'J')
                """,
                "duckdb": """
                    SELECT * FROM customers
                    WHERE name LIKE 'J%'
                """,
            },
            "difficulty": "easy",
            "tags": ["string", "filtering"]
        },
        {
            "id": "window_function",
            "question": "Rank customers by total spending",
            "sql": {
                "sqlite": """
                    SELECT
                        customer_id,
                        total_spent,
                        ROW_NUMBER() OVER (ORDER BY total_spent DESC) as rank
                    FROM (
                        SELECT customer_id, SUM(amount) as total_spent
                        FROM orders
                        GROUP BY customer_id
                    )
                """,
                "postgresql": """
                    SELECT
                        customer_id,
                        SUM(amount) as total_spent,
                        RANK() OVER (ORDER BY SUM(amount) DESC) as rank
                    FROM orders
                    GROUP BY customer_id
                """,
                "bigquery": """
                    SELECT
                        customer_id,
                        SUM(amount) as total_spent,
                        RANK() OVER (ORDER BY SUM(amount) DESC) as rank
                    FROM orders
                    GROUP BY customer_id
                """,
                "duckdb": """
                    SELECT
                        customer_id,
                        SUM(amount) as total_spent,
                        RANK() OVER (ORDER BY SUM(amount) DESC) as rank
                    FROM orders
                    GROUP BY customer_id
                """,
            },
            "difficulty": "hard",
            "tags": ["window", "ranking", "aggregation"]
        },
    ]

    def generate_for_dialect(self, dialect: str) -> List[GoldQuery]:
        """Generate gold queries for a specific dialect."""
        queries = []

        for base in self.BASE_QUERIES:
            if dialect in base["sql"]:
                queries.append(GoldQuery(
                    id=f"{base['id']}_{dialect}",
                    question=base["question"],
                    dialect=dialect,
                    sql=base["sql"][dialect],
                    expected_result=None,  # Populated by execution
                    difficulty=base["difficulty"],
                    tags=base["tags"]
                ))

        return queries

    def save_to_file(self, queries: List[GoldQuery], filepath: str):
        """Save queries to JSON file."""
        data = [
            {
                "id": q.id,
                "question": q.question,
                "dialect": q.dialect,
                "gold_sql": q.sql,
                "expected_result": q.expected_result,
                "difficulty": q.difficulty,
                "tags": q.tags
            }
            for q in queries
        ]

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
```

---

## 6. Updated SQL Agent

```python
# src/agentx/executor/sql_agent.py

from typing import Dict, Any, Optional
from dataclasses import dataclass
from ..infrastructure.database import DatabaseAdapter, create_adapter, SchemaSnapshot
from ..validation.hallucination_detector import HallucinationDetector
from ..validation.sql_parser import MultiDialectSQLParser

@dataclass
class AgentConfig:
    dialect: str
    connection_string: Optional[str] = None
    db_path: Optional[str] = None
    project: Optional[str] = None  # For BigQuery
    dataset: Optional[str] = None  # For BigQuery


class SQLAgent:
    """Multi-dialect SQL Agent."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.dialect = config.dialect

        # Create appropriate database adapter
        self.adapter = self._create_adapter()

        # Initialize validation components
        self.parser = MultiDialectSQLParser(default_dialect=self.dialect)
        self.detector = HallucinationDetector(dialect=self.dialect)

        # Get schema
        self.schema = self.adapter.get_schema_snapshot()

    def _create_adapter(self) -> DatabaseAdapter:
        """Create database adapter based on config."""
        if self.dialect == "sqlite":
            return create_adapter(
                "sqlite",
                db_path=self.config.db_path or ":memory:"
            )
        elif self.dialect == "bigquery":
            return create_adapter(
                "bigquery",
                project=self.config.project,
                dataset=self.config.dataset
            )
        elif self.dialect == "duckdb":
            return create_adapter(
                "duckdb",
                db_path=self.config.db_path or ":memory:"
            )
        else:
            # Default: try SQLAlchemy
            from sqlalchemy import create_engine
            # ... handle other dialects
            raise NotImplementedError(f"Dialect {self.dialect} not yet supported")

    def validate_query(self, sql: str) -> Dict[str, Any]:
        """Validate SQL for the configured dialect."""
        result = {
            "is_valid": True,
            "dialect": self.dialect,
            "errors": [],
            "warnings": [],
            "hallucination_report": None
        }

        try:
            # Parse and validate syntax
            parsed = self.parser.parse(sql, self.dialect)

            # Check for hallucinations
            hallucination_report = self.detector.detect(sql, self.schema)
            result["hallucination_report"] = hallucination_report

            if hallucination_report.total_hallucinations > 0:
                result["is_valid"] = False
                for table in hallucination_report.phantom_tables:
                    result["errors"].append(f"Table '{table}' does not exist")
                for col in hallucination_report.phantom_columns:
                    result["errors"].append(f"Column '{col}' does not exist")
                for func in hallucination_report.phantom_functions:
                    result["warnings"].append(
                        f"Function '{func}' may not be valid for {self.dialect}"
                    )

        except Exception as e:
            result["is_valid"] = False
            result["errors"].append(f"Parse error: {str(e)}")

        return result

    def execute(self, sql: str) -> Dict[str, Any]:
        """Execute SQL and return results."""
        import time

        start = time.time()
        try:
            results = self.adapter.execute(sql)
            elapsed = (time.time() - start) * 1000

            return {
                "success": True,
                "data": results,
                "rows_returned": len(results),
                "execution_time_ms": elapsed,
                "dialect": self.dialect
            }
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": elapsed,
                "dialect": self.dialect
            }

    def process_query(self, sql: str, validate: bool = True) -> Dict[str, Any]:
        """Full pipeline: validate → execute → analyze."""
        result = {
            "query": sql,
            "dialect": self.dialect,
            "validation": None,
            "execution": None,
            "overall_status": "FAILED"
        }

        # Validate
        if validate:
            validation = self.validate_query(sql)
            result["validation"] = validation

            if not validation["is_valid"]:
                return result

        # Execute
        execution = self.execute(sql)
        result["execution"] = execution

        if execution["success"]:
            result["overall_status"] = "SUCCESS"

        return result
```

---

## 7. Recommended File Structure

```
src/agentx/
├── dialects/
│   ├── __init__.py
│   ├── registry.py          # Dialect configurations
│   └── functions/
│       ├── sqlite.py        # SQLite function definitions
│       ├── bigquery.py      # BigQuery function definitions
│       ├── postgresql.py    # PostgreSQL function definitions
│       └── duckdb.py        # DuckDB function definitions
│
├── infrastructure/
│   ├── __init__.py
│   ├── database.py          # DatabaseAdapter ABC + implementations
│   ├── adapters/
│   │   ├── sqlite.py
│   │   ├── bigquery.py
│   │   ├── duckdb.py
│   │   └── postgresql.py
│   └── schema.py            # SchemaSnapshot, TableInfo, ColumnInfo
│
├── validation/
│   ├── __init__.py
│   ├── sql_parser.py        # MultiDialectSQLParser
│   ├── hallucination.py     # HallucinationDetector
│   └── schema_validator.py  # SchemaValidator
│
├── evaluation/
│   ├── __init__.py
│   ├── scorer.py
│   ├── comparators.py
│   └── runner.py
│
├── executor/
│   ├── __init__.py
│   └── sql_agent.py         # Multi-dialect SQLAgent
│
└── tasks/
    ├── __init__.py
    ├── gold_queries/
    │   ├── sqlite/
    │   ├── bigquery/
    │   └── postgresql/
    └── generator.py          # GoldQueryGenerator
```

---

## 8. Migration Checklist

- [ ] Create `src/agentx/dialects/registry.py` with dialect configs
- [ ] Implement `SQLiteAdapter` in `infrastructure/adapters/sqlite.py`
- [ ] Implement `DuckDBAdapter` in `infrastructure/adapters/duckdb.py`
- [ ] Implement `BigQueryAdapter` in `infrastructure/adapters/bigquery.py`
- [ ] Update `HallucinationDetector` to use dialect-aware function validation
- [ ] Update `SQLAgent` to accept dialect parameter
- [ ] Create gold queries per dialect
- [ ] Remove hardcoded PostgreSQL connection strings
- [ ] Update tests to run against multiple dialects
- [ ] Add SQLite as default for local development (no Docker needed!)

---

## 9. Benefits of This Architecture

| Benefit | Description |
|---------|-------------|
| **SQLite as default** | Zero setup for local development |
| **Easy testing** | In-memory SQLite for fast unit tests |
| **Production flexibility** | Same code works with BigQuery, Snowflake |
| **Dialect-aware validation** | Catch function errors before execution |
| **Transpilation** | Convert queries between dialects |
| **Extensible** | Add new dialects by implementing adapter |
