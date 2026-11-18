import streamlit as st

from core.schema import ensure_schema
from ui.header import render_header_compact
from ui.auth_page import login_signup_page
from ui.admin_page import admin_dashboard
from ui.alumni_page import alumni_dashboard

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Alumni Management System", page_icon="🎓", layout="wide")

# ---------------- SESSION STATE DEFAULTS ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None
if "username" not in st.session_state:
    st.session_state.username = ""
if "linkedin_profile" not in st.session_state:
    st.session_state.linkedin_profile = None
if "login_mode" not in st.session_state:
    st.session_state.login_mode = None  # "alumni" / "admin" / None

# ---------------- DB SCHEMA INIT ----------------
ensure_schema()

# ---------------- UI ROUTER ----------------
render_header_compact()

if not st.session_state.logged_in:
    login_signup_page()
else:
    if st.session_state.role == "admin":
        admin_dashboard()
    else:
        alumni_dashboard()
