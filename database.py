import sqlite3
import pandas as pd

# ---------------- CONNECTION ----------------
def conn():
    return sqlite3.connect("vendors.db", check_same_thread=False)

# ---------------- USERS ----------------
def create_user_table():
    c = conn()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT
    )
    """)
    c.commit()
    c.close()

def register_user(u, p, r):
    c = conn()
    try:
        c.execute("INSERT INTO users VALUES (?, ?, ?)", (u, p, r))
        c.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        c.close()

def login_user(u, p):
    c = conn()
    res = c.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (u, p)
    ).fetchone()
    c.close()
    return res

# ---------------- VENDORS ----------------
def create_vendor_table():
    c = conn()
    c.execute("""
    CREATE TABLE IF NOT EXISTS vendors(
        vendor_id TEXT PRIMARY KEY,
        name TEXT,
        price INTEGER,
        delivery_days INTEGER,
        rating REAL,
        location TEXT,
        category TEXT
    )
    """)
    c.commit()
    c.close()

# ---------------- INITIAL LOAD ----------------
def load():
    c = conn()
    count = c.execute("SELECT COUNT(*) FROM vendors").fetchone()[0]

    if count == 0:
        df = pd.read_csv("vendors.csv")
        df.to_sql("vendors", c, if_exists="replace", index=False)

    c.close()

# ---------------- FETCH ----------------
def fetch_data():
    load()
    c = conn()
    df = pd.read_sql("SELECT * FROM vendors", c)
    c.close()
    return df

# ---------------- ADD ----------------
def add_vendor(*v):
    c = conn()
    try:
        c.execute("INSERT INTO vendors VALUES (?, ?, ?, ?, ?, ?, ?)", v)
        c.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        c.close()

# ---------------- UPDATE ----------------
def update_vendor(id, *v):
    c = conn()
    c.execute("""
    UPDATE vendors
    SET name=?, price=?, delivery_days=?, rating=?, location=?, category=?
    WHERE vendor_id=?
    """, (*v, id))
    c.commit()
    c.close()

# ---------------- DELETE ----------------
def delete_vendor(id):
    c = conn()
    c.execute("DELETE FROM vendors WHERE vendor_id=?", (id,))
    c.commit()
    c.close()

# ---------------- CSV UPLOAD ----------------
def upload_csv(f):
    c = conn()
    df = pd.read_csv(f)
    df.to_sql("vendors", c, if_exists="append", index=False)
    c.close()