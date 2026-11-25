"""
services/auth_service.py — Authentication logic (register and login).

This file is the LOGIC LAYER for user registration and login.
It talks to the database through db.py and is called by app.py.

Three functions:
  hash_password()   — Hashes a password with a salt using SHA-256.
  register_user()   — Creates a new user account in the database.
  login_user()      — Checks phone + password and returns the user.
"""

import hashlib   # Built-in module for hashing (SHA-256)
import os        # Built-in module — we use os.urandom() to make a salt
import sqlite3   # Built-in module — we catch sqlite3.IntegrityError

# Import our database connection function from the data layer
from database.db import get_connection


def hash_password(password, salt):
    """
    Combine the salt and password, then hash them with SHA-256.

    How it works step by step:
      1. Glue the salt and password together: salt + password
      2. Convert that string into bytes (SHA-256 needs bytes, not text)
      3. Run SHA-256 on those bytes
      4. Convert the result to a hexadecimal string (letters + numbers)

    Parameters:
        password (str): The plain-text password the user typed.
        salt (str):     A random string unique to this user.

    Returns:
        str: The hashed password as a hexadecimal string.
    """

    # Combine salt and password into one string, then convert to bytes
    salted_password = (salt + password).encode("utf-8")

    # Hash the bytes with SHA-256 and return the hex string
    return hashlib.sha256(salted_password).hexdigest()


def register_user(name, phone, password, role, location,
                   skill=None, experience_years=None):
    """
    Create a new user account in the database.

    Steps:
      1. Generate a random salt (16 random bytes turned into hex = 32 chars)
      2. Hash the password with that salt
      3. Insert a row into the 'users' table
      4. If the role is 'worker', also insert a row into 'worker_profiles'

    Parameters:
        name (str):              Full name
        phone (str):             Phone number (must be unique)
        password (str):          Plain-text password (will be hashed)
        role (str):              'customer' or 'worker'
        location (str):          City or area
        skill (str or None):     Worker's skill (only if role is 'worker')
        experience_years (int or None): Years of experience (only if worker)

    Returns:
        tuple: (True, "Registration successful!") on success
               (False, "error message") on failure
    """

    # Generate a random salt: 16 random bytes → 32-character hex string
    # os.urandom(16) produces 16 truly random bytes.
    # .hex() converts those bytes to a readable string like "a3f7b2..."
    salt = os.urandom(16).hex()

    # Hash the password with the salt
    password_hash = hash_password(password, salt)

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Insert the new user into the 'users' table.
        # We use ? placeholders to prevent SQL injection.
        cursor.execute("""
            INSERT INTO users (name, phone, password_hash, salt, role, location)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, phone, password_hash, salt, role, location))

        # If this person is a worker, also create their worker profile.
        # cursor.lastrowid gives us the id of the row we just inserted.
        if role == "worker":
            user_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO worker_profiles (user_id, skill, experience_years)
                VALUES (?, ?, ?)
            """, (user_id, skill, experience_years))

        # Save both inserts to the database
        connection.commit()
        return (True, "Registration successful!")

    except sqlite3.IntegrityError:
        # This happens when the phone number already exists in the database
        # because we marked 'phone' as UNIQUE in the table.
        connection.rollback()
        return (False, "This phone number is already registered.")

    finally:
        # 'finally' runs no matter what — success or error.
        # Always close the connection to free resources.
        connection.close()


def login_user(phone, password):
    """
    Check if the phone number and password are correct.

    Steps:
      1. Look up the user by phone number
      2. If not found, return None
      3. If found, hash the typed password with the stored salt
      4. Compare the result with the stored password_hash
      5. If they match, return the user's data. If not, return None.

    Parameters:
        phone (str):    The phone number typed by the user.
        password (str): The plain-text password typed by the user.

    Returns:
        dict or None: A dictionary with the user's data if login succeeds,
                      or None if the phone or password is wrong.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # Look up the user by phone number (using ? placeholder)
    cursor.execute("SELECT * FROM users WHERE phone = ?", (phone,))
    row = cursor.fetchone()

    connection.close()

    # If no user has this phone number, login fails
    if row is None:
        return None

    # Hash the typed password with the stored salt
    typed_hash = hash_password(password, row["salt"])

    # Compare: if they match, login succeeds
    if typed_hash == row["password_hash"]:
        # Convert the sqlite3.Row object to a plain dictionary
        # so it's easier to store in session_state
        return dict(row)
    else:
        return None
