"""
pages/5_Available_Jobs.py — Shows matching Open jobs for the worker.

Checks the worker's skill, location, and availability.
In Stage 5, we will connect this page to job_broadcasts and add
the Accept button inside a single database transaction.
"""

import streamlit as st
from utils.helpers import require_role
from services.job_service import get_worker_profile
from services.allocation_service import get_broadcast_jobs_for_worker, accept_job

# ---------- Page config ----------
st.set_page_config(page_title="Available Jobs", layout="centered")

# ---------- Role protection ----------
user = require_role("worker")

st.title("📢 Available Jobs")
st.write("Jobs matching your skill and city appear here. Click **Refresh** to check for new jobs.")

if st.button("🔄 Refresh"):
    st.rerun()

# ---------- Check worker profile & availability ----------
profile = get_worker_profile(user["id"])

if profile is None:
    st.error("Worker profile not found.")
    st.stop()

st.caption(f"Showing **{profile['skill']}** jobs in **{user['location']}**")

# If worker marked themselves as Busy, remind them
if profile["is_available"] == 0:
    st.warning(
        "You are currently marked as **Busy**. "
        "Go to **Worker Dashboard** and turn on availability to receive new jobs."
    )
    st.stop()

# ---------- Fetch Pending broadcast jobs for this worker ----------
jobs = get_broadcast_jobs_for_worker(user["id"])

if not jobs:
    st.info("No matching open jobs in your area right now. Check back soon!")
else:
    for job in jobs:
        with st.container(border=True):
            st.subheader(f"Job #{job['id']} — {job['skill_needed']}")
            st.write(f"**Customer:** {job['customer_name']}")
            st.write(f"**Location:** {job['location']}")
            st.write(f"**Description:** {job['description']}")
            st.caption(f"Posted on: {job['created_at']}")

            # Each button needs a unique key so Streamlit tracks them separately
            if st.button("✅ Accept Job", key=f"accept_{job['id']}"):
                success, message = accept_job(job["id"], user["id"])
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
