"""
utils/helpers.py — Shared helper functions for all Streamlit pages.

Contains:
  SKILLS             — Standard list of skilled trades used across the app.
  show_sidebar_user() — Displays logged-in user info and Logout button.
  require_role()     — Checks login and role; blocks access if wrong.
"""

import streamlit as st

# Standard list of skills supported by the platform
SKILLS = [
    "Plumber",
    "Electrician",
    "Painter",
    "Roofer",
    "Carpenter",
    "Tile Worker",
]


def show_sidebar_user():
    """
    Display the logged-in user's details and a Logout button in the sidebar.
    """

    user = st.session_state["user"]

    with st.sidebar:
        st.write(f"👤 **{user['name']}**")
        st.write(f"Role: {user['role'].title()}")
        st.write(f"📍 {user['location']}")

        # Logout clears session_state and returns to the login screen
        if st.button("Logout", key="sidebar_logout"):
            del st.session_state["user"]
            st.rerun()


def require_role(expected_role):
    """
    Protect a page so only logged-in users with the right role can see it.

    If the user is not logged in, or has a different role, this function
    shows a clear message and stops the page immediately using st.stop().

    Parameters:
        expected_role (str): 'customer' or 'worker'

    Returns:
        dict: The logged-in user's dictionary from st.session_state.
    """

    # Step 1: Check if anyone is logged in
    if "user" not in st.session_state:
        st.warning("Please log in on the Home page first.")
        st.stop()

    user = st.session_state["user"]

    # Step 2: Check if the logged-in user has the expected role
    if user["role"] != expected_role:
        st.error(
            f"Access denied: This page is for {expected_role}s only. "
            f"You are logged in as a {user['role']}."
        )
        st.stop()

    # Step 3: Show user info in the sidebar and return the user dict
    show_sidebar_user()
    return user
