"""
pages/2_Post_Job.py — Page for customers to post a new job.

Collects the required skill, job description, and location, validates them,
and calls job_service.create_job() to save the job in SQLite.
"""

import streamlit as st
from utils.helpers import require_role, SKILLS
from services.job_service import create_job
from services.allocation_service import broadcast_job

# ---------- Page config ----------
st.set_page_config(page_title="Post a Job", layout="centered")

# ---------- Role protection ----------
user = require_role("customer")

st.title("➕ Post a New Job")
st.write("Describe the work you need done so local skilled workers can help.")

# ---------- Job creation form ----------
with st.form("post_job_form"):
    skill_needed = st.selectbox("Skill Needed", SKILLS)
    description = st.text_area(
        "Job Description",
        placeholder="Example: Kitchen sink pipe is leaking and needs repair."
    )
    # Pre-fill location with the customer's registered city/area
    location = st.text_input("Job Location (City / Area)", value=user["location"])

    submitted = st.form_submit_button("Post Job")

# ---------- Handle form submission ----------
if submitted:
    # Validate inputs before saving
    if not description.strip():
        st.error("Please enter a description of the job.")
    elif len(description.strip()) < 10:
        st.error("Please provide a slightly more detailed description (at least 10 characters).")
    elif not location.strip():
        st.error("Please enter the job location.")
    else:
        # Call the logic layer to save the job and broadcast to matching workers
        job_id = create_job(
            customer_id=user["id"],
            skill_needed=skill_needed,
            description=description.strip(),
            location=location.strip(),
        )
        notified_count = broadcast_job(job_id, skill_needed, location.strip())

        st.success(f"Job #{job_id} posted successfully with status 'Open'!")
        if notified_count > 0:
            st.info(f"📢 Broadcast sent to **{notified_count}** available worker(s) in {location.strip()}.")
        else:
            st.warning("No available workers matched right now, but your job is saved as Open.")
        st.info("Go to **My Jobs** in the sidebar to track your request.")
