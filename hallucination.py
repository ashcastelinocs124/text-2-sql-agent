import sqlglot
from sqlglot import parse_one
from schema import Schemainspector
from sqlglot.errors import ParseError
from sqlglot.optimizer import optimize


class HallucinationDetector:
    def __init__(self):
        self.schema_inspector = Schemainspector()
        self.forbidden =  ["alter", "drop", "truncate", "delete", "update","insert", "create", "grant", "revoke", "copy"]    
    def ast_version(self):
        ast_version = repr(parse_one("SELECT a + 1 AS z"))
    
    def validate_syntax(self,sql: str):
        """
        Function focuses on initial validation of the sql query and informating any syntax or expression issues.
        """
        try:
            parsed = sqlglot.parse_one(sql, read = "postgres")
            return parsed
        except Exception as e:
            raise ValueError(f"Invalid SQL Syntax: {e}")
    
    def schema_validation(self, parsed):
        """
        Function focuses on schema validation where we validate where columns and tables exist, 
        and whether their types match or not
        """

        try:
            schema = self.schema_inspector.get_schema()
            tables = parsed.find_all(sqlglot.exp.Table)
            
            # First, validate all tables exist and collect all valid columns
            all_valid_columns = set()
            
            for t in tables:
                table = t.name.lower()
                if table not in schema:
                    raise ValueError(f"Invalid table {table}")

                table_schema = schema[table]
                
                # Normalize columns to a set of names for checking
                # SQLAlchemy returns a list of dicts: [{'name': 'id', 'type': ...}, ...]
                raw_columns = table_schema.get('columns', [])
                if isinstance(raw_columns, list) and raw_columns and isinstance(raw_columns[0], dict):
                    table_columns = {c['name'].lower() for c in raw_columns}
                elif isinstance(raw_columns, dict):
                     table_columns = {k.lower() for k in raw_columns.keys()}
                else:
                    table_columns = {str(c).lower() for c in raw_columns}
                
                # Add this table's columns to the set of all valid columns
                all_valid_columns.update(table_columns)

            # Collect all aliases defined in the query (e.g., SUM(x) as total)
            # These should not be validated against the schema since they're computed columns
            aliases = set()
            for alias_node in parsed.find_all(sqlglot.exp.Alias):
                if alias_node.alias:
                    aliases.add(alias_node.alias.lower())

            # Now validate all columns in the query against the combined set
            columns = parsed.find_all(sqlglot.exp.Column)
            
            for col in columns:
                column = col.name.lower()
                # Skip special cases like COUNT(*), aggregate functions, etc.
                if column == '*':
                    continue
                # Skip aliases (computed columns like ORDER BY total_spent)
                if column in aliases:
                    continue
                if column not in all_valid_columns:
                    raise ValueError(f"Invalid Column {column}")
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            raise ValueError(f"Invalid SQL Schema: {e}")
    

    def validate_safe(self, sql: str):
        lowered = sql.lower()

        for bad in self.forbidden:
            if bad in lowered:
                raise ValueError(f"Unsafe operation detected: {bad}")
    
    def validate_logic(self, parsed, schema_dict):
        # sqlglot Schema expects dictionary mapping table names to column types: {table: {col: type}}
        # We need to transform schema_dict if it comes directly from sqlalchemy inspector (nested dict with 'columns' key)
        
        glot_schema = {}
        for table, meta in schema_dict.items():
            cols = meta.get('columns', [])
            col_map = {}
            
            if isinstance(cols, list) and cols and isinstance(cols[0], dict):
                # SQLAlchemy format: [{'name': 'a', 'type': TYPE}, ...]
                # We use str(type) to get a string representation for sqlglot
                col_map = {c['name']: str(c['type']) for c in cols}
            elif isinstance(cols, dict):
                col_map = cols
            else:
                 # usage as list of strings
                col_map = {c: "text" for c in cols}
            
            glot_schema[table] = col_map

        try:
            optimize(parsed, schema = glot_schema)

        except Exception as e:
            raise ValueError(f"Logical Error failed: {e}")
    
    def validate_sql(self, sql):
        # 1. Safety Check
        self.validate_safe(sql)
        
        # 2. Syntax Check
        parsed = self.validate_syntax(sql)
        
        # 3. Schema Existence Check
        self.schema_validation(parsed)

        # 4. Logic Optimization Check
        # Note: schema_validation fetches schema internally, but logic check needs it passed
        schema = self.schema_inspector.get_schema()
        self.validate_logic(parsed, schema)

        return "SQL Query is Valid"
