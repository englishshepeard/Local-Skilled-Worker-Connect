"""
pages/1_Customer_Dashboard.py — Customer home dashboard.

Shows a quick summary of the customer's jobs (total, open, active, completed)
and guides them to Post Job or My Jobs.
"""

import streamlit as st
from utils.helpers import require_role
from services.job_service import get_customer_jobs

# ---------- Page config ----------
st.set_page_config(page_title="Customer Dashboard", layout="centered")

# ---------- Role protection ----------
# Only logged-in customers can view this page
user = require_role("customer")

# ---------- Header and Refresh button ----------
st.title("🏠 Customer Dashboard")
st.write(f"Hello, **{user['name']}**! Manage your service requests from here.")

if st.button("🔄 Refresh"):
    st.rerun()

# ---------- Fetch customer's jobs via the service layer ----------
jobs = get_customer_jobs(user["id"])

# Count jobs by status so the customer gets a quick overview
total_jobs = len(jobs)
open_jobs = len([j for j in jobs if j["status"] == "Open"])
active_jobs = len([j for j in jobs if j["status"] in ("Accepted", "In Progress")])
completed_jobs = len([j for j in jobs if j["status"] == "Completed"])

# ---------- Summary metrics ----------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Jobs", total_jobs)
col2.metric("Open", open_jobs)
col3.metric("In Progress", active_jobs)
col4.metric("Completed", completed_jobs)

st.markdown("---")
st.subheader("What would you like to do?")
st.write("- **Post Job** (in the sidebar): Request a plumber, electrician, painter, etc.")
st.write("- **My Jobs** (in the sidebar): Check job status and see your assigned worker's phone number.")
