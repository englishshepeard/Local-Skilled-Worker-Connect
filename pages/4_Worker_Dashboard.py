"""
pages/4_Worker_Dashboard.py — Worker home dashboard and profile settings.

Allows a logged-in worker to:
  - View a quick summary of their active and completed jobs
  - Toggle their availability (Available vs. Busy)
  - Update their skill and years of experience
"""

import streamlit as st
from utils.helpers import require_role, SKILLS
from services.job_service import (
    get_worker_profile,
    update_worker_profile,
    get_worker_jobs,
    get_worker_rating_summary,
)

# ---------- Page config ----------
st.set_page_config(page_title="Worker Dashboard", layout="centered")

# ---------- Role protection ----------
user = require_role("worker")

st.title("👷 Worker Dashboard")
st.write(f"Hello, **{user['name']}**! Manage your profile and availability here.")

if st.button("🔄 Refresh"):
    st.rerun()

# ---------- Fetch worker profile and jobs ----------
profile = get_worker_profile(user["id"])
my_jobs = get_worker_jobs(user["id"])

if profile is None:
    st.error("Worker profile not found. Please contact support or re-register.")
    st.stop()

# Count active and completed jobs, and fetch rating summary
active_count = len([j for j in my_jobs if j["status"] in ("Accepted", "In Progress")])
completed_count = len([j for j in my_jobs if j["status"] == "Completed"])
status_text = "Available ✅" if profile["is_available"] == 1 else "Busy 🔴"
rating_summary = get_worker_rating_summary(user["id"])

if rating_summary["avg_rating"] is not None:
    rating_text = f"{rating_summary['avg_rating']} / 5 ({rating_summary['total_reviews']})"
else:
    rating_text = "No ratings yet"

# ---------- Summary metrics ----------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Status", status_text)
col2.metric("Active Jobs", active_count)
col3.metric("Completed", completed_count)
col4.metric("Avg Rating", rating_text)

st.markdown("---")
st.subheader("⚙️ Update Profile & Availability")

# Find the index of the worker's current skill so the dropdown pre-selects it
if profile["skill"] in SKILLS:
    skill_index = SKILLS.index(profile["skill"])
else:
    skill_index = 0

with st.form("worker_profile_form"):
    is_available = st.checkbox(
        "I am available to receive new job requests",
        value=(profile["is_available"] == 1),
    )
    skill = st.selectbox("Your Skill", SKILLS, index=skill_index)
    experience_years = st.number_input(
        "Years of Experience",
        min_value=0,
        max_value=50,
        value=int(profile["experience_years"]),
    )

    saved = st.form_submit_button("Save Changes")

if saved:
    if experience_years < 0:
        st.error("Experience years cannot be negative.")
    else:
        update_worker_profile(
            user_id=user["id"],
            skill=skill,
            experience_years=int(experience_years),
            is_available=is_available,
        )
        st.success("Profile updated successfully!")
        st.rerun()
