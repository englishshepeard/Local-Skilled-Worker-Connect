"""
pages/6_My_Work.py — Shows all jobs accepted by this worker.

Displays the customer's name, phone number, location, description,
and current job status. Includes a Refresh button.
"""

import streamlit as st
from utils.helpers import require_role
from services.job_service import get_worker_jobs, update_job_status

# ---------- Page config ----------
st.set_page_config(page_title="My Work", layout="centered")

# ---------- Role protection ----------
user = require_role("worker")

st.title("🧰 My Work")
st.write("Manage your accepted jobs, update work progress, and view history.")

col_refresh, col_filter = st.columns([1, 2])
with col_refresh:
    if st.button("🔄 Refresh"):
        st.rerun()
with col_filter:
    status_filter = st.selectbox(
        "Filter by Status",
        ["All", "Accepted", "In Progress", "Completed"],
    )

# ---------- Fetch accepted jobs via the service layer ----------
jobs = get_worker_jobs(user["id"])

if status_filter != "All":
    jobs = [j for j in jobs if j["status"] == status_filter]

if not jobs:
    st.info("No jobs found for the selected filter.")
else:
    for job in jobs:
        with st.container(border=True):
            st.subheader(f"Job #{job['id']} — {job['skill_needed']}")
            st.write(f"**Status:** {job['status']}")
            st.write(f"**Customer:** {job['customer_name']} | 📞 **Phone:** {job['customer_phone']}")
            st.write(f"**Location:** {job['location']}")
            st.write(f"**Description:** {job['description']}")
            st.caption(f"Posted on: {job['created_at']}")

            # Status progression buttons
            if job["status"] == "Accepted":
                if st.button("🔨 Start Work (In Progress)", key=f"start_{job['id']}"):
                    ok, msg = update_job_status(job["id"], user["id"], "In Progress")
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            elif job["status"] == "In Progress":
                if st.button("🎉 Mark Completed", key=f"complete_{job['id']}"):
                    ok, msg = update_job_status(job["id"], user["id"], "Completed")
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
