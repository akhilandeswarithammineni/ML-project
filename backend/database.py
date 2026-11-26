
import sqlite3


def init_db():
    conn = sqlite3.connect("load_sentinel.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            meter TEXT,
            reading REAL,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_results(results):
    conn = sqlite3.connect("load_sentinel.db")

    for item in results:
        conn.execute("""
            INSERT INTO anomalies (timestamp, meter, reading, status)
            VALUES (?, ?, ?, ?)
        """, (
            item["timestamp"],
            item["meter"],
            item["reading"],
            item["status"]
        ))

    conn.commit()
    conn.close()

