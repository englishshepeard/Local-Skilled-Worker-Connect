"""
pages/3_My_Jobs.py — Page for customers to view all their posted jobs.

Shows each job's status, description, location, and — once accepted —
the assigned worker's name and phone number. Includes a Refresh button
because Streamlit does not update live when a worker accepts a job.
"""

import streamlit as st
from utils.helpers import require_role
from services.job_service import get_customer_jobs, cancel_job, submit_rating

# ---------- Page config ----------
st.set_page_config(page_title="My Jobs", layout="centered")

# ---------- Role protection ----------
user = require_role("customer")

st.title("📋 My Posted Jobs")
st.write("Track your jobs, cancel open requests, or rate completed work.")

col_refresh, col_filter = st.columns([1, 2])
with col_refresh:
    if st.button("🔄 Refresh"):
        st.rerun()
with col_filter:
    status_filter = st.selectbox(
        "Filter by Status",
        ["All", "Open", "Accepted", "In Progress", "Completed", "Cancelled"],
    )

# ---------- Fetch jobs via the service layer ----------
jobs = get_customer_jobs(user["id"])

if status_filter != "All":
    jobs = [j for j in jobs if j["status"] == status_filter]

if not jobs:
    st.info("No jobs found for the selected filter.")
else:
    for job in jobs:
        with st.container(border=True):
            st.subheader(f"Job #{job['id']} — {job['skill_needed']}")
            st.write(f"**Status:** {job['status']}")
            st.write(f"**Location:** {job['location']}")
            st.write(f"**Description:** {job['description']}")
            st.caption(f"Posted on: {job['created_at']}")

            # If a worker has accepted the job, show their contact details
            if job["worker_name"] is not None:
                st.success(
                    f"👷 **Assigned Worker:** {job['worker_name']} "
                    f"| 📞 **Phone:** {job['worker_phone']}"
                )

            # Allow customer to cancel if job is still Open
            if job["status"] == "Open":
                st.info("⏳ Waiting for an available worker to accept this job.")
                if st.button("❌ Cancel Job", key=f"cancel_{job['id']}"):
                    ok, msg = cancel_job(job["id"], user["id"])
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            # Allow customer to rate the worker once Completed
            if job["status"] == "Completed":
                if job["rating"] is not None:
                    st.write(f"⭐ **Your Rating:** {job['rating']} / 5")
                    if job["review"]:
                        st.caption(f"Review: \"{job['review']}\"")
                else:
                    with st.form(f"rate_form_{job['id']}"):
                        st.write("**Rate this worker:**")
                        rating_val = st.slider("Stars", min_value=1, max_value=5, value=5)
                        review_text = st.text_input("Short Review (optional)")
                        rate_btn = st.form_submit_button("Submit Rating")

                    if rate_btn:
                        ok, msg = submit_rating(
                            job_id=job["id"],
                            customer_id=user["id"],
                            worker_id=job["accepted_by"],
                            rating=rating_val,
                            review=review_text,
                        )
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
