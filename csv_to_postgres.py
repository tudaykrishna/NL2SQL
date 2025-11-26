"""
csv_to_postgres.py

Usage:
    python csv_to_postgres.py C:/Users/MZ933GN/Downloads/archive postgresql://user:pass@host:port/dbname

What it does:
- Reads all .csv files in the given folder
- For each CSV:
    - creates/replaces a table named after the filename (lowercase, non-alphanum replaced with _)
    - loads the CSV rows into that table
- Creates/updates two metadata tables:
    - table_descriptions(table_name TEXT PRIMARY KEY, description TEXT)
      (description left blank)
    - table_columns(id SERIAL PRIMARY KEY, table_name TEXT, column_name TEXT, data_type TEXT, ordinal_position INT)
"""

import sys
import os
import re
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# ---- helpers ----
def sanitize_table_name(name: str) -> str:
    """Lowercase, replace non-alphanumeric with underscore, trim underscores."""
    name = name.lower()
    name = re.sub(r'[^a-z0-9]+', '_', name)
    name = re.sub(r'^_+|_+$', '', name)
    if not name:
        name = 'table'
    return name

def infer_sql_type(pd_series: pd.Series) -> str:
    """Return a human-friendly SQL type name inferred from a pandas Series dtype."""
    # Keep it simple — store a generic text/numeric mapping. PostgreSQL accepts these.
    if pd.api.types.is_integer_dtype(pd_series):
        return 'INTEGER'
    if pd.api.types.is_float_dtype(pd_series):
        return 'DOUBLE PRECISION'
    if pd.api.types.is_bool_dtype(pd_series):
        return 'BOOLEAN'
    if pd.api.types.is_datetime64_any_dtype(pd_series):
        return 'TIMESTAMP'
    # fallback: length-aware TEXT or VARCHAR
    max_len = None
    try:
        max_len = pd_series.dropna().astype(str).map(len).max()
    except Exception:
        max_len = None
    if max_len is not None and max_len <= 255:
        return f'VARCHAR({max_len})'
    return 'TEXT'

# ---- main ----
def main(csv_folder: str, db_url: str):
    folder = Path(csv_folder)
    if not folder.exists() or not folder.is_dir():
        print(f"ERROR: folder not found: {csv_folder}")
        return

    # Create SQLAlchemy engine
    engine = create_engine(db_url, future=True)

    # Prepare metadata table names
    desc_table = 'table_descriptions'
    cols_table = 'table_columns'

    # Create metadata tables if not exist
    create_meta_sql = f"""
    CREATE TABLE IF NOT EXISTS {desc_table} (
        table_name TEXT PRIMARY KEY,
        description TEXT
    );
    CREATE TABLE IF NOT EXISTS {cols_table} (
        id SERIAL PRIMARY KEY,
        table_name TEXT NOT NULL,
        column_name TEXT NOT NULL,
        data_type TEXT,
        ordinal_position INT
    );
    """
    with engine.begin() as conn:
        conn.execute(text(create_meta_sql))

    # Iterate CSV files
    csv_files = sorted(folder.glob("*.csv"))
    if not csv_files:
        print("No CSV files found in folder.")
        return

    processed_tables = []

    for csv_path in csv_files:
        try:
            print(f"Processing file: {csv_path.name}")
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f"  Failed to read {csv_path.name}: {e}")
            continue

        table_name = sanitize_table_name(csv_path.stem)
        if not table_name:
            table_name = f"table_{csv_path.stem}"

        # Write dataframe to SQL (replace existing table)
        try:
            # pandas.to_sql uses SQLAlchemy. if_exists='replace' will drop+create
            df.to_sql(table_name, engine, if_exists='replace', index=False, method='multi')
            print(f"  Created/updated table `{table_name}` with {len(df)} rows and {len(df.columns)} columns.")
        except SQLAlchemyError as e:
            print(f"  Failed to create table {table_name}: {e}")
            continue

        processed_tables.append((table_name, df))

        # Upsert into table_descriptions (leave description blank if new)
        with engine.begin() as conn:
            upsert_sql = f"""
            INSERT INTO {desc_table}(table_name, description)
            VALUES (:tname, '')
            ON CONFLICT (table_name) DO NOTHING;
            """
            conn.execute(text(upsert_sql), {"tname": table_name})

        # Remove previous column entries for this table and insert fresh ones
        with engine.begin() as conn:
            conn.execute(text(f"DELETE FROM {cols_table} WHERE table_name = :tname"), {"tname": table_name})
            # Insert each column with inferred type
            for pos, col in enumerate(df.columns, start=1):
                dtype = infer_sql_type(df[col])
                insert_col_sql = f"""
                INSERT INTO {cols_table}(table_name, column_name, data_type, ordinal_position)
                VALUES (:tname, :colname, :dtype, :pos)
                """
                conn.execute(text(insert_col_sql), {"tname": table_name, "colname": str(col), "dtype": dtype, "pos": pos})

    # Summary
    print("\nFinished. Summary of processed tables:")
    for tname, df in processed_tables:
        print(f" - {tname}: {len(df)} rows, columns: {list(df.columns)}")

    print(f"\nMetadata tables created/updated: {desc_table}, {cols_table}")
    print("You can now connect to your DB and fill descriptions in 'table_descriptions' as needed.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python csv_to_postgres.py /path/to/csv_folder postgresql://user:pass@host:port/dbname")
        sys.exit(1)
    csv_folder = sys.argv[1]
    db_url = sys.argv[2]
    main(csv_folder, db_url)
