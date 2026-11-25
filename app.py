"""
app.py — Main entry point for Local Skilled Worker Connect.

This is the PRESENTATION LAYER (what the user sees).
It handles:
  - Creating the database tables on first run
  - Registration form (for new users)
  - Login form (for existing users)
  - Logout
  - Showing a welcome dashboard based on the user's role

It NEVER talks to the database directly. It calls service functions
from auth_service.py, which talk to the database through db.py.

st.session_state is a special Streamlit dictionary that survives
page reruns. We store the logged-in user's info here.
"""

import streamlit as st

# Import our logic-layer functions
from database.db import create_tables
from services.auth_service import register_user, login_user
from utils.helpers import SKILLS, show_sidebar_user

# ---------- Page configuration ----------
# Must be the first Streamlit command. Sets browser tab title.
st.set_page_config(
    page_title="Local Skilled Worker Connect",
    layout="centered"
)

# ---------- Create database tables on first run ----------
# This runs every time the script reruns, but create_tables() uses
# 'IF NOT EXISTS', so it only actually creates tables the first time.
create_tables()


def show_registration_form():
    """
    Display the registration form and handle sign-up.

    Uses st.form() so that all the inputs are submitted together
    when the user clicks the Register button (instead of rerunning
    the page on every keystroke).
    """

    st.subheader("📝 Create a New Account")

    # st.form groups inputs together — the page only reruns when
    # the user clicks the submit button, not on every keystroke.
    with st.form("register_form"):

        # Text input fields
        name = st.text_input("Full Name")
        phone = st.text_input("Phone Number")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        # Role selection — radio buttons
        role = st.radio("I am a:", ["customer", "worker"])

        # Location
        location = st.text_input("Your City / Area")

        # If the user chose 'worker', show extra fields
        # We always show these but they only matter if role == 'worker'
        st.markdown("---")
        st.write("**Worker details** *(fill only if you are a worker)*")
        skill = st.selectbox("Your Skill", SKILLS)
        experience_years = st.number_input(
            "Years of Experience", min_value=0, max_value=50, value=0
        )

        # The submit button
        submitted = st.form_submit_button("Register")

    # --- Handle form submission (this runs only when button is clicked) ---
    if submitted:

        # --- Input validation ---
        # Check that no field is left empty
        if not name.strip():
            st.error("Please enter your name.")
            return

        if not phone.strip():
            st.error("Please enter your phone number.")
            return

        # Check phone is digits only and between 10-15 characters
        if not phone.strip().isdigit() or len(phone.strip()) < 10 or len(phone.strip()) > 15:
            st.error("Phone number must be 10-15 digits (numbers only).")
            return

        if not password:
            st.error("Please enter a password.")
            return

        if len(password) < 4:
            st.error("Password must be at least 4 characters long.")
            return

        if password != confirm_password:
            st.error("Passwords do not match. Please try again.")
            return

        if not location.strip():
            st.error("Please enter your city or area.")
            return

        # If worker, check that experience is provided
        if role == "worker" and experience_years < 0:
            st.error("Experience years cannot be negative.")
            return

        # --- Call the service function to register ---
        # The presentation layer calls the logic layer (never the DB directly)
        if role == "worker":
            success, message = register_user(
                name.strip(), phone.strip(), password, role,
                location.strip(), skill, experience_years
            )
        else:
            success, message = register_user(
                name.strip(), phone.strip(), password, role,
                location.strip()
            )

        # Show the result to the user
        if success:
            st.success(message + " You can now log in.")
        else:
            st.error(message)


def show_login_form():
    """
    Display the login form and handle sign-in.

    On successful login, stores the user's info in st.session_state
    so the app remembers who is logged in across page reruns.
    """

    st.subheader("🔑 Log In to Your Account")

    with st.form("login_form"):
        phone = st.text_input("Phone Number")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In")

    if submitted:
        # --- Input validation ---
        if not phone.strip():
            st.error("Please enter your phone number.")
            return

        if not password:
            st.error("Please enter your password.")
            return

        # --- Call the service function to verify login ---
        user = login_user(phone.strip(), password)

        if user is not None:
            # Login succeeded! Store user info in session_state.
            # session_state survives page reruns, so the app remembers
            # the user until they log out or close the browser.
            st.session_state["user"] = user
            st.success(f"Welcome back, {user['name']}!")

            # Rerun the page so the logged-in view appears immediately
            st.rerun()
        else:
            st.error("Invalid phone number or password.")


def show_logged_in_view():
    """
    Show the dashboard for a logged-in user.

    Displays a welcome message, the user's details, and a logout button.
    The content changes based on whether the user is a customer or worker.
    """

    # Get the stored user info from session_state
    user = st.session_state["user"]

    # --- Sidebar: user info and logout ---
    show_sidebar_user()

    # --- Main content ---
    st.title("🔧 Local Skilled Worker Connect")

    if user["role"] == "customer":
        st.write(f"Welcome, **{user['name']}**! You are logged in as a **Customer**.")
        st.info("👈 Use the sidebar pages to post jobs and track your requests.")

    elif user["role"] == "worker":
        st.write(f"Welcome, **{user['name']}**! You are logged in as a **Worker**.")
        st.info("👈 Use the sidebar pages to view available jobs and manage your work.")


# ============================================================
# MAIN APP LOGIC — This runs every time the page loads or reruns
# ============================================================

# Check if a user is already logged in (stored in session_state)
if "user" in st.session_state:
    # User is logged in → show the dashboard
    show_logged_in_view()

else:
    # No one is logged in → show login and register forms
    st.title("🔧 Local Skilled Worker Connect")
    st.write("Connect with local skilled workers in your area.")

    # Create two tabs: one for Login, one for Register
    tab_login, tab_register = st.tabs(["🔑 Login", "📝 Register"])

    with tab_login:
        show_login_form()

    with tab_register:
        show_registration_form()
