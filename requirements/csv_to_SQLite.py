#!/usr/bin/env python3

import os
import re
import csv
import sqlite3
from pathlib import Path
from typing import List, Tuple

# Try pandas
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except Exception:
    PANDAS_AVAILABLE = False


# ------------------ UTILITIES ------------------

def sanitize_table_name(name: str) -> str:
    name = name.lower()
    name = re.sub(r'\s+', '_', name)
    name = re.sub(r'[^0-9a-zA-Z_]', '_', name)
    name = re.sub(r'_+', '_', name).strip('_')
    if not name:
        name = "table"
    if re.match(r'^[0-9]', name):
        name = "t_" + name
    return name


def unique_table_name(conn: sqlite3.Connection, base: str) -> str:
    name = base
    i = 1
    cur = conn.cursor()
    while True:
        cur.execute("SELECT name FROM sqlite_master WHERE name=?", (name,))
        if not cur.fetchone():
            return name
        name = f"{base}_{i}"
        i += 1


def sniff_delimiter(sample: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample)
        return dialect.delimiter
    except:
        for d in [",", ";", "\t", "|"]:
            if d in sample:
                return d
        return ","


def read_csv_fallback(path: Path):
    sample = path.read_bytes()[:2048]
    try:
        sample = sample.decode("utf-8-sig", errors="replace")
    except:
        sample = sample.decode("latin-1", errors="replace")

    delimiter = sniff_delimiter(sample)

    # Try encodings
    for enc in ["utf-8-sig", "utf-8", "latin-1"]:
        try:
            with open(path, encoding=enc, errors="replace", newline="") as f:
                reader = csv.reader(f, delimiter=delimiter)
                rows = list(reader)
                break
        except:
            continue
    else:
        raise Exception(f"Cannot read CSV: {path}")

    if not rows:
        return [], []

    header = [str(x).strip() for x in rows[0]]
    data = rows[1:]

    # Normalize row length
    cols = len(header)
    cleaned = []
    for r in data:
        if len(r) < cols:
            r = r + [""] * (cols - len(r))
        cleaned.append(tuple(r[:cols]))

    return header, cleaned


# ------------------ SQL HELPERS ------------------

def create_metadata_tables(conn):
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS table_description (
            table_name TEXT PRIMARY KEY,
            description TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS table_columns (
            table_name TEXT,
            column_name TEXT
        )
    """)

    conn.commit()


def update_metadata(conn, table_name: str, columns: List[str]):
    cur = conn.cursor()

    cur.execute(
        "INSERT OR IGNORE INTO table_description(table_name, description) VALUES (?, '')",
        (table_name,)
    )

    cur.execute("DELETE FROM table_columns WHERE table_name=?", (table_name,))
    cur.executemany(
        "INSERT INTO table_columns(table_name, column_name) VALUES (?, ?)",
        [(table_name, c) for c in columns]
    )

    conn.commit()


# ------------------ CSV IMPORT ------------------

def import_with_pandas(conn, csv_path: Path, table_name: str):
    for enc in ["utf-8-sig", "utf-8", "latin-1"]:
        try:
            df = pd.read_csv(csv_path, encoding=enc)
            break
        except:
            df = None
            continue

    if df is None:
        raise Exception(f"Failed reading using pandas: {csv_path}")

    df.columns = [str(c) for c in df.columns]
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    return list(df.columns)


def import_without_pandas(conn, csv_path: Path, table_name: str):
    cols, rows = read_csv_fallback(csv_path)

    if not cols:
        cols = ["col1"]

    # clean col names
    clean_cols = []
    used = {}
    for c in cols:
        c2 = re.sub(r'[^0-9a-zA-Z_]', '_', c.strip() or "col")
        c2 = re.sub(r'_+', '_', c2)
        if c2 in used:
            used[c2] += 1
            c2 = f"{c2}_{used[c2]}"
        else:
            used[c2] = 1
        clean_cols.append(c2)

    cur = conn.cursor()
    ddl = ", ".join(f'"{c}" TEXT' for c in clean_cols)
    cur.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({ddl})')

    if rows:
        placeholders = ",".join("?" for _ in clean_cols)
        col_list = ",".join(f'"{c}"' for c in clean_cols)
        insert_sql = f'INSERT INTO "{table_name}" ({col_list}) VALUES ({placeholders})'
        cur.executemany(insert_sql, rows)

    conn.commit()
    return clean_cols


# ------------------ MAIN IMPORT LOGIC ------------------

def import_all(csv_folder: Path, sqlite_path: Path):

    conn = sqlite3.connect(sqlite_path)
    create_metadata_tables(conn)

    csv_files = sorted(csv_folder.glob("*.csv"))
    print(f"\nFound {len(csv_files)} CSV files.\n")

    for i, file in enumerate(csv_files, start=1):
        print(f"[{i}/{len(csv_files)}] Importing {file.name} ... ", end="")

        base = sanitize_table_name(file.stem)
        table_name = unique_table_name(conn, base)

        try:
            if PANDAS_AVAILABLE:
                cols = import_with_pandas(conn, file, table_name)
            else:
                cols = import_without_pandas(conn, file, table_name)

            update_metadata(conn, table_name, cols)
            print(f"OK → table '{table_name}'")

        except Exception as e:
            print(f"FAILED ({e})")

    conn.close()
    print("\nAll done!\n")


# ------------------ SCRIPT ENTRY ------------------

def main():
    print("=== CSV → SQLite Importer ===\n")

    csv_folder_input = input("Enter CSV folder path: ").strip()
    sqlite_input = input("Enter SQLite DB path (file or folder): ").strip()

    csv_folder = Path(csv_folder_input).expanduser().resolve()
    sqlite_path = Path(sqlite_input).expanduser().resolve()

    if not csv_folder.exists() or not csv_folder.is_dir():
        print("❌ CSV folder does not exist.")
        return

    # If folder → create imported_csvs.sqlite
    if sqlite_path.is_dir():
        sqlite_path = sqlite_path / "imported_csvs.sqlite"

    sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\nUsing SQLite DB: {sqlite_path}\n")
    import_all(csv_folder, sqlite_path)


if __name__ == "__main__":
    main()
