import requests
import streamlit as st

def _sec(name, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default

LINKEDIN_CLIENT_ID = _sec("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = _sec("LINKEDIN_CLIENT_SECRET", "")
LINKEDIN_REDIRECT_URI = _sec("LINKEDIN_REDIRECT_URI", "http://localhost:8501/?oauth=linkedin")

def linkedin_config_ok() -> bool:
    return bool(LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET and LINKEDIN_REDIRECT_URI)

def linkedin_auth_url():
    scope = "openid profile email"
    return (
        "https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={LINKEDIN_CLIENT_ID}"
        f"&redirect_uri={requests.utils.quote(LINKEDIN_REDIRECT_URI, safe='')}"
        f"&scope={requests.utils.quote(scope)}"
        f"&state=alumni_oauth_state"
    )

def linkedin_exchange_code_for_token(code: str):
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "client_id": LINKEDIN_CLIENT_ID,
        "client_secret": LINKEDIN_CLIENT_SECRET,
    }
    r = requests.post(token_url, data=data, timeout=20)
    r.raise_for_status()
    return r.json()["access_token"]

def linkedin_fetch_userinfo(access_token: str):
    r = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()

def handle_linkedin_callback():
    qp = st.query_params
    if "oauth" in qp and qp.get("oauth") == "linkedin" and "code" in qp:
        if not linkedin_config_ok():
            st.error("LinkedIn not configured in secrets.toml")
            return
        code = qp.get("code")
        try:
            token = linkedin_exchange_code_for_token(code)
            info = linkedin_fetch_userinfo(token)
            st.session_state.linkedin_profile = info
            st.query_params.clear()
            st.success("LinkedIn connected ✅")
            st.rerun()
        except Exception as e:
            st.error(f"LinkedIn OAuth failed: {e}")
