import streamlit as st

def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = ""
    st.session_state.linkedin_profile = None
    st.session_state.login_mode = None
    st.rerun()
