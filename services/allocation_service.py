"""
services/allocation_service.py — Broadcast job allocation logic.

This file is the LOGIC LAYER for the core feature:
  1. Broadcast a new job to all matching, available workers.
  2. Show a worker only their Pending broadcasts for Open jobs.
  3. Let the first worker who clicks Accept claim the job safely
     inside a single database transaction.
"""

from database.db import get_connection


def broadcast_job(job_id, skill_needed, location):
    """
    Find all matching available workers and create a 'Pending' broadcast
    row for each one in job_broadcasts.

    Matching rules:
      - users.role = 'worker'
      - worker_profiles.skill = skill_needed
      - worker_profiles.is_available = 1
      - users.location matches job location (case-insensitive, trimmed)

    Parameters:
        job_id (int):       ID of the newly created job.
        skill_needed (str): Required skill.
        location (str):     Job city or area.

    Returns:
        int: Number of matching workers notified.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # Step 1: Find all matching available workers
    cursor.execute("""
        SELECT users.id
        FROM users
        INNER JOIN worker_profiles ON users.id = worker_profiles.user_id
        WHERE users.role = 'worker'
          AND worker_profiles.skill = ?
          AND worker_profiles.is_available = 1
          AND LOWER(TRIM(users.location)) = LOWER(TRIM(?))
    """, (skill_needed, location))

    matching_workers = cursor.fetchall()

    # Step 2: Insert one 'Pending' broadcast row per matching worker
    for worker in matching_workers:
        cursor.execute("""
            INSERT INTO job_broadcasts (job_id, worker_id, response)
            VALUES (?, ?, 'Pending')
        """, (job_id, worker["id"]))

    connection.commit()
    connection.close()

    return len(matching_workers)


def get_broadcast_jobs_for_worker(worker_id):
    """
    Fetch all 'Pending' broadcasts for a worker where the job is still 'Open'.

    Parameters:
        worker_id (int): ID of the logged-in worker.

    Returns:
        list: List of dictionaries with job and customer details.
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
        FROM job_broadcasts
        INNER JOIN jobs ON job_broadcasts.job_id = jobs.id
        INNER JOIN users ON jobs.customer_id = users.id
        WHERE job_broadcasts.worker_id = ?
          AND job_broadcasts.response = 'Pending'
          AND jobs.status = 'Open'
        ORDER BY jobs.id DESC
    """, (worker_id,))

    rows = cursor.fetchall()
    connection.close()

    return [dict(row) for row in rows]


def accept_job(job_id, worker_id):
    """
    Attempt to accept a job inside ONE atomic database transaction.

    Why BEGIN IMMEDIATE?
      It locks the database for writing immediately so two workers
      clicking Accept at the exact same moment cannot both claim the
      same job. The second worker will wait, see status != 'Open',
      and get "Sorry, this job was already taken."

    Steps:
      1. Start a transaction with BEGIN IMMEDIATE.
      2. Check that the job's status is still 'Open'.
      3. If NOT 'Open': rollback and return (False, error message).
      4. If 'Open':
           - Update jobs: status = 'Accepted', accepted_by = worker_id
           - Update this worker's broadcast: response = 'Accepted'
           - Update all other workers' broadcasts for this job: response = 'Expired'
           - Commit the transaction.

    Parameters:
        job_id (int):    ID of the job being accepted.
        worker_id (int): ID of the worker clicking Accept.

    Returns:
        tuple: (True, success_message) or (False, error_message)
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Start an immediate write transaction
        cursor.execute("BEGIN IMMEDIATE")

        # Step 1: Check current status of the job
        cursor.execute("SELECT status FROM jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()

        if job is None or job["status"] != "Open":
            connection.rollback()
            return (False, "Sorry, this job was already taken.")

        # Step 2: Claim the job in the jobs table
        cursor.execute("""
            UPDATE jobs
            SET status = 'Accepted', accepted_by = ?
            WHERE id = ?
        """, (worker_id, job_id))

        # Step 3: Mark this worker's broadcast as 'Accepted'
        cursor.execute("""
            UPDATE job_broadcasts
            SET response = 'Accepted'
            WHERE job_id = ? AND worker_id = ?
        """, (job_id, worker_id))

        # Step 4: Mark all other workers' broadcasts for this job as 'Expired'
        cursor.execute("""
            UPDATE job_broadcasts
            SET response = 'Expired'
            WHERE job_id = ? AND worker_id != ?
        """, (job_id, worker_id))

        # Step 5: Save all 3 updates together
        connection.commit()
        return (True, "Job accepted! Go to My Work to see customer details.")

    except Exception:
        # If anything unexpected goes wrong, undo all partial changes
        connection.rollback()
        return (False, "Could not accept the job due to a database error. Please try again.")

    finally:
        connection.close()
