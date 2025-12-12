# schema_grounding_plugin.py
# SchemaGroundingPlugin for Semantic Kernel (updated get_table_columns to match your Table_columns schema)
# and added a VERY SIMPLE execute_sql_script kernel function that directly executes the given SQL.
#
# Replace DB_PATH placeholder below with the path to your .sqlite file before using.

import sqlite3
import asyncio
from typing import List, Dict, Any, Optional
from semantic_kernel.functions import kernel_function

# ----- CONFIG: replace this with your actual sqlite path -----
DB_PATH = "./db.sqlite"  # <-- replace me with the actual .sqlite file path
# -------------------------------------------------------------


async def _query_sqlite(db_path: str, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
    """
    Helper: run blocking sqlite queries in a thread to avoid blocking the event loop.
    Returns list of dicts (rows).
    """
    params = params or []

    def run():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    return await asyncio.to_thread(run)


class SchemaGroundingPlugin:
    """
    Schema Grounding Plugin exposing kernel functions:
      - get_table_descriptions(): returns all rows from table_description (table_name + description).
      - get_table_columns(table_names): given a list of table names, returns column metadata from table_columns.
      - execute_sql_script(sql): (VERY SIMPLE) executes the provided SQL and returns rows & columns.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH



    @kernel_function(description="Return all rows from table_description and table_columns.")
    async def get_schema_info(self) -> Dict[str, List[Dict[str, Any]]]:
        result = {
            "table_description": [],
            "table_columns": []
        }

        # ---- FETCH table_description ----
        try:
            query = "SELECT * FROM table_description;"
            rows = await _query_sqlite(self.db_path, query)
            normalized = []
            for r in rows:
                row = {k: (v if v is not None else "") for k, v in r.items()}
                if "table_name" not in row:
                    continue
                if "description" not in row:
                    row["description"] = ""
                normalized.append(row)
            result["table_description"] = normalized
        except Exception:
            result["table_description"] = []

        # ---- FETCH table_columns ----
        try:
            query = "SELECT * FROM table_columns;"
            rows = await _query_sqlite(self.db_path, query)
            normalized = []
            for r in rows:
                row = {k: (v if v is not None else "") for k, v in r.items()}

                table_col = row.get("table_name") or row.get("table") or row.get("tablename") or ""
                column_col = row.get("column_name") or row.get("column") or row.get("colname") or ""

                if not table_col or not column_col:
                    continue

                if "description" not in row:
                    row["description"] = ""
                if "datatype" not in row:
                    row["datatype"] = ""

                normalized.append({
                    "table_name": table_col,
                    "column_name": column_col,
                    "description": row["description"],
                    "datatype": row["datatype"]
                })

            result["table_columns"] = normalized
        except Exception:
            result["table_columns"] = []
        print("i trust you!!!")
        return result

  

    @kernel_function(
        description="Execute the provided SQL script directly on the SQLite DB and return rows & columns."
    )
    async def execute_sql_script(self, sql: str) -> Dict[str, Any]:

        def run():
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            try:
                cur.execute(sql)
                fetched = cur.fetchall()
                cols = [c[0] for c in cur.description] if cur.description else []
                rows = [dict(r) for r in fetched]
                return {
                    "success": True,
                    "rows": rows,
                    "columns": cols,
                    "row_count": len(rows),
                    "error": None
                }
            except Exception as e:
                return {
                    "success": False,
                    "rows": [],
                    "columns": [],
                    "row_count": 0,
                    "error": str(e)
                }
            finally:
                try:
                    cur.close()
                except Exception:
                    pass
                conn.close()
        print("it's working!!!!!!")
        return await asyncio.to_thread(run)
