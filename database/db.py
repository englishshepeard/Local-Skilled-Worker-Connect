"""
database/db.py — Database connection and table creation.

This file is the DATA LAYER. It is the only file that talks directly
to the SQLite database. All other files must go through service
functions to reach the database.

Two functions:
  get_connection()  — Opens a connection to the database file.
  create_tables()   — Creates all four tables if they don't exist yet.
"""

import sqlite3
import os


def get_connection():
    """
    Open and return a connection to the SQLite database file.

    The database file is stored in the same folder as this script,
    named 'local_skilled_worker.db'. If the file does not exist,
    SQLite creates it automatically.

    We also turn on foreign key enforcement. SQLite has foreign keys
    OFF by default, which means it would silently ignore our
    FOREIGN KEY rules. The PRAGMA command below turns them ON.
    """

    # os.path.dirname(__file__) gives the folder where THIS script lives.
    # We join it with the database filename to get the full path.
    db_folder = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(db_folder, "local_skilled_worker.db")

    # Connect to the database (creates the file if it doesn't exist).
    # timeout=10 tells SQLite to wait up to 10 seconds if another request
    # is currently writing, avoiding "database is locked" errors.
    connection = sqlite3.connect(db_path, timeout=10)

    # Make SQLite return rows as dictionaries instead of plain tuples.
    # This lets us write row["name"] instead of row[1], which is clearer.
    connection.row_factory = sqlite3.Row

    # Turn on foreign key enforcement
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def create_tables():
    """
    Create all four tables if they do not already exist.

    'IF NOT EXISTS' means: if the table is already there, do nothing.
    So this function is safe to call every time the app starts.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # ---- Table 1: users ----
    # Stores every registered person (both customers and workers).
    # 'phone' is UNIQUE because we use it for login — no two users
    # can have the same phone number.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT    NOT NULL,
            phone          TEXT    NOT NULL UNIQUE,
            password_hash  TEXT    NOT NULL,
            salt           TEXT    NOT NULL,
            role           TEXT    NOT NULL CHECK (role IN ('customer', 'worker')),
            location       TEXT    NOT NULL
        )
    """)

    # ---- Table 2: worker_profiles ----
    # Extra information only for users whose role is 'worker'.
    # user_id is both the primary key AND a foreign key pointing to users.id.
    # is_available uses INTEGER because SQLite has no BOOLEAN type.
    # 1 means available, 0 means busy.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS worker_profiles (
            user_id           INTEGER PRIMARY KEY,
            skill             TEXT    NOT NULL,
            experience_years  INTEGER NOT NULL,
            is_available      INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # ---- Table 3: jobs ----
    # Every job posted by a customer.
    # status starts as 'Open' and moves through:
    #   Open -> Accepted -> In Progress -> Completed  (or Cancelled)
    # accepted_by is NULL until a worker accepts the job.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id            INTEGER   PRIMARY KEY AUTOINCREMENT,
            customer_id   INTEGER   NOT NULL,
            skill_needed  TEXT      NOT NULL,
            description   TEXT      NOT NULL,
            location      TEXT      NOT NULL,
            status        TEXT      NOT NULL DEFAULT 'Open',
            accepted_by   INTEGER,
            created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES users (id),
            FOREIGN KEY (accepted_by) REFERENCES users (id)
        )
    """)

    # ---- Table 4: job_broadcasts ----
    # When a job is posted, one row is created here for EACH matching
    # worker. The worker's response starts as 'Pending'.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_broadcasts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id     INTEGER NOT NULL,
            worker_id  INTEGER NOT NULL,
            response   TEXT    NOT NULL DEFAULT 'Pending',
            FOREIGN KEY (job_id)    REFERENCES jobs (id),
            FOREIGN KEY (worker_id) REFERENCES users (id)
        )
    """)

    # ---- Table 5: ratings ----
    # Stores customer ratings (1 to 5 stars) and optional reviews for
    # completed jobs. job_id is UNIQUE so each job can be rated only once.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id           INTEGER   PRIMARY KEY AUTOINCREMENT,
            job_id       INTEGER   NOT NULL UNIQUE,
            customer_id  INTEGER   NOT NULL,
            worker_id    INTEGER   NOT NULL,
            rating       INTEGER   NOT NULL CHECK (rating BETWEEN 1 AND 5),
            review       TEXT,
            created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id)      REFERENCES jobs (id),
            FOREIGN KEY (customer_id) REFERENCES users (id),
            FOREIGN KEY (worker_id)   REFERENCES users (id)
        )
    """)

    # Save all the changes to the database file
    connection.commit()

    # Close the connection (free up resources)
    connection.close()
