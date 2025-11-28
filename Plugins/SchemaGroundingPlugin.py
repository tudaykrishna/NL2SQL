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
DB_PATH = "/content/drive/MyDrive/db.sqlite"  # <-- replace me with the actual .sqlite file path
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

    @kernel_function(description="Return all rows from the table_description table (table_name + description).")
    async def get_table_descriptions(self) -> List[Dict[str, Any]]:
        query = "SELECT * FROM table_description;"
        try:
            rows = await _query_sqlite(self.db_path, query)
            normalized = []
            for r in rows:
                row = {k: (v if v is not None else "") for k, v in r.items()}
                if "table_name" not in row:
                    continue
                if "description" not in row:
                    row["description"] = ""
                normalized.append(row)
            return normalized
        except Exception:
            return []

    @kernel_function(
        description="Given a list of table names, return column metadata from table_columns table."
    )
    async def get_table_columns(self, table_names: List[str]) -> List[Dict[str, Any]]:
        """
        Input:
          table_names: List[str] - table names selected by orchestrator from table_description

        Returns:
          [
            { "table_name":"<name>", "column_name":"<col>", "description":"", "datatype":"" },
            ...
          ]

        Behavior:
          - Supports table_columns rows that have only (table_name, column_name).
          - If description/datatype columns exist, include them; otherwise return empty strings for those fields.
        """
        if not table_names:
            return []

        # Use parameterized IN-clause
        placeholders = ",".join(["?"] * len(table_names))
        query = f"SELECT * FROM table_columns WHERE table_name IN ({placeholders});"
        try:
            rows = await _query_sqlite(self.db_path, query, table_names)
            normalized = []
            for r in rows:
                # Normalize keys and provide defaults for missing fields
                row = {k: (v if v is not None else "") for k, v in r.items()}
                # Accept several possible column-name variants
                table_col = row.get("table_name") or row.get("table") or row.get("tablename") or ""
                column_col = row.get("column_name") or row.get("column") or row.get("colname") or ""
                if not table_col or not column_col:
                    # Defensive parse for single CSV-like value (e.g., "employee_data,EmpID")
                    first_vals = list(row.values())
                    if len(first_vals) == 1 and isinstance(first_vals[0], str) and "," in first_vals[0]:
                        parts = [p.strip() for p in first_vals[0].split(",")]
                        if len(parts) >= 2:
                            table_col = table_col or parts[0]
                            column_col = column_col or parts[1]
                    else:
                        # skip malformed row
                        continue

                description = row.get("description", "")
                datatype = row.get("datatype", "")
                # Ensure strings
                description = description if isinstance(description, str) else ""
                datatype = datatype if isinstance(datatype, str) else ""

                normalized.append({
                    "table_name": table_col,
                    "column_name": column_col,
                    "description": description,
                    "datatype": datatype
                })
            return normalized
        except Exception:
            # On error return empty list so orchestrator can log and handle failure
            return []

    @kernel_function(
        description="Execute the provided SQL script directly on the SQLite DB and return rows & columns."
    )
    async def execute_sql_script(self, sql: str) -> Dict[str, Any]:
        """
        VERY SIMPLE executor:
        - Executes the exact SQL string provided.
        - No safety checks, no timeouts, no parameterization, no LIMIT enforcement.
        - Returns a dict containing success, rows, columns, row_count, and optional error.

        Input:
          - sql: SQL string to execute (may be SELECT or any SQL).

        Output:
          {
            "success": True|False,
            "rows": [ {col: val, ...}, ... ],
            "columns": [ "col1", "col2", ... ],
            "row_count": int,
            "error": "<error message|null>"
          }
        """
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
        return await asyncio.to_thread(run)
