"""
services/job_service.py — Business logic for customer jobs.

This file is the LOGIC LAYER for creating and viewing jobs.
Pages call these functions; these functions talk to SQLite via db.py.

Functions:
  create_job()         — Saves a new job with status 'Open'.
  get_customer_jobs()  — Fetches all jobs posted by a specific customer.
"""

from database.db import get_connection


def create_job(customer_id, skill_needed, description, location):
    """
    Save a new job posted by a customer with status 'Open'.

    Parameters:
        customer_id (int):  ID of the logged-in customer.
        skill_needed (str): Required skill (e.g., 'Plumber').
        description (str):  Details about the work needed.
        location (str):     City or area where the job is located.

    Returns:
        int: The ID of the newly created job.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # Insert the new job using ? placeholders to prevent SQL injection.
    # status defaults to 'Open' and created_at defaults to CURRENT_TIMESTAMP.
    cursor.execute("""
        INSERT INTO jobs (customer_id, skill_needed, description, location, status)
        VALUES (?, ?, ?, ?, 'Open')
    """, (customer_id, skill_needed, description, location))

    new_job_id = cursor.lastrowid
    connection.commit()
    connection.close()

    return new_job_id


def get_customer_jobs(customer_id):
    """
    Fetch all jobs posted by a given customer, newest first.

    Uses a LEFT JOIN with the users table on accepted_by so that if a
    worker has accepted the job, we also get the worker's name and phone.
    If no worker has accepted yet (accepted_by is NULL), worker_name and
    worker_phone will simply be None.

    Parameters:
        customer_id (int): ID of the logged-in customer.

    Returns:
        list: A list of dictionaries, one per job.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            jobs.id,
            jobs.skill_needed,
            jobs.description,
            jobs.location,
            jobs.status,
            jobs.accepted_by,
            jobs.created_at,
            users.name     AS worker_name,
            users.phone    AS worker_phone,
            ratings.rating AS rating,
            ratings.review AS review
        FROM jobs
        LEFT JOIN users   ON jobs.accepted_by = users.id
        LEFT JOIN ratings ON jobs.id = ratings.job_id
        WHERE jobs.customer_id = ?
        ORDER BY jobs.id DESC
    """, (customer_id,))

    rows = cursor.fetchall()
    connection.close()

    # Convert sqlite3.Row objects to plain dictionaries
    return [dict(row) for row in rows]


def get_worker_profile(user_id):
    """
    Fetch a worker's profile (skill, experience_years, is_available).

    Parameters:
        user_id (int): ID of the logged-in worker.

    Returns:
        dict or None: Worker profile dictionary, or None if not found.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT user_id, skill, experience_years, is_available
        FROM worker_profiles
        WHERE user_id = ?
    """, (user_id,))

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None
    return dict(row)


def update_worker_profile(user_id, skill, experience_years, is_available):
    """
    Update a worker's skill, years of experience, and availability.

    SQLite stores booleans as integers: 1 = available, 0 = busy.

    Parameters:
        user_id (int):          ID of the logged-in worker.
        skill (str):            Updated skill name.
        experience_years (int): Updated years of experience.
        is_available (bool):    True if available for jobs, False if busy.
    """

    available_int = 1 if is_available else 0

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE worker_profiles
        SET skill = ?, experience_years = ?, is_available = ?
        WHERE user_id = ?
    """, (skill, experience_years, available_int, user_id))

    connection.commit()
    connection.close()


def get_available_jobs_for_worker(skill, location):
    """
    Fetch all 'Open' jobs matching a worker's skill and location.

    Comparison on location uses LOWER(TRIM(...)) so 'Pune' and 'pune '
    still match cleanly.

    Parameters:
        skill (str):    Worker's skill (e.g., 'Plumber').
        location (str): Worker's registered city or area.

    Returns:
        list: A list of dictionaries, one per matching Open job.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            jobs.id,
            jobs.skill_needed,
            jobs.description,
            jobs.location,
            jobs.status,
            jobs.created_at,
            users.name AS customer_name
        FROM jobs
        INNER JOIN users ON jobs.customer_id = users.id
        WHERE jobs.status = 'Open'
          AND jobs.skill_needed = ?
          AND LOWER(TRIM(jobs.location)) = LOWER(TRIM(?))
        ORDER BY jobs.id DESC
    """, (skill, location))

    rows = cursor.fetchall()
    connection.close()

    return [dict(row) for row in rows]


def get_worker_jobs(worker_id):
    """
    Fetch all jobs accepted by a specific worker, newest first.

    Joins with users on customer_id so the worker can see the
    customer's name and phone number to coordinate the work.

    Parameters:
        worker_id (int): ID of the logged-in worker.

    Returns:
        list: A list of dictionaries, one per accepted job.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            jobs.id,
            jobs.skill_needed,
            jobs.description,
            jobs.location,
            jobs.status,
            jobs.created_at,
            users.name  AS customer_name,
            users.phone AS customer_phone
        FROM jobs
        INNER JOIN users ON jobs.customer_id = users.id
        WHERE jobs.accepted_by = ?
        ORDER BY jobs.id DESC
    """, (worker_id,))

    rows = cursor.fetchall()
    connection.close()

    return [dict(row) for row in rows]


def cancel_job(job_id, customer_id):
    """
    Cancel an 'Open' job posted by the customer and expire its Pending broadcasts.

    Only jobs with status 'Open' can be cancelled by the customer.

    Parameters:
        job_id (int):      ID of the job to cancel.
        customer_id (int): ID of the logged-in customer.

    Returns:
        tuple: (True, success_message) or (False, error_message)
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("BEGIN IMMEDIATE")

        cursor.execute("""
            SELECT status, customer_id
            FROM jobs
            WHERE id = ?
        """, (job_id,))
        job = cursor.fetchone()

        if job is None or job["customer_id"] != customer_id:
            connection.rollback()
            return (False, "Job not found.")

        if job["status"] != "Open":
            connection.rollback()
            return (False, "Only 'Open' jobs can be cancelled.")

        cursor.execute("""
            UPDATE jobs
            SET status = 'Cancelled'
            WHERE id = ?
        """, (job_id,))

        cursor.execute("""
            UPDATE job_broadcasts
            SET response = 'Expired'
            WHERE job_id = ? AND response = 'Pending'
        """, (job_id,))

        connection.commit()
        return (True, f"Job #{job_id} has been cancelled.")

    except Exception:
        connection.rollback()
        return (False, "Could not cancel the job. Please try again.")

    finally:
        connection.close()


def update_job_status(job_id, worker_id, new_status):
    """
    Move an accepted job through its lifecycle:
      Accepted -> In Progress -> Completed

    Only the worker assigned to the job (accepted_by) can update it.

    Parameters:
        job_id (int):     ID of the job.
        worker_id (int):  ID of the logged-in worker.
        new_status (str): 'In Progress' or 'Completed'.

    Returns:
        tuple: (True, success_message) or (False, error_message)
    """

    allowed_transitions = {
        "Accepted": "In Progress",
        "In Progress": "Completed",
    }

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT status, accepted_by
        FROM jobs
        WHERE id = ?
    """, (job_id,))
    job = cursor.fetchone()

    if job is None or job["accepted_by"] != worker_id:
        connection.close()
        return (False, "Job not found or not assigned to you.")

    expected_next = allowed_transitions.get(job["status"])
    if expected_next != new_status:
        connection.close()
        return (False, f"Cannot change status from '{job['status']}' to '{new_status}'.")

    cursor.execute("""
        UPDATE jobs
        SET status = ?
        WHERE id = ?
    """, (new_status, job_id))

    connection.commit()
    connection.close()
    return (True, f"Job #{job_id} marked as '{new_status}'.")


def submit_rating(job_id, customer_id, worker_id, rating, review):
    """
    Save a 1-5 star rating and optional review for a Completed job.

    Parameters:
        job_id (int):      ID of the completed job.
        customer_id (int): ID of the customer who posted it.
        worker_id (int):   ID of the worker who completed it.
        rating (int):      Integer from 1 to 5.
        review (str):      Optional short feedback text.

    Returns:
        tuple: (True, success_message) or (False, error_message)
    """

    if rating < 1 or rating > 5:
        return (False, "Rating must be between 1 and 5.")

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT status, customer_id, accepted_by
            FROM jobs
            WHERE id = ?
        """, (job_id,))
        job = cursor.fetchone()

        if job is None or job["customer_id"] != customer_id:
            return (False, "Job not found.")

        if job["status"] != "Completed":
            return (False, "You can only rate a job after it is Completed.")

        cursor.execute("""
            INSERT INTO ratings (job_id, customer_id, worker_id, rating, review)
            VALUES (?, ?, ?, ?, ?)
        """, (job_id, customer_id, worker_id, int(rating), review.strip()))

        connection.commit()
        return (True, "Thank you! Your rating has been saved.")

    except Exception:
        connection.rollback()
        return (False, "You have already rated this job.")

    finally:
        connection.close()


def get_worker_rating_summary(worker_id):
    """
    Calculate the average rating and total number of reviews for a worker.

    Parameters:
        worker_id (int): ID of the worker.

    Returns:
        dict: {'avg_rating': float or None, 'total_reviews': int}
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            AVG(rating) AS avg_rating,
            COUNT(*)    AS total_reviews
        FROM ratings
        WHERE worker_id = ?
    """, (worker_id,))

    row = cursor.fetchone()
    connection.close()

    if row["total_reviews"] == 0:
        return {"avg_rating": None, "total_reviews": 0}

    return {
        "avg_rating": round(row["avg_rating"], 1),
        "total_reviews": row["total_reviews"],
    }
