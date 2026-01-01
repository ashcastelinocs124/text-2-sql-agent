from sqlalchemy import create_engine, inspect 


class Schemainspector:

    def __init__(self, postgreurl=None):

        self.databaseurl = postgreurl
        if self.databaseurl:
            self.engine = create_engine(self.databaseurl)
            self.inspector = inspect(self.engine)
        else:
            self.engine = None
            self.inspector = None
        self.schema = {}

    def get_schema(self):
        if not self.inspector:
            return {}
            
        for table in self.inspector.get_table_names(schema = "public"):
            self.schema[table] = {
            "columns": self.inspector.get_columns(table, schema="public"),
            "primary_key": self.inspector.get_pk_constraint(table, schema="public"),
            "foreign_keys": self.inspector.get_foreign_keys(table, schema="public"),
            "indexes": self.inspector.get_indexes(table, schema="public"),
            }
        return self.schema