import streamlit as st

from core.db import db_exec, db_fetchone
from core.security import hash_password, check_password, validate_password
from core.linkedin_oauth import linkedin_config_ok, linkedin_auth_url, handle_linkedin_callback

def login_signup_page():
    handle_linkedin_callback()

    st.markdown("<h2 style='margin-top:0;'>🎓 Alumni Management System</h2>", unsafe_allow_html=True)

    # -------- STEP 1: PICK MODE --------
    if st.session_state.login_mode is None:
        st.subheader("Continue as")
        c1, c2 = st.columns(2)

        with c1:
            if st.button("🎓 Alumni", use_container_width=True):
                st.session_state.login_mode = "alumni"
                st.rerun()

        with c2:
            if st.button("👨‍💼 Admin", use_container_width=True):
                st.session_state.login_mode = "admin"
                st.rerun()

        st.divider()

        st.subheader("Signup (Alumni)")
        su_username = st.text_input("Choose a username", key="su_username").strip()
        su_email = st.text_input("Email", key="su_email").strip()
        su_pass = st.text_input("Password", type="password", key="su_pass").strip()
        su_confirm = st.text_input("Confirm password", type="password", key="su_confirm").strip()

        if st.button("Create account", key="btn_signup"):
            if not su_username or not su_pass:
                st.error("Username and password are required.")
                return
            if su_pass != su_confirm:
                st.error("Passwords do not match.")
                return

            err = validate_password(su_pass)
            if err:
                st.error(err)
                return

            try:
                db_exec(
                    """
                    INSERT INTO users (username, password_hash, email, role, status)
                    VALUES (:u, :p, :e, 'alumni', 'approved')
                    """,
                    {"u": su_username, "p": hash_password(su_pass), "e": su_email},
                )
                st.success("Signup successful ✅ Now click Alumni to login.")
            except Exception as e:
                st.error(f"Signup failed: {e}")

        return

    # -------- BACK BUTTON --------
    if st.button("⬅️ Back"):
        st.session_state.login_mode = None
        st.rerun()

    st.divider()

    mode = st.session_state.login_mode

    if mode == "alumni":
        st.subheader("🎓 Alumni Login")
        username = st.text_input("Username", key="al_login_username").strip()
        password = st.text_input("Password", type="password", key="al_login_password").strip()

        if st.button("Login", key="btn_login_alumni"):
            if not username or not password:
                st.error("Enter username and password.")
                return

            user = db_fetchone(
                "SELECT username, password_hash, role, status FROM users WHERE username=:u AND role='alumni'",
                {"u": username},
            )

            if not user:
                st.error("Alumni user not found.")
                return
            if user[3] != "approved":
                st.error("Your account is not approved / is blocked.")
                return

            if check_password(password, user[1]):
                st.session_state.logged_in = True
                st.session_state.role = user[2]
                st.session_state.username = user[0]
                st.rerun()
            else:
                st.error("Invalid password.")

        st.divider()
        st.markdown("**LinkedIn** (optional)")
        if linkedin_config_ok():
            st.link_button("🔗 Connect LinkedIn", linkedin_auth_url(), use_container_width=True)
        else:
            st.info("Add LINKEDIN_CLIENT_ID/SECRET/REDIRECT_URI in secrets.toml")

    elif mode == "admin":
        st.subheader("👨‍💼 Admin Login")
        username = st.text_input("Admin Username", key="ad_login_username").strip()
        password = st.text_input("Admin Password", type="password", key="ad_login_password").strip()

        if st.button("Login", key="btn_login_admin"):
            if not username or not password:
                st.error("Enter username and password.")
                return

            user = db_fetchone(
                "SELECT username, password_hash, role, status FROM users WHERE username=:u AND role='admin'",
                {"u": username},
            )

            if not user:
                st.error("Admin user not found.")
                return
            if user[3] != "approved":
                st.error("Admin account blocked.")
                return

            if check_password(password, user[1]):
                st.session_state.logged_in = True
                st.session_state.role = user[2]
                st.session_state.username = user[0]
                st.rerun()
            else:
                st.error("Invalid password.")
