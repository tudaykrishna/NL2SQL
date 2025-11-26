# schema_grounding_plugin.py
# SchemaGroundingPlugin for Semantic Kernel (updated get_table_columns to match your Table_columns schema)
#
# Replace DB_PATH placeholder below with the path to your .sqlite file before using.
#
# The Table_columns table schema you're using appears to be:
#   table_name, column_name
# (no description/datatype columns). This implementation handles that case and also
# gracefully handles the extended schema if description/datatype are present.

import sqlite3
import asyncio
from typing import List, Dict, Any, Optional
from semantic_kernel.functions import kernel_function

# ----- CONFIG: replace this with your actual sqlite path -----
DB_PATH = "path/to/your/database.sqlite"  # <-- replace me with the actual .sqlite file path
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
    Schema Grounding Plugin exposing two kernel functions:
      - get_table_descriptions(): returns all rows from Table_description table
      - get_table_columns(table_names): given a list of table names, returns column metadata from Table_columns table

    Updated to support Table_columns schema that contains only (table_name, column_name).
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH

    @kernel_function(description="Return all rows from the Table_description table (table_name + description).")
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
        description="Given a list of table names, return column metadata from Table_columns table."
    )
    async def get_table_columns(self, table_names: List[str]) -> List[Dict[str, Any]]:
        """
        Input:
          table_names: List[str] - table names selected by orchestrator from Table_description

        Returns:
          [
            { "table_name":"<name>", "column_name":"<col>", "description":"", "datatype":"" },
            ...
          ]

        Behavior:
          - Supports Table_columns rows that have only (table_name, column_name).
          - If description/datatype columns exist, include them; otherwise return empty strings for those fields.
        """
        if not table_names:
            return []

        # Use parameterized IN-clause
        placeholders = ",".join(["?"] * len(table_names))
        # Try to select known columns. If additional cols exist we'll handle them in normalization.
        query = f"SELECT * FROM table_columns WHERE table_name IN ({placeholders});"
        try:
            rows = await _query_sqlite(self.db_path, query, table_names)
            normalized = []
            for r in rows:
                # Normalize keys and provide defaults for missing fields
                row = {k: (v if v is not None else "") for k, v in r.items()}
                # Accept both lowercase/uppercase column names if DB schema differs
                table_col = row.get("table_name") or row.get("table") or row.get("tablename") or ""
                column_col = row.get("column_name") or row.get("column") or row.get("colname") or ""
                if not table_col or not column_col:
                    # If SELECT * returned a single CSV-like value, try to parse it
                    # (defensive: not expected, but safe)
                    # e.g., a single column with "employee_data,EmpID"
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
