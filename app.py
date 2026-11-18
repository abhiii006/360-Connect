import os
import re
import html
import base64
import bcrypt
import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from PIL import Image
import socket
import subprocess
import threading
import time

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# ---------------- GD PREPARATION BACKGROUND SERVICE ----------------
def is_gd_service_ready(port=3000):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except Exception:
        return False

def start_gd_service():
    if is_gd_service_ready(3000):
        return
    gd_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gd_preparation")
    if os.path.isdir(gd_dir):
        try:
            flags = 0x08000000 if os.name == 'nt' else 0 # CREATE_NO_WINDOW
            subprocess.Popen(
                "npm.cmd run dev" if os.name == 'nt' else "npm run dev",
                cwd=gd_dir,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=flags
            )
        except Exception:
            pass

# Pre-warm GD Preparation service in background daemon thread
threading.Thread(target=start_gd_service, daemon=True).start()


# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="360 Connect - Alumni Portal",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- BASIC UI CSS ----------------
st.markdown(
    """
    <style>
    /* Global Light Page Background */
    .stApp, body, [data-testid="stAppViewContainer"] {
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }

    /* Make Streamlit use full width */
    .block-container {
        max-width: 100% !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        padding-top: 1rem !important;
        margin-top: 0rem !important;
        padding-bottom: 2rem !important;
    }

    /* ── Hide Deploy Button, Main Menu, Footer ── */
    .stAppDeployButton,
    #MainMenu,
    div[data-testid="stStatusWidget"],
    [data-testid="stDecoration"],
    div[data-testid="stDecoration"],
    footer {
        display: none !important;
        visibility: hidden !important;
    }

    /* ── Keep Streamlit Header transparent but functional ── */
    header[data-testid="stHeader"],
    .stAppHeader {
        background: transparent !important;
        box-shadow: none !important;
    }

    /* ── Sidebar Gradient Styling ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(160deg, #1e1b4b 0%, #312e81 55%, #4338ca 100%) !important;
        border-right: none !important;
    }
    [data-testid="stSidebar"] * {
        color: #e0e7ff !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #c7d2fe !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
        color: #c7d2fe !important;
    }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
        color: #a5b4fc !important;
    }
    [data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div {
        background: rgba(165,180,252,0.2) !important;
        border-radius: 8px !important;
    }

    /* ── Global Link Buttons (LinkedIn / GitHub) ── */
    a[data-testid="stLinkButton"] {
        background: linear-gradient(135deg, #2563eb, #4f46e5) !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        padding: 9px 18px !important;
        box-shadow: 0 3px 10px rgba(37, 99, 235, 0.28) !important;
        width: 100% !important;
        text-align: center !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.18s ease-in-out !important;
        opacity: 1 !important;
        visibility: visible !important;
    }
    a[data-testid="stLinkButton"]:hover,
    a[data-testid="stLinkButton"]:focus,
    a[data-testid="stLinkButton"]:active {
        background: linear-gradient(135deg, #1d4ed8, #4338ca) !important;
        color: #ffffff !important;
        box-shadow: 0 5px 16px rgba(37, 99, 235, 0.42) !important;
        text-decoration: none !important;
        opacity: 1 !important;
        visibility: visible !important;
        transform: translateY(-1px) !important;
    }
    a[data-testid="stLinkButton"] * {
        color: #ffffff !important;
        opacity: 1 !important;
        visibility: visible !important;
    }

    /* ── Global Search Input ── */
    [data-testid="stTextInput"] input {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 2px solid #c7d2fe !important;
        border-radius: 12px !important;
        font-size: 14px !important;
        padding: 10px 14px !important;
    }
    [data-testid="stTextInput"] input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
    }
    [data-testid="stTextInput"] input::placeholder {
        color: #94a3b8 !important;
    }

    /* ── KPI Container & Card Boxes (Global) ── */
    .kpi-container {
        background: #ffffff !important;
        border-radius: 18px !important;
        padding: 18px 20px !important;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.03) !important;
        border: 1px solid #e2e8f0 !important;
    }
    .kpi-title {
        font-size: 11px;
        font-weight: 700;
        color: #64748b;
        letter-spacing: 0.6px;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .kpi-val {
        font-size: 26px;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.1;
    }
    .kpi-badge-blue {
        background: #dbeafe;
        color: #2563eb;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 10px;
        margin-left: 6px;
    }

    .admin-card-box {
        background: #ffffff !important;
        border-radius: 18px !important;
        padding: 22px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03) !important;
        border: 1px solid #e2e8f0 !important;
        margin-bottom: 20px !important;
    }

    .admin-nav-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 0 16px 0;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------- COMPACT HEADER (ONLY ONE HEADER) ----------------
def render_header_compact():
    st.markdown(
        """
        <div style="
            width:100%;
            display:flex;
            justify-content:space-between;
            align-items:center;
            padding:8px 16px;
            border-radius:12px;
            background:linear-gradient(135deg,#020617,#0f172a);
            margin:0 0 12px 0;
            border:1px solid rgba(255,255,255,0.08);
            box-sizing:border-box;
        ">
            <div>
                <div style="font-size:20px;font-weight:800;color:#22d3ee;line-height:1;">
                    360 Connect
                </div>
                <div style="font-size:11px;opacity:0.75;margin-top:2px;">
                    Alumni Management System
                </div>
            </div>
            <div style="font-size:11px;opacity:0.60;white-space:nowrap;">
                MySQL
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------- SAFE SECRETS GETTER ----------------
def _sec(name, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


# ---------------- DATABASE ----------------
MYSQL_USER = _sec("MYSQL_USER", "alumni_user")
MYSQL_PASS = _sec("MYSQL_PASS", "StrongPass@123")
MYSQL_HOST = _sec("MYSQL_HOST", "127.0.0.1")
MYSQL_DB = _sec("MYSQL_DB", "alumni_db")
MYSQL_PORT = int(_sec("MYSQL_PORT", 3306))

# ---------------- LINKEDIN OAUTH ----------------
LINKEDIN_CLIENT_ID = _sec("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = _sec("LINKEDIN_CLIENT_SECRET", "")
LINKEDIN_REDIRECT_URI = _sec("LINKEDIN_REDIRECT_URI", "http://localhost:8501/?oauth=linkedin")


def linkedin_config_ok() -> bool:
    return bool(LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET and LINKEDIN_REDIRECT_URI)


# ---------------- DB ENGINE ----------------
MYSQL_URL = URL.create(
    "mysql+pymysql",
    username=MYSQL_USER,
    password=MYSQL_PASS,
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    database=MYSQL_DB,
    query={"charset": "utf8mb4"},
)
engine = create_engine(MYSQL_URL, pool_pre_ping=True)

# ---------------- HELPERS ----------------
def db_exec(stmt, params=None):
    params = params or {}
    with engine.begin() as conn:
        return conn.execute(text(stmt), params)


def db_fetchall(stmt, params=None):
    params = params or {}
    with engine.begin() as conn:
        return conn.execute(text(stmt), params).fetchall()


def db_fetchone(stmt, params=None):
    params = params or {}
    with engine.begin() as conn:
        return conn.execute(text(stmt), params).fetchone()


def hash_password(pw: str) -> bytes:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt())


def check_password(pw: str, hashed: bytes) -> bool:
    if hashed is None:
        return False
    if isinstance(hashed, str):
        hashed = hashed.encode("utf-8")
    return bcrypt.checkpw(pw.encode("utf-8"), hashed)


def validate_password(password: str):
    if len(password) < 8:
        return "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return "Password must have at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return "Password must have at least one lowercase letter"
    if not re.search(r"\d", password):
        return "Password must have at least one number"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must have at least one special character"
    return None


def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "https://" + url
    return url


# Helper to convert graduation year to start year - end year format
def format_batch_year(yr_str: str) -> str:
    if not yr_str:
        return ""
    yr_clean = str(yr_str).strip()
    if not yr_clean or yr_clean.lower() in ("none", "null", "—"):
        return ""
    # If 4-digit year like '2027' -> '2023 - 2027'
    if re.match(r"^\d{4}$", yr_clean):
        try:
            end_yr = int(yr_clean)
            start_yr = end_yr - 4
            return f"{start_yr} - {end_yr}"
        except Exception:
            return yr_clean
    # If already a range like '2023-2027' or '2023 - 2027'
    if "-" in yr_clean:
        parts = [p.strip() for p in yr_clean.split("-")]
        if len(parts) == 2 and parts[0] and parts[1]:
            return f"{parts[0]} - {parts[1]}"
    return yr_clean


def df_with_sno(rows, columns):
    df = pd.DataFrame(rows, columns=columns)
    df = df.reset_index(drop=True)
    df.insert(0, "No.", range(1, len(df) + 1))
    return df


def show_df(df: pd.DataFrame):
    headers = "".join([f"<th style='background:linear-gradient(135deg, #1e1b4b, #312e81); color:#e0e7ff; font-weight:700; font-size:13px; padding:13px 16px; text-align:left; letter-spacing:0.3px; white-space:nowrap;'>{c}</th>" for c in df.columns])
    
    rows_html = []
    for i, (_, row) in enumerate(df.iterrows()):
        bg_col = "#f8fafc" if i % 2 == 0 else "#eef2f6"
        cells = "".join([f"<td style='padding:11px 16px; font-size:13px; color:#1e293b; font-weight:500; border-bottom:1px solid #cbd5e1; white-space:nowrap;'>{'' if (pd.isna(v) or v is None or str(v) == 'None') else str(v)}</td>" for v in row])
        rows_html.append(f"<tr style='background:{bg_col};'>{cells}</tr>")
    
    tbody = "".join(rows_html)
    table_html = f"""
    <div style="overflow-x:auto; background:#f8fafc; border-radius:14px; border:1px solid #cbd5e1; box-shadow:0 4px 16px rgba(0,0,0,0.06); margin-top:14px; margin-bottom:16px;">
        <table style="width:100%; border-collapse:collapse; text-align:left; font-family:inherit;">
            <thead><tr>{headers}</tr></thead>
            <tbody>{tbody}</tbody>
        </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)


# ---------------- SCHEMA ----------------
def ensure_schema():
    db_exec(
        """
    CREATE TABLE IF NOT EXISTS users (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        username VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARBINARY(255) NOT NULL,
        email VARCHAR(255),
        role VARCHAR(20) NOT NULL DEFAULT 'alumni',
        status VARCHAR(20) NOT NULL DEFAULT 'approved',
        linkedin_id VARCHAR(128),
        linkedin_email VARCHAR(255),
        linkedin_verified TINYINT NOT NULL DEFAULT 0,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    )

    db_exec(
        """
    CREATE TABLE IF NOT EXISTS alumni (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        username VARCHAR(100) NOT NULL,
        name VARCHAR(255),
        bio TEXT,
        linkedin VARCHAR(512),
        github VARCHAR(512),
        year VARCHAR(20),
        department VARCHAR(120),
        company VARCHAR(255),
        profile_pic VARCHAR(512),
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY uq_alumni_username (username)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    )

    db_exec(
        """
    CREATE TABLE IF NOT EXISTS messages (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        sender VARCHAR(100) NOT NULL,
        receiver VARCHAR(100) NOT NULL,
        message TEXT NOT NULL,
        is_read TINYINT NOT NULL DEFAULT 0,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    )

    try:
        db_exec("ALTER TABLE messages ADD COLUMN is_read TINYINT NOT NULL DEFAULT 0;")
    except Exception:
        pass

    db_exec(
        """
    CREATE TABLE IF NOT EXISTS connections (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        sender VARCHAR(100) NOT NULL,
        receiver VARCHAR(100) NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY uq_connection (sender, receiver)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    )

    db_exec(
        """
    CREATE TABLE IF NOT EXISTS cleared_chats (
        username VARCHAR(100) NOT NULL,
        peer VARCHAR(100) NOT NULL,
        cleared_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (username, peer)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    )

    # Ensure all tables have aligned collation to prevent MySQL join collation errors
    for tbl in ["users", "alumni", "messages", "connections", "cleared_chats"]:
        try:
            db_exec(f"ALTER TABLE {tbl} CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        except Exception:
            pass

    admin = db_fetchone("SELECT id FROM users WHERE username='admin' AND role='admin'")
    if not admin:
        db_exec(
            "INSERT INTO users (username, password_hash, email, role, status) VALUES (:u,:p,:e,'admin','approved')",
            {"u": "admin", "p": hash_password("admin123"), "e": "admin@local"},
        )


ensure_schema()

# ---------------- SESSION STATE ----------------
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
if "auth_screen" not in st.session_state:
    st.session_state.auth_screen = "main_login"


def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = ""
    st.session_state.linkedin_profile = None
    st.session_state.login_mode = None
    st.session_state.auth_screen = "main_login"
    st.rerun()





# ---------------- LINKEDIN OIDC ----------------
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


handle_linkedin_callback()


def _clean_field(v):
    if not v or str(v).strip().lower() in ("none", "null", "—"):
        return ""
    return re.sub(r"<[^>]+>", "", str(v)).strip()


# ---------------- PROFILE LOAD ----------------
def load_profile_from_db(username: str):
    username = (username or "").strip()
    prof = db_fetchone(
        """SELECT name,bio,linkedin,github,year,department,company,profile_pic
           FROM alumni WHERE username=:u""",
        {"u": username},
    )
    user_meta = db_fetchone(
        "SELECT email, linkedin_verified FROM users WHERE username=:u",
        {"u": username},
    )

    return {
        "name": _clean_field(prof[0] if prof else ""),
        "bio": _clean_field(prof[1] if prof else ""),
        "linkedin": (prof[2] if prof else "") or "",
        "github": (prof[3] if prof else "") or "",
        "year": (prof[4] if prof else "") or "",
        "department": _clean_field(prof[5] if prof else ""),
        "company": _clean_field(prof[6] if prof else ""),
        "profile_pic": (prof[7] if prof else "") or "",
        "email": (user_meta[0] if user_meta else "") or "",
        "verified": (user_meta and user_meta[1] == 1),
    }


# ---------------- AVATAR HELPER ----------------
def get_avatar_html(username: str, size: int = 44, shape: str = "circle") -> str:
    username = (username or "").strip()
    p_info = load_profile_from_db(username)
    disp_name = p_info["name"] or f"@{username}"
    initials = disp_name[:2].upper()
    pic_path = p_info.get("profile_pic") or ""

    border_radius = "50%" if shape == "circle" else "12px"

    if pic_path and os.path.exists(pic_path):
        try:
            with open(pic_path, "rb") as f:
                img_bytes = f.read()
            ext = os.path.splitext(pic_path)[1].lower().replace(".", "")
            mime = "image/png" if ext == "png" else ("image/jpeg" if ext in ["jpg", "jpeg"] else f"image/{ext}")
            b64_str = base64.b64encode(img_bytes).decode("utf-8")
            return f'<img src="data:{mime};base64,{b64_str}" style="width:{size}px; height:{size}px; border-radius:{border_radius}; object-fit:cover; flex-shrink:0; border:1.5px solid #cbd5e1;" />'
        except Exception:
            pass

    font_sz = max(11, int(size * 0.36))
    return f'<div style="width:{size}px; height:{size}px; border-radius:{border_radius}; background:linear-gradient(135deg, #10b981, #059669); color:#ffffff; font-weight:800; font-size:{font_sz}px; display:flex; align-items:center; justify-content:center; flex-shrink:0;">{initials}</div>'


# ---------------- AUTH UI (360 Connect Screens) ----------------
def login_signup_page():
    # Force Light Theme & Card CSS matching screenshot
    st.markdown(
        """
        <style>
        /* Force light page background */
        .stApp, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: #f8fafc !important;
            color: #0f172a !important;
        }

        /* Hide Streamlit top toolbar on auth page */
        div[data-testid="stToolbar"], .stAppDeployButton, #MainMenu {
            display: none !important;
        }
        header[data-testid="stHeader"] {
            background: transparent !important;
        }

        /* Single White Auth Card Container */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #ffffff !important;
            border-radius: 24px !important;
            padding: 36px 32px 32px 32px !important;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.07), 0 2px 6px rgba(0, 0, 0, 0.03) !important;
            border: 1px solid #eef2f6 !important;
        }

        /* Form background transparent inside container */
        div[data-testid="stForm"] {
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            box-shadow: none !important;
        }

        /* Input Labels */
        label, div[data-testid="stForm"] label, [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *, label * {
            font-weight: 700 !important;
            color: #0f172a !important;
            font-size: 14px !important;
            margin-bottom: 4px !important;
        }

        /* Input Boxes & Textareas */
        input, textarea, div[data-testid="stForm"] input, div[data-testid="stForm"] textarea, [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border-radius: 12px !important;
            border: 1px solid #cbd5e1 !important;
            padding: 12px 14px !important;
            font-size: 14px !important;
        }
        input::placeholder, textarea::placeholder, div[data-testid="stForm"] input::placeholder, div[data-testid="stForm"] textarea::placeholder {
            color: #94a3b8 !important;
        }
        input:focus, textarea:focus, div[data-testid="stForm"] input:focus, div[data-testid="stForm"] textarea:focus {
            border-color: #6366f1 !important;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
        }

        /* Primary Submit Button (Login / Create Account) */
        button[kind="primaryFormSubmit"],
        .stFormSubmitButton > button {
            background: linear-gradient(135deg, #2563eb, #6366f1) !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            border-radius: 12px !important;
            border: none !important;
            padding: 12px 20px !important;
            font-size: 15px !important;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35) !important;
            width: 100% !important;
        }
        button[kind="primaryFormSubmit"]:hover,
        .stFormSubmitButton > button:hover {
            background: linear-gradient(135deg, #1d4ed8, #4f46e5) !important;
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5) !important;
            transform: translateY(-1px) !important;
        }

        /* Secondary LinkedIn Button */
        a[data-testid="stLinkButton"], .stElementContainer button[kind="secondary"] {
            background-color: #ffffff !important;
            color: #334155 !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
        }
        a[data-testid="stLinkButton"]:hover, .stElementContainer button[kind="secondary"]:hover {
            background-color: #f8fafc !important;
            border-color: #94a3b8 !important;
        }

        /* Blue Text Link Buttons for Registration */
        div.btn-reg-link button {
            background: transparent !important;
            border: none !important;
            color: #2563eb !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            box-shadow: none !important;
            padding: 4px 6px !important;
            width: 100% !important;
        }
        div.btn-reg-link button:hover {
            text-decoration: underline !important;
            background: transparent !important;
        }

        /* Admin Pill Button */
        div.btn-admin-pill button {
            background: #1d4ed8 !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            border: none !important;
            font-weight: 700 !important;
            font-size: 13px !important;
            padding: 8px 24px !important;
            box-shadow: 0 2px 8px rgba(29, 78, 216, 0.3) !important;
        }
        div.btn-admin-pill button:hover {
            background: #1e40af !important;
        }

        /* Back Outline Button */
        div.btn-back-outline button {
            background: #ffffff !important;
            color: #64748b !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            padding: 6px 20px !important;
        }

        /* Divider text */
        .auth-divider {
            display: flex;
            align-items: center;
            text-align: center;
            color: #94a3b8;
            font-size: 13px;
            margin: 18px 0;
        }
        .auth-divider::before, .auth-divider::after {
            content: '';
            flex: 1;
            border-bottom: 1px solid #e2e8f0;
        }
        .auth-divider::before { margin-right: .6em; }
        .auth-divider::after { margin-left: .6em; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1.8, 1])

    with col2:
        screen = st.session_state.get("auth_screen", "main_login")

        # Single White Container for ALL Card Elements
        with st.container(border=True):

            # ---------------- 1. MAIN LOGIN SCREEN ----------------
            if screen == "main_login":
                st.markdown(
                    """
                    <div style="text-align:center; margin-bottom: 22px;">
                        <div style="font-size: 28px; font-weight: 800; color: #4F46E5; display: flex; align-items: center; justify-content: center; gap: 8px;">
                            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <circle cx="12" cy="12" r="3"></circle>
                                <circle cx="19" cy="5" r="2"></circle>
                                <circle cx="5" cy="5" r="2"></circle>
                                <circle cx="5" cy="19" r="2"></circle>
                                <circle cx="19" cy="19" r="2"></circle>
                                <line x1="12" y1="9" x2="19" y2="5"></line>
                                <line x1="12" y1="9" x2="5" y2="5"></line>
                                <line x1="12" y1="15" x2="5" y2="19"></line>
                                <line x1="12" y1="15" x2="19" y2="19"></line>
                            </svg>
                            360 Connect
                        </div>
                        <div style="font-size: 13px; color: #475569; margin-top: 6px; font-weight: 500;">
                            Bridging the Gap, Empowering the Future
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                with st.form("form_main_login", clear_on_submit=False):
                    email_or_user = st.text_input("Email Address", placeholder="name@university.edu", key="login_email_val").strip()

                    st.markdown(
                        """
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 4px;">
                            <span style="font-weight:600; color:#334155; font-size:13px;">Password</span>
                            <a href="#" style="font-size:12px; color:#2563eb; text-decoration:none; font-weight:600;">Forgot password?</a>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    password = st.text_input("Password", type="password", placeholder="••••••••", key="login_pass_val", label_visibility="collapsed").strip()

                    submitted = st.form_submit_button("Login", use_container_width=True)

                if submitted:
                    if not email_or_user or not password:
                        st.error("Please enter email/username and password.")
                    else:
                        user = db_fetchone(
                            "SELECT username, password_hash, role, status FROM users WHERE username=:u OR email=:u",
                            {"u": email_or_user},
                        )
                        if not user:
                            st.error("Account not found.")
                        elif user[3] != "approved":
                            st.error("Account is pending approval or blocked.")
                        elif check_password(password, user[1]):
                            st.session_state.logged_in = True
                            st.session_state.role = user[2]
                            st.session_state.username = user[0]
                            st.rerun()
                        else:
                            st.error("Invalid password.")

                st.markdown('<div class="auth-divider">or</div>', unsafe_allow_html=True)

                if linkedin_config_ok():
                    st.link_button("Continue with LinkedIn", linkedin_auth_url(), use_container_width=True)
                else:
                    st.button("Continue with LinkedIn", disabled=True, use_container_width=True)

                st.markdown(
                    """
                    <div style="text-align:center; font-size: 13px; color: #475569; font-weight: 500; margin-top: 18px; margin-bottom: 8px;">
                        Don't have an account?
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                c_stu, c_dot, c_alu = st.columns([1, 0.1, 1])
                with c_stu:
                    st.markdown('<div class="btn-reg-link">', unsafe_allow_html=True)
                    if st.button("Student Registration", key="btn_to_student_reg", use_container_width=True):
                        st.session_state.auth_screen = "student_signup"
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

                with c_dot:
                    st.markdown("<div style='text-align:center; color:#94a3b8; font-weight:bold; margin-top:6px;'>•</div>", unsafe_allow_html=True)

                with c_alu:
                    st.markdown('<div class="btn-reg-link">', unsafe_allow_html=True)
                    if st.button("Alumni Registration", key="btn_to_alumni_reg", use_container_width=True):
                        st.session_state.auth_screen = "alumni_signup"
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

                ca1, ca2, ca3 = st.columns([1, 1.2, 1])
                with ca2:
                    st.markdown('<div class="btn-admin-pill">', unsafe_allow_html=True)
                    if st.button("Admin", key="btn_to_admin_login", use_container_width=True):
                        st.session_state.auth_screen = "admin_login"
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            # ---------------- 2. ADMIN LOGIN SCREEN ----------------
            elif screen == "admin_login":
                st.markdown(
                    """
                    <div style="text-align:center; margin-bottom: 22px;">
                        <div style="font-size: 28px; font-weight: 800; color: #4F46E5; display: flex; align-items: center; justify-content: center; gap: 8px;">
                            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <circle cx="12" cy="12" r="3"></circle>
                                <circle cx="19" cy="5" r="2"></circle>
                                <circle cx="5" cy="5" r="2"></circle>
                                <circle cx="5" cy="19" r="2"></circle>
                                <circle cx="19" cy="19" r="2"></circle>
                                <line x1="12" y1="9" x2="19" y2="5"></line>
                                <line x1="12" y1="9" x2="5" y2="5"></line>
                                <line x1="12" y1="15" x2="5" y2="19"></line>
                                <line x1="12" y1="15" x2="19" y2="19"></line>
                            </svg>
                            360 Connect
                        </div>
                        <div style="font-size: 15px; color: #2563eb; font-weight: 700; margin-top: 6px;">
                            Admin
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                with st.form("form_admin_login"):
                    username = st.text_input("Username", placeholder="eg. abhiii06", key="admin_user_val").strip()
                    password = st.text_input("Password", type="password", placeholder="••••••••", key="admin_pass_val").strip()
                    submitted = st.form_submit_button("Login", use_container_width=True)

                if submitted:
                    if not username or not password:
                        st.error("Please enter username and password.")
                    else:
                        user = db_fetchone(
                            "SELECT username, password_hash, role, status FROM users WHERE (username=:u OR email=:u) AND role='admin'",
                            {"u": username},
                        )
                        if not user:
                            st.error("Admin account not found.")
                        elif user[3] != "approved":
                            st.error("Admin account blocked.")
                        elif check_password(password, user[1]):
                            st.session_state.logged_in = True
                            st.session_state.role = user[2]
                            st.session_state.username = user[0]
                            st.rerun()
                        else:
                            st.error("Invalid password.")

                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                cb1, cb2, cb3 = st.columns([1, 1, 1])
                with cb2:
                    st.markdown('<div class="btn-back-outline">', unsafe_allow_html=True)
                    if st.button("Back", key="btn_admin_back", use_container_width=True):
                        st.session_state.auth_screen = "main_login"
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            # ---------------- 3. ALUMNI SIGNUP SCREEN ----------------
            elif screen == "alumni_signup":
                st.markdown(
                    """
                    <div style="text-align:center; margin-bottom: 22px;">
                        <div style="font-size: 28px; font-weight: 800; color: #4F46E5; display: flex; align-items: center; justify-content: center; gap: 8px;">
                            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <circle cx="12" cy="12" r="3"></circle>
                                <circle cx="19" cy="5" r="2"></circle>
                                <circle cx="5" cy="5" r="2"></circle>
                                <circle cx="5" cy="19" r="2"></circle>
                                <circle cx="19" cy="19" r="2"></circle>
                                <line x1="12" y1="9" x2="19" y2="5"></line>
                                <line x1="12" y1="9" x2="5" y2="5"></line>
                                <line x1="12" y1="15" x2="5" y2="19"></line>
                                <line x1="12" y1="15" x2="19" y2="19"></line>
                            </svg>
                            360 Connect
                        </div>
                        <div style="font-size: 15px; color: #475569; font-weight: 500; margin-top: 6px;">
                            Sign Up as <span style="color: #2563eb; font-weight: 700;">Alumni</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                with st.form("form_alumni_signup"):
                    username = st.text_input("Username", placeholder="eg. abhiii06", key="alumni_su_user_val").strip()
                    email = st.text_input("Email Address", placeholder="name@university.edu", key="alumni_su_email_val").strip()
                    password = st.text_input("Password", type="password", placeholder="••••••••", key="alumni_su_pass_val").strip()
                    confirm_pass = st.text_input("Conform Password", type="password", placeholder="••••••••", key="alumni_su_confirm_val").strip()

                    submitted = st.form_submit_button("Create Account", use_container_width=True)

                if submitted:
                    if not username or not email or not password:
                        st.error("All fields are required.")
                    elif password != confirm_pass:
                        st.error("Passwords do not match.")
                    else:
                        err = validate_password(password)
                        if err:
                            st.error(err)
                        else:
                            try:
                                db_exec(
                                    """
                                    INSERT INTO users (username, password_hash, email, role, status)
                                    VALUES (:u, :p, :e, 'alumni', 'approved')
                                    """,
                                    {"u": username, "p": hash_password(password), "e": email},
                                )
                                db_exec(
                                    "INSERT IGNORE INTO alumni (username, name) VALUES (:u, :n)",
                                    {"u": username, "n": username},
                                )
                                st.success("Account created successfully! Please login.")
                                st.session_state.auth_screen = "main_login"
                                st.rerun()
                            except Exception as e:
                                st.error(f"Registration failed: {e}")

                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                cb1, cb2, cb3 = st.columns([1, 1, 1])
                with cb2:
                    st.markdown('<div class="btn-back-outline">', unsafe_allow_html=True)
                    if st.button("Back", key="btn_alumni_su_back", use_container_width=True):
                        st.session_state.auth_screen = "main_login"
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            # ---------------- 4. STUDENT SIGNUP SCREEN ----------------
            elif screen == "student_signup":
                st.markdown(
                    """
                    <div style="text-align:center; margin-bottom: 22px;">
                        <div style="font-size: 28px; font-weight: 800; color: #4F46E5; display: flex; align-items: center; justify-content: center; gap: 8px;">
                            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <circle cx="12" cy="12" r="3"></circle>
                                <circle cx="19" cy="5" r="2"></circle>
                                <circle cx="5" cy="5" r="2"></circle>
                                <circle cx="5" cy="19" r="2"></circle>
                                <circle cx="19" cy="19" r="2"></circle>
                                <line x1="12" y1="9" x2="19" y2="5"></line>
                                <line x1="12" y1="9" x2="5" y2="5"></line>
                                <line x1="12" y1="15" x2="5" y2="19"></line>
                                <line x1="12" y1="15" x2="19" y2="19"></line>
                            </svg>
                            360 Connect
                        </div>
                        <div style="font-size: 15px; color: #475569; font-weight: 500; margin-top: 6px;">
                            Sign Up as <span style="color: #2563eb; font-weight: 700;">Student</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                with st.form("form_student_signup"):
                    username = st.text_input("Username", placeholder="eg. abhiii06", key="student_su_user_val").strip()
                    email = st.text_input("Email Address", placeholder="name@university.edu", key="student_su_email_val").strip()
                    password = st.text_input("Password", type="password", placeholder="••••••••", key="student_su_pass_val").strip()
                    confirm_pass = st.text_input("Conform Password", type="password", placeholder="••••••••", key="student_su_confirm_val").strip()

                    submitted = st.form_submit_button("Create Account", use_container_width=True)

                if submitted:
                    if not username or not email or not password:
                        st.error("All fields are required.")
                    elif password != confirm_pass:
                        st.error("Passwords do not match.")
                    else:
                        err = validate_password(password)
                        if err:
                            st.error(err)
                        else:
                            try:
                                db_exec(
                                    """
                                    INSERT INTO users (username, password_hash, email, role, status)
                                    VALUES (:u, :p, :e, 'student', 'approved')
                                    """,
                                    {"u": username, "p": hash_password(password), "e": email},
                                )
                                db_exec(
                                    "INSERT IGNORE INTO alumni (username, name) VALUES (:u, :n)",
                                    {"u": username, "n": username},
                                )
                                st.success("Student account created successfully! Please login.")
                                st.session_state.auth_screen = "main_login"
                                st.rerun()
                            except Exception as e:
                                st.error(f"Registration failed: {e}")

                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                cb1, cb2, cb3 = st.columns([1, 1, 1])
                with cb2:
                    st.markdown('<div class="btn-secondary-outline">', unsafe_allow_html=True)
                    if st.button("Back", key="btn_student_su_back", use_container_width=True):
                        st.session_state.auth_screen = "main_login"
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)





def inject_dashboard_theme_css():
    st.markdown(
        """
        <style>
        /* Light Page Background */
        .stApp, body, [data-testid="stAppViewContainer"] {
            background-color: #f8fafc !important;
            color: #0f172a !important;
        }

        /* ── Streamlit Header & Sidebar Toggle Fix ── */
        header[data-testid="stHeader"],
        [data-testid="stHeader"],
        .stAppHeader {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            background: transparent !important;
            background-color: transparent !important;
            box-shadow: none !important;
            border: none !important;
            height: 60px !important;
            min-height: 60px !important;
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            z-index: 99999 !important;
            pointer-events: none !important;
        }

        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"],
        div[data-testid="stSidebarCollapsedControl"],
        button[aria-label="Expand sidebar"],
        button[aria-label="Open sidebar"] {
            display: inline-flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            pointer-events: auto !important;
            position: fixed !important;
            top: 12px !important;
            left: 12px !important;
            background: #ffffff !important;
            color: #000000 !important;
            border: 1.5px solid #cbd5e1 !important;
            border-radius: 8px !important;
            padding: 6px 10px !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
            cursor: pointer !important;
            z-index: 9999999 !important;
        }

        [data-testid="stSidebarCollapsedControl"] button,
        [data-testid="collapsedControl"] button {
            background: transparent !important;
            border: none !important;
            color: #000000 !important;
            pointer-events: auto !important;
        }
        [data-testid="stSidebarCollapsedControl"] svg,
        [data-testid="collapsedControl"] svg,
        [data-testid="collapsedControl"] button svg,
        button[data-testid="stSidebarCollapsedControl"] svg,
        header[data-testid="stHeader"] button svg {
            fill: #000000 !important;
            stroke: #000000 !important;
            color: #000000 !important;
        }

        /* Hide only Deploy button and footer decorations */
        [data-testid="stToolbarActions"],
        [data-testid="stDecoration"],
        div[data-testid="stDecoration"],
        footer {
            display: none !important;
            visibility: hidden !important;
        }

        /* High Contrast Button Styling */
        button, .stButton > button, div.stDownloadButton > button {
            font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
            font-size: 14px !important;
            font-weight: 700 !important;
        }

        /* Primary Blue/Purple Gradient Buttons */
        button[kind="primary"],
        button[kind="primaryFormSubmit"],
        div.btn-purple-approve button,
        div.btn-chat-purple button,
        div.stDownloadButton button {
            background: linear-gradient(135deg, #2563eb, #6366f1) !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35) !important;
            border-radius: 12px !important;
            padding: 10px 18px !important;
            width: 100% !important;
        }
        button[kind="primary"]:hover,
        button[kind="primaryFormSubmit"]:hover,
        div.btn-purple-approve button:hover,
        div.btn-chat-purple button:hover,
        div.stDownloadButton button:hover {
            background: linear-gradient(135deg, #1d4ed8, #4f46e5) !important;
            color: #ffffff !important;
        }

        /* Secondary / Outline Buttons (Default for all non-primary buttons) */
        button[kind="secondary"],
        .stButton > button:not([kind="primary"]):not([kind="primaryFormSubmit"]),
        div.btn-outline-reject button,
        div.btn-view-profile button,
        div.btn-back-outline button {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1.5px solid #cbd5e1 !important;
            font-weight: 700 !important;
            border-radius: 12px !important;
            padding: 10px 18px !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
            width: 100% !important;
            text-align: center !important;
        }
        button[kind="secondary"]:hover,
        .stButton > button:not([kind="primary"]):not([kind="primaryFormSubmit"]):hover,
        div.btn-outline-reject button:hover,
        div.btn-view-profile button:hover,
        div.btn-back-outline button:hover {
            background-color: #f1f5f9 !important;
            color: #0f172a !important;
            border-color: #94a3b8 !important;
        }

        /* High Contrast Radio Button Styling (Main Body only, strictly excludes sidebar) */
        [data-testid="stMain"] div[data-testid="stRadio"] label,
        [data-testid="stMain"] div[data-testid="stRadio"] label *,
        [data-testid="stMain"] div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stMain"] div[data-testid="stRadio"] span,
        [data-testid="stMain"] div[data-testid="stRadio"] div {
            color: #0f172a !important;
        }

        /* Metrics contrast in main view */
        div[data-testid="stMetricValue"] > div,
        div[data-testid="stMetricLabel"] > div {
            color: #0f172a !important;
        }

        /* ── Sidebar Radio Navigation: Clean Transparent Restored Style ── */
        [data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"] {
            background-color: transparent !important;
            background: transparent !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 4px 8px !important;
            margin: 2px 0 !important;
            box-shadow: none !important;
            transform: none !important;
        }
        [data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {
            background: rgba(255, 255, 255, 0.08) !important;
            border: none !important;
            transform: none !important;
        }
        [data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"] * {
            color: #c7d2fe !important;
        }
        [data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"] p {
            color: #c7d2fe !important;
            font-size: 14px !important;
            font-weight: 600 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div {
            background: rgba(165,180,252,0.2) !important;
            border-radius: 8px !important;
        }

        /* Link Buttons (LinkedIn / GitHub) */
        a[data-testid="stLinkButton"] {
            background: linear-gradient(135deg, #2563eb, #4f46e5) !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: 700 !important;
            border-radius: 12px !important;
            padding: 10px 18px !important;
            box-shadow: 0 3px 10px rgba(37, 99, 235, 0.28) !important;
            width: 100% !important;
            text-align: center !important;
            transition: all 0.18s ease-in-out !important;
            opacity: 1 !important;
            visibility: visible !important;
        }
        a[data-testid="stLinkButton"]:hover,
        a[data-testid="stLinkButton"]:focus,
        a[data-testid="stLinkButton"]:active {
            background: linear-gradient(135deg, #1d4ed8, #4338ca) !important;
            color: #ffffff !important;
            box-shadow: 0 5px 16px rgba(37, 99, 235, 0.42) !important;
            text-decoration: none !important;
            transform: translateY(-1px) !important;
        }
        a[data-testid="stLinkButton"] * {
            color: #ffffff !important;
            opacity: 1 !important;
            visibility: visible !important;
        }

        /* Top Header Styling */
        .admin-nav-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0 16px 0;
            border-bottom: 1px solid #e2e8f0;
            margin-bottom: 24px;
        }

        /* Cards */
        .admin-card-box {
            background: #ffffff !important;
            border-radius: 20px !important;
            padding: 24px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.02) !important;
            border: 1px solid #eef2f6 !important;
            margin-bottom: 20px !important;
        }

        /* KPI Metric Cards */
        .kpi-container {
            background: #ffffff !important;
            border-radius: 20px !important;
            padding: 20px 22px !important;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.03) !important;
            border: 1px solid #f1f5f9 !important;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }
        .kpi-title {
            font-size: 11px;
            font-weight: 700;
            color: #64748b;
            letter-spacing: 0.6px;
            text-transform: uppercase;
            margin-bottom: 6px;
        }
        .kpi-val {
            font-size: 30px;
            font-weight: 800;
            color: #0f172a;
            line-height: 1.1;
        }
        .kpi-badge-blue {
            background: #dbeafe;
            color: #2563eb;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 10px;
            margin-left: 6px;
        }

        /* ── Remove extra top space ── */
        .block-container {
            padding-top: 0rem !important;
            margin-top: 0rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
            max-width: 100% !important;
        }

        /* ── Sidebar gradient styling ── */
        [data-testid="stSidebar"] {
            background: linear-gradient(160deg, #1e1b4b 0%, #312e81 55%, #4338ca 100%) !important;
            border-right: none !important;
        }
        [data-testid="stSidebar"] * {
            color: #e0e7ff !important;
        }
        [data-testid="stSidebar"] .stRadio label {
            color: #c7d2fe !important;
            font-weight: 600 !important;
        }
        [data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
            color: #c7d2fe !important;
        }
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
            color: #a5b4fc !important;
        }
        [data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div {
            background: rgba(165,180,252,0.2) !important;
            border-radius: 8px !important;
        }

        /* ── Clean Sidebar Collapse/Expand Arrow Controls -> Black Arrow ── */
        [data-testid="stSidebarCollapseButton"] button,
        button[data-testid="stSidebarCollapseButton"] {
            color: #000000 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        [data-testid="stSidebarCollapseButton"] svg,
        button[data-testid="stSidebarCollapseButton"] svg,
        section[data-testid="stSidebar"] button[kind="header"] svg,
        section[data-testid="stSidebar"] button svg {
            fill: #000000 !important;
            stroke: #000000 !important;
            color: #000000 !important;
        }

        /* When sidebar is collapsed, the open arrow button */
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapsedControl"] button,
        button[data-testid="stSidebarCollapsedControl"] {
            display: inline-flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            background: #ffffff !important;
            color: #000000 !important;
            border: 1.5px solid #cbd5e1 !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
            padding: 4px 8px !important;
        }
        [data-testid="stSidebarCollapsedControl"] svg,
        [data-testid="collapsedControl"] svg,
        [data-testid="collapsedControl"] button svg,
        button[data-testid="stSidebarCollapsedControl"] svg,
        header[data-testid="stHeader"] button svg {
            fill: #000000 !important;
            stroke: #000000 !important;
            color: #000000 !important;
        }

        /* ── WhatsApp Contact Card Direct Tap Overlay ── */
        div[data-testid="stElementContainer"]:has(div.wa-contact-card-item) {
            position: relative !important;
            z-index: 1 !important;
            margin-bottom: 0px !important;
            pointer-events: none !important;
        }
        div[data-testid="stElementContainer"]:has(div.wa-contact-card-item) * {
            pointer-events: none !important;
        }
        div[data-testid="stElementContainer"]:has(div.wa-contact-card-item) + div[data-testid="stElementContainer"] {
            position: relative !important;
            margin-top: -72px !important;
            height: 72px !important;
            z-index: 99999 !important;
            margin-bottom: 8px !important;
            pointer-events: auto !important;
        }
        div[data-testid="stElementContainer"]:has(div.wa-contact-card-item) + div[data-testid="stElementContainer"] div[data-testid="stButton"] {
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            height: 72px !important;
            pointer-events: auto !important;
        }
        div[data-testid="stElementContainer"]:has(div.wa-contact-card-item) + div[data-testid="stElementContainer"] button {
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            height: 72px !important;
            min-height: 72px !important;
            opacity: 0 !important;
            font-size: 0 !important;
            color: transparent !important;
            background: transparent !important;
            border: none !important;
            cursor: pointer !important;
            box-shadow: none !important;
            outline: none !important;
            padding: 0 !important;
            margin: 0 !important;
            pointer-events: auto !important;
            z-index: 99999 !important;
        }
        div[data-testid="stElementContainer"]:has(div.wa-contact-card-item) + div[data-testid="stElementContainer"] button * {
            opacity: 0 !important;
            font-size: 0 !important;
            color: transparent !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }

        /* ── Input & Textarea styling (Bio box matching Name/Email input boxes) ── */
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        textarea {
            background: #ffffff !important;
            color: #0f172a !important;
            border: 2px solid #1e1b4b !important;
            border-radius: 12px !important;
            font-size: 14px !important;
            padding: 10px 14px !important;
        }
        [data-testid="stTextInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus,
        textarea:focus {
            border-color: #312e81 !important;
            box-shadow: 0 0 0 3px rgba(30, 27, 75, 0.15) !important;
        }
        [data-testid="stTextInput"] input::placeholder,
        [data-testid="stTextArea"] textarea::placeholder,
        textarea::placeholder {
            color: #94a3b8 !important;
        }

        /* ── File Uploader Box (Profile Picture Drag & Drop) ── */
        [data-testid="stFileUploader"],
        section[data-testid="stFileUploaderDropzone"],
        [data-testid="stFileUploaderDropzone"],
        div[data-testid="stFileDropzone"] {
            background-color: #ffffff !important;
            background: #ffffff !important;
            border: 2px solid #1e1b4b !important;
            border-radius: 14px !important;
            color: #0f172a !important;
        }
        section[data-testid="stFileUploaderDropzone"] *,
        [data-testid="stFileUploaderDropzone"] *,
        div[data-testid="stFileDropzone"] * {
            color: #0f172a !important;
        }
        section[data-testid="stFileUploaderDropzone"] small,
        [data-testid="stFileUploaderDropzone"] small {
            color: #64748b !important;
        }
        section[data-testid="stFileUploaderDropzone"] button,
        [data-testid="stFileUploaderDropzone"] button {
            background: #1e1b4b !important;
            color: #ffffff !important;
            border-radius: 10px !important;
            border: none !important;
            font-weight: 700 !important;
        }
        section[data-testid="stFileUploaderDropzone"] button *,
        [data-testid="stFileUploaderDropzone"] button * {
            color: #ffffff !important;
        }

        /* ── Global Form Submit Buttons (Save Profile, etc.) ── */
        div[data-testid="stFormSubmitButton"] button,
        .stFormSubmitButton > button,
        button[kind="primaryFormSubmit"] {
            background: linear-gradient(135deg, #2563eb 0%, #6366f1 100%) !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            font-size: 15px !important;
            border-radius: 12px !important;
            border: none !important;
            padding: 12px 28px !important;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35) !important;
            cursor: pointer !important;
        }
        div[data-testid="stFormSubmitButton"] button *,
        .stFormSubmitButton > button *,
        button[kind="primaryFormSubmit"] * {
            color: #ffffff !important;
            font-weight: 700 !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
        div[data-testid="stFormSubmitButton"] button:hover,
        .stFormSubmitButton > button:hover,
        button[kind="primaryFormSubmit"]:hover {
            background: linear-gradient(135deg, #1d4ed8 0%, #4f46e5 100%) !important;
            box-shadow: 0 6px 18px rgba(99, 102, 241, 0.5) !important;
            transform: translateY(-1px) !important;
        }

        /* ── Compact WhatsApp Chat Form Send Button ── */
        div[data-testid="stForm"]:has(input[placeholder="Type a message..."]) div[data-testid="stFormSubmitButton"] button,
        div[data-testid="stForm"]:has(input[aria-label="Type a message"]) div[data-testid="stFormSubmitButton"] button {
            background: linear-gradient(135deg, #2563eb, #6366f1) !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            font-size: 14px !important;
            padding: 8px 16px !important;
            height: 44px !important;
            min-height: 44px !important;
            max-height: 44px !important;
            width: 100% !important;
            white-space: nowrap !important;
            word-break: keep-all !important;
            border-radius: 12px !important;
            border: none !important;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35) !important;
            margin: 0 !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        div[data-testid="stForm"]:has(input[placeholder="Type a message..."]) div[data-testid="stFormSubmitButton"] button *,
        div[data-testid="stForm"]:has(input[aria-label="Type a message"]) div[data-testid="stFormSubmitButton"] button * {
            white-space: nowrap !important;
            word-break: keep-all !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            font-size: 14px !important;
        }
        div[data-testid="stForm"]:has(input[placeholder="Type a message..."]) div[data-testid="stFormSubmitButton"] button:hover,
        div[data-testid="stForm"]:has(input[aria-label="Type a message"]) div[data-testid="stFormSubmitButton"] button:hover {
            background: linear-gradient(135deg, #1d4ed8, #4f46e5) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 18px rgba(99, 102, 241, 0.5) !important;
        }

        /* ── Directory Connect & Action Primary Buttons ── */
        /* Streamlit renders a widget outside the preceding markdown div, so
           target its generated key class as well as the visual wrapper. */
        div.btn-connect-primary button,
        div[class*="st-key-btn_conn_"] button {
            background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
            background-color: #2563eb !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: 700 !important;
            border-radius: 12px !important;
            padding: 9px 18px !important;
            box-shadow: 0 3px 10px rgba(37, 99, 235, 0.35) !important;
            width: 100% !important;
            text-align: center !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: all 0.18s ease-in-out !important;
        }
        div.btn-connect-primary button *,
        div[class*="st-key-btn_conn_"] button * {
            color: #ffffff !important;
            font-weight: 700 !important;
        }
        div.btn-connect-primary button:hover,
        div[class*="st-key-btn_conn_"] button:hover {
            background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
            background-color: #1d4ed8 !important;
            color: #ffffff !important;
            box-shadow: 0 5px 16px rgba(37, 99, 235, 0.45) !important;
            transform: translateY(-1px) !important;
        }

        /* ── Accept Request Button (Vibrant Emerald Green) ── */
        div.btn-accept-green button,
        div[class*="st-key-acc_"] button {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
            background-color: #10b981 !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: 700 !important;
            border-radius: 10px !important;
            padding: 8px 14px !important;
            box-shadow: 0 3px 10px rgba(16, 185, 129, 0.3) !important;
            transition: all 0.18s ease-in-out !important;
            width: 100% !important;
        }
        div.btn-accept-green button *,
        div[class*="st-key-acc_"] button * {
            color: #ffffff !important;
            font-weight: 700 !important;
        }
        div.btn-accept-green button:hover,
        div[class*="st-key-acc_"] button:hover {
            background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
            box-shadow: 0 5px 14px rgba(16, 185, 129, 0.45) !important;
            transform: translateY(-1px) !important;
        }

        /* ── Decline Request Button (Soft Rose Crimson Outline) ── */
        div.btn-decline-red button,
        div[class*="st-key-dec_"] button {
            background: #fef2f2 !important;
            background-color: #fef2f2 !important;
            color: #dc2626 !important;
            border: 1.5px solid #fca5a5 !important;
            font-weight: 700 !important;
            border-radius: 10px !important;
            padding: 8px 14px !important;
            box-shadow: 0 1px 3px rgba(220, 38, 38, 0.08) !important;
            transition: all 0.18s ease-in-out !important;
            width: 100% !important;
        }
        div.btn-decline-red button *,
        div[class*="st-key-dec_"] button * {
            color: #dc2626 !important;
            font-weight: 700 !important;
        }
        div.btn-decline-red button:hover,
        div[class*="st-key-dec_"] button:hover {
            background: #fee2e2 !important;
            color: #b91c1c !important;
            border-color: #f87171 !important;
            transform: translateY(-1px) !important;
        }

        /* ── Download CSV Button ── */
        div[data-testid="stDownloadButton"] > button,
        div.stDownloadButton > button {
            background: linear-gradient(135deg, #2563eb, #6366f1) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 12px !important;
            font-size: 15px !important;
            font-weight: 700 !important;
            padding: 12px 24px !important;
            width: 100% !important;
            cursor: pointer !important;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35) !important;
        }
        div[data-testid="stDownloadButton"] > button *,
        div.stDownloadButton > button * {
            color: #ffffff !important;
            font-weight: 700 !important;
        }
        div[data-testid="stDownloadButton"] > button:hover,
        div.stDownloadButton > button:hover {
            background: linear-gradient(135deg, #1d4ed8, #4f46e5) !important;
            box-shadow: 0 6px 18px rgba(99, 102, 241, 0.5) !important;
            transform: translateY(-1px) !important;
        }

        /* ── WhatsApp Seamless Chat Header & Blue Options Button ── */
        div[class*="st-key-wa_chat_header"] {
            background: #f0f2f5 !important;
            background-color: #f0f2f5 !important;
            border: 1px solid #e2e8f0 !important;
            border-bottom: 1px solid #d1d7db !important;
            border-radius: 14px 14px 0 0 !important;
            padding: 10px 16px !important;
            min-height: 60px !important;
            height: 60px !important;
            box-sizing: border-box !important;
            display: flex !important;
            align-items: center !important;
            margin-bottom: 0 !important;
        }
        div[class*="st-key-wa_chat_header"] > div {
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        div[class*="st-key-wa_chat_header"] div[data-testid="stHorizontalBlock"] {
            align-items: center !important;
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        div[class*="st-key-wa_chat_header"] div[data-testid="stColumn"] {
            display: flex !important;
            align-items: center !important;
            padding: 0 !important;
        }
        div[class*="st-key-wa_chat_header"] div[data-testid="stColumn"]:first-child {
            justify-content: flex-start !important;
        }
        div[class*="st-key-wa_chat_header"] div[data-testid="stColumn"]:last-child {
            justify-content: flex-end !important;
        }
        div[class*="st-key-wa_chat_header"] div[data-testid="stPopover"] {
            display: flex !important;
            align-items: center !important;
            justify-content: flex-end !important;
            margin: 0 !important;
            padding: 0 !important;
            width: auto !important;
        }
        /* Blue Box for Options Button (moved to top-right and changed from black to blue) */
        div[class*="st-key-wa_chat_header"] div[data-testid="stPopover"] > button {
            background: #2563eb !important;
            background-color: #2563eb !important;
            border: none !important;
            color: #ffffff !important;
            font-size: 20px !important;
            font-weight: 800 !important;
            box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35) !important;
            padding: 0 !important;
            min-height: 36px !important;
            height: 36px !important;
            width: 36px !important;
            min-width: 36px !important;
            cursor: pointer !important;
            border-radius: 8px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin: 0 0 0 auto !important;
            transition: all 0.2s ease !important;
        }
        div[class*="st-key-wa_chat_header"] div[data-testid="stPopover"] > button:hover {
            background: #1d4ed8 !important;
            background-color: #1d4ed8 !important;
            color: #ffffff !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.5) !important;
            transform: translateY(-1px) !important;
        }
        div[class*="st-key-wa_chat_header"] div[data-testid="stPopover"] > button *,
        div[class*="st-key-wa_chat_header"] div[data-testid="stPopover"] > button span,
        div[class*="st-key-wa_chat_header"] div[data-testid="stPopover"] > button p {
            color: #ffffff !important;
            font-size: 20px !important;
            font-weight: 800 !important;
            line-height: 1 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        /* Hide default Streamlit dropdown arrow inside chat header popover button */
        div[class*="st-key-wa_chat_header"] div[data-testid="stPopover"] button svg,
        div[class*="st-key-wa_chat_header"] div[data-testid="stPopover"] button [data-testid="stIcon"],
        div[class*="st-key-wa_chat_header"] div[data-testid="stPopover"] button span:has(svg) {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            height: 0 !important;
        }
        /* Remove gap between chat header and messages canvas */
        div:has(> div[class*="st-key-wa_chat_header"]),
        div[data-testid="stElementContainer"]:has(div[class*="st-key-wa_chat_header"]) {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }
        div:has(> div[class*="st-key-wa_chat_header"]) + div,
        div[data-testid="stElementContainer"]:has(div[class*="st-key-wa_chat_header"]) + div[data-testid="stElementContainer"],
        div[data-testid="stElementContainer"]:has(.wa-chat-canvas) {
            margin-top: -1rem !important;
            padding-top: 0 !important;
        }

        /* ── Clean White Popover Dropdown Card ── */
        div[data-testid="stPopoverBody"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.12) !important;
            padding: 12px !important;
        }
        div[data-testid="stPopoverBody"] * {
            color: #0f172a !important;
        }
        div[data-testid="stPopoverBody"] button {
            background: #ffffff !important;
            color: #dc2626 !important;
            border: 1px solid #fee2e2 !important;
            font-weight: 700 !important;
            border-radius: 8px !important;
            padding: 8px 14px !important;
            width: 100% !important;
        }
        div[data-testid="stPopoverBody"] button:hover {
            background: #fef2f2 !important;
            color: #b91c1c !important;
            border-color: #fca5a5 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------- ALUMNI UI ----------------
def alumni_dashboard():
    inject_dashboard_theme_css()

    # Sidebar Navigation
    st.sidebar.markdown(
        """
        <div style="font-size: 22px; font-weight: 800; color: #ffffff; display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.5">
                <circle cx="12" cy="12" r="3"></circle>
                <circle cx="19" cy="5" r="2"></circle>
                <circle cx="5" cy="5" r="2"></circle>
                <circle cx="5" cy="19" r="2"></circle>
                <circle cx="19" cy="19" r="2"></circle>
            </svg>
            360 Connect
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.role == "student":
        nav_options = ["Dashboard", "Alumni Directory", "GD Preparation", "Aptitude Preparation", "Messages", "My Profile", "Logout"]
    else:
        nav_options = ["Dashboard", "Alumni Directory", "GD Preparation", "Aptitude Preparation", "Messages", "My Profile", "Logout"]
    selected_nav = st.sidebar.radio("Navigation", nav_options, label_visibility="collapsed")
    user_role_label = st.session_state.role.capitalize() if st.session_state.role else "Alumni"
    st.sidebar.caption(f"Signed in as: **{st.session_state.username}** ({user_role_label})")

    if selected_nav == "Logout":
        logout()
        return

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    p = load_profile_from_db(st.session_state.username)
    display_user_name = p["name"] or st.session_state.username

    # ---------------- 1. ALUMNI DASHBOARD ----------------
    if selected_nav == "Dashboard":
        st.markdown(
            f"""
            <div style="margin-bottom: 24px;">
                <h1 style="font-size: 32px; font-weight: 800; color: #1e1b4b; margin: 0 0 6px 0;">Welcome back, {display_user_name}.</h1>
                <div style="font-size: 15px; color: #64748b; font-weight: 500;">
                    Here is what's happening in your alumni network today.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Real Network KPI Stats from DB
        total_alumni = db_fetchone("SELECT COUNT(*) FROM users WHERE role='alumni'")[0]
        total_students = db_fetchone("SELECT COUNT(*) FROM users WHERE role='student'")[0]
        total_connections = db_fetchone(
            """
            SELECT COUNT(*) FROM connections
            WHERE (sender = :u OR receiver = :u) AND status = 'accepted'
            """,
            {"u": st.session_state.username},
        )[0]

        s1, s2, s3 = st.columns(3)
        with s1:
            st.markdown(
                f"""
                <div class="kpi-container">
                    <div>
                        <div class="kpi-title">TOTAL ALUMNI</div>
                        <div class="kpi-val">{total_alumni} <span class="kpi-badge-blue">Network</span></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with s2:
            st.markdown(
                f"""
                <div class="kpi-container">
                    <div>
                        <div class="kpi-title">ACTIVE STUDENTS</div>
                        <div class="kpi-val">{total_students} <span class="kpi-badge-blue">Mentorship</span></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with s3:
            st.markdown(
                f"""
                <div class="kpi-container">
                    <div>
                        <div class="kpi-title">MY CONNECTIONS</div>
                        <div class="kpi-val">{total_connections} <span class="kpi-badge-blue">Connected</span></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        col_l, col_r = st.columns([1.1, 1.2])

        with col_l:
            # Current User's Profile Summary Card
            formatted_yr = format_batch_year(p["year"])
            batch_line = f"<div style='font-size:13px; font-weight:700; color:#2563eb; margin-top:2px;'>Batch: {formatted_yr}</div>" if formatted_yr else ""
            dept_line = f"<div style='font-size:13px; color:#475569; margin-top:2px;'>{p['department']}</div>" if p['department'] else ""
            comp_line = f"<div style='font-size:13px; color:#64748b; margin-top:2px;'>{p['company']}</div>" if p['company'] else ""
            bio_line = f"<div style='font-size:13px; color:#64748b; font-style:italic; margin-top:10px; border-top:1px solid #f1f5f9; padding-top:8px;'>{p['bio']}</div>" if p['bio'] else ""
            avatar_html = get_avatar_html(st.session_state.username, size=56)

            card_content = (
                f'<div class="admin-card-box">'
                f'<div style="font-size: 18px; font-weight: 800; color: #0f172a; margin-bottom: 14px;">Your Profile Card</div>'
                f'<div style="display: flex; align-items: center; gap: 16px;">'
                f'{avatar_html}'
                f'<div>'
                f'<div style="font-size: 18px; font-weight: 800; color: #0f172a;">{display_user_name}</div>'
                f'{batch_line}'
                f'{dept_line}'
                f'{comp_line}'
                f'</div>'
                f'</div>'
                f'{bio_line}'
                f'</div>'
            )
            st.markdown(card_content, unsafe_allow_html=True)

        with col_r:
            # Connection Requests Section
            st.markdown(
                """
                <div class="admin-card-box">
                    <div style="font-size: 18px; font-weight: 800; color: #0f172a; margin-bottom: 4px;">Connection Requests</div>
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 16px;">Review incoming requests to connect and chat.</div>
                """,
                unsafe_allow_html=True,
            )

            pending_raw = db_fetchall(
                """
                SELECT id, sender, created_at
                FROM connections
                WHERE receiver = :u AND status = 'pending'
                ORDER BY created_at DESC
                """,
                {"u": st.session_state.username},
            )

            pending_requests = []
            for r in pending_raw:
                c_id, c_sender, c_time = r
                sender_user = db_fetchone("SELECT role FROM users WHERE username = :u", {"u": c_sender})
                sender_alumni = db_fetchone("SELECT name, department, year FROM alumni WHERE username = :u", {"u": c_sender})
                s_role = sender_user[0] if sender_user else "Member"
                s_name = sender_alumni[0] if sender_alumni else None
                s_dept = sender_alumni[1] if sender_alumni else ""
                s_yr = sender_alumni[2] if sender_alumni else ""
                pending_requests.append((c_id, c_sender, c_time, s_role, s_name, s_dept, s_yr))

            if not pending_requests:
                st.markdown(
                    """
                    <div style="text-align:center; padding:24px 10px; color:#94a3b8; font-size:13px;">
                        No pending connection requests. When students or alumni send you requests from the Alumni Directory, they will appear here.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                for req in pending_requests:
                    req_id, req_sender, req_time, req_role, req_name, req_dept, req_yr = req
                    disp_req_name = req_name or f"@{req_sender}"
                    role_badge = f"<span style='background:#dbeafe;color:#2563eb;font-size:11px;font-weight:700;padding:2px 8px;border-radius:8px;'>{str(req_role).capitalize()}</span>" if req_role else ""

                    st.markdown(
                        f"""
                        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:12px 14px; margin-bottom:10px;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <div style="display:flex; align-items:center; gap:10px;">
                                    <div style="width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg, #4f46e5, #2563eb); color:#fff; font-weight:800; display:flex; align-items:center; justify-content:center; font-size:13px;">
                                        {disp_req_name[:2].upper()}
                                    </div>
                                    <div>
                                        <div style="font-weight:800; font-size:14px; color:#0f172a;">{disp_req_name} {role_badge}</div>
                                        <div style="font-size:12px; color:#64748b;">{req_dept or 'Member'} {('• ' + format_batch_year(req_yr)) if req_yr else ''}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        st.markdown('<div class="btn-accept-green">', unsafe_allow_html=True)
                        if st.button("Accept Request", key=f"acc_{req_id}", use_container_width=True):
                            db_exec("UPDATE connections SET status='accepted' WHERE id=:id", {"id": req_id})
                            st.success(f"Connected with @{req_sender}! You can now message each other.")
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    with btn_c2:
                        st.markdown('<div class="btn-decline-red">', unsafe_allow_html=True)
                        if st.button("Decline", key=f"dec_{req_id}", use_container_width=True):
                            db_exec("UPDATE connections SET status='rejected' WHERE id=:id", {"id": req_id})
                            st.info("Request declined.")
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- 2. DIRECTORY ----------------
    elif selected_nav in ["Directory", "Alumni Directory"]:
        st.markdown(
            """
            <div style="margin-bottom: 20px;">
                <h1 style="font-size: 28px; font-weight: 800; color: #0f172a; margin: 0 0 4px 0;">Alumni Directory</h1>
                <div style="font-size: 13px; color: #64748b;">Discover students & alumni. Send connection requests to network and chat.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        q = st.text_input("Search", placeholder="Search alumni by name, department, or company...", label_visibility="collapsed", key="alumni_dir_search_input").strip().lower()

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        rows = db_fetchall(
            """
            SELECT a.username, a.name, a.bio, a.department, a.company, a.linkedin, a.github, a.year,
                   u.email, u.status, u.linkedin_verified, u.role
            FROM alumni a
            LEFT JOIN users u ON u.username = a.username
            ORDER BY a.updated_at DESC
            LIMIT 500
            """
        )

        filtered = []
        for r in rows:
            u, name, bio, dept, comp, li, gh, yr, email, status, verified, role = r
            blob = f"{u} {name or ''} {bio or ''} {dept or ''} {comp or ''} {yr or ''} {role or ''}".lower()
            if q and q not in blob:
                continue
            filtered.append(r)

        if not filtered:
            st.info("No matching alumni profiles found.")
        else:
            for idx, r in enumerate(filtered):
                u, name, bio, dept, comp, li, gh, yr, email, status, verified, role = r
                disp_name = name or f"@{u}"

                formatted_yr = format_batch_year(yr)
                yr_html   = f"<div style='font-size:13px;font-weight:700;color:#2563eb;margin-top:3px;'>{formatted_yr}</div>" if formatted_yr else ""
                dept_html = f"<div style='font-size:12px;color:#475569;margin-top:2px;'>{dept}</div>" if dept else ""
                comp_html = f"<div style='font-size:12px;color:#64748b;margin-top:2px;'>{comp}</div>" if comp else ""

                st.markdown(
                    f"""
                    <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:4px solid #6366f1;
                                border-radius:12px; padding:14px 18px; margin-bottom:8px;
                                display:flex; align-items:center; gap:14px;">
                        {get_avatar_html(u, size=52)}
                        <div style="flex:1;min-width:0;">
                            <div style="font-size:16px;font-weight:800;color:#0f172a;">{disp_name} <span style='font-size:11px;font-weight:600;color:#6366f1;background:#eef2ff;padding:2px 6px;border-radius:6px;'>{str(role or 'Member').capitalize()}</span></div>
                            {yr_html}{dept_html}{comp_html}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Connect / Message Action Buttons
                if u != st.session_state.username:
                    conn = db_fetchone(
                        """
                        SELECT id, sender, receiver, status
                        FROM connections
                        WHERE (sender=:u AND receiver=:target) OR (sender=:target AND receiver=:u)
                        """,
                        {"u": st.session_state.username, "target": u},
                    )

                    btn_cols = st.columns([1.2, 1.4, 1.4, 2])

                    with btn_cols[0]:
                        if not conn or conn[3] in ["rejected", "declined"]:
                            st.markdown('<div class="btn-connect-primary">', unsafe_allow_html=True)
                            if st.button("Connect", key=f"btn_conn_{u}", type="primary", use_container_width=True):
                                if conn:
                                    db_exec(
                                        "UPDATE connections SET sender=:s, receiver=:r, status='pending' WHERE id=:id",
                                        {"s": st.session_state.username, "r": u, "id": conn[0]},
                                    )
                                else:
                                    db_exec(
                                        "INSERT INTO connections (sender, receiver, status) VALUES (:s, :r, 'pending')",
                                        {"s": st.session_state.username, "r": u},
                                    )
                                st.success(f"Connection request sent to {disp_name}!")
                                st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)
                        elif conn[3] == "pending":
                            if conn[1] == st.session_state.username:
                                st.markdown("<div style='background:#fef3c7; color:#d97706; padding:8px 12px; border-radius:10px; font-size:12px; font-weight:700; text-align:center;'>Request Pending</div>", unsafe_allow_html=True)
                            else:
                                st.markdown('<div class="btn-connect-primary">', unsafe_allow_html=True)
                                if st.button("Accept Request", key=f"btn_acc_dir_{u}", type="primary", use_container_width=True):
                                    db_exec("UPDATE connections SET status='accepted' WHERE id=:id", {"id": conn[0]})
                                    st.success(f"Connected with {disp_name}!")
                                    st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)
                        elif conn[3] == "accepted":
                            st.markdown("<div style='background:#dcfce7; color:#16a34a; padding:8px 12px; border-radius:10px; font-size:12px; font-weight:700; text-align:center;'>Connected</div>", unsafe_allow_html=True)

                    with btn_cols[1]:
                        if li:
                            st.link_button("Open LinkedIn", normalize_url(li), use_container_width=True)
                    with btn_cols[2]:
                        if gh:
                            st.link_button("Open GitHub", normalize_url(gh), use_container_width=True)
                else:
                    if li or gh:
                        btn_cols = st.columns([1.4, 1.4, 3])
                        with btn_cols[0]:
                            if li:
                                st.link_button("Open LinkedIn", normalize_url(li), use_container_width=True)
                        with btn_cols[1]:
                            if gh:
                                st.link_button("Open GitHub", normalize_url(gh), use_container_width=True)

                st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    # ---------------- 2.5. GD PREPARATION & AI PRACTICE ----------------
    elif selected_nav == "GD Preparation":
        gd_url = os.getenv("GD_SERVICE_URL", "http://localhost:3000")
        st.markdown(
            f"""
            <div style="margin-bottom: 20px;">
                <div style="display: flex; align-items: center; justify-content: space-between; background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); padding: 24px 28px; border-radius: 16px; color: white; box-shadow: 0 10px 25px -5px rgba(30,27,75,0.25);">
                    <div>
                        <h1 style="font-size: 28px; font-weight: 800; color: #ffffff; margin: 0 0 6px 0; display: flex; align-items: center; gap: 10px;">
                            🎯 GD Preparation & AI Practice
                        </h1>
                        <div style="font-size: 14px; color: #c7d2fe; font-weight: 500;">
                            Interactive Group Discussion simulator powered by AI to help students ace technical & HR group discussions.
                        </div>
                    </div>
                    <a href="{gd_url}" target="_blank" style="background: #ffffff; color: #312e81; padding: 10px 18px; border-radius: 10px; font-weight: 700; text-decoration: none; display: inline-flex; align-items: center; gap: 8px; font-size: 14px;">
                        <span>Open in New Tab</span>
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                    </a>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        import streamlit.components.v1 as components
        if not is_gd_service_ready(3000):
            with st.spinner("⏳ Starting GD Preparation AI module... please wait a moment"):
                start_gd_service()
                for _ in range(12):
                    if is_gd_service_ready(3000):
                        break
                    time.sleep(1)

        components.iframe(gd_url, height=820, scrolling=True)


    # ---------------- 2.6. APTITUDE PREPARATION ----------------
    elif selected_nav == "Aptitude Preparation":
        import random

        APTI_QUESTION_POOL = [
            # ── 1. LOGICAL REASONING (20 Questions) ─────────────────────────
            {"q": "Find the missing number in the series: 2, 6, 12, 20, 30, ?", "opts": ["42", "40", "44", "38"], "ans": "42", "cat": "Reasoning", "exp": "The differences are +4, +6, +8, +10, +12. So 30 + 12 = 42."},
            {"q": "If APPLE is coded as BQQMF, how is MANGO coded?", "opts": ["NBOHP", "NBOIP", "MCOHP", "NBOGO"], "ans": "NBOHP", "cat": "Reasoning", "exp": "Each letter is shifted forward by +1: M->N, A->B, N->O, G->H, O->P."},
            {"q": "A is B's sister. B is C's brother. C is D's father. How is A related to D?", "opts": ["Aunt", "Mother", "Sister", "Grandmother"], "ans": "Aunt", "cat": "Reasoning", "exp": "A is the sister of C (father of D), making A the aunt of D."},
            {"q": "Complete the series: Z, X, V, T, R, ?", "opts": ["P", "Q", "O", "S"], "ans": "P", "cat": "Reasoning", "exp": "Letters decrease by 2 in alphabet position: 26, 24, 22, 20, 18, 16 (P)."},
            {"q": "If 'FISH' is written as 'EHRG', what does 'BIRD' become?", "opts": ["AHQC", "BIQD", "AJQE", "CHSC"], "ans": "AHQC", "cat": "Reasoning", "exp": "Each character is shifted backward by 1: B->A, I->H, R->Q, D->C."},
            {"q": "Pointing to a man, a woman said: 'His mother is the only daughter of my mother.' How is the woman related to the man?", "opts": ["Mother", "Grandmother", "Sister", "Daughter"], "ans": "Mother", "cat": "Reasoning", "exp": "'The only daughter of my mother' is the woman herself. Hence she is the man's mother."},
            {"q": "Which number comes next: 1, 1, 2, 3, 5, 8, 13, ?", "opts": ["21", "20", "18", "24"], "ans": "21", "cat": "Reasoning", "exp": "Fibonacci sequence: each number is the sum of the two preceding numbers (8 + 13 = 21)."},
            {"q": "All roses are flowers. Some flowers fade quickly. Therefore:", "opts": ["Some roses may fade quickly", "All roses fade quickly", "No rose fades quickly", "All flowers are roses"], "ans": "Some roses may fade quickly", "cat": "Reasoning", "exp": "Since only some flowers fade quickly, some roses may or may not fade quickly."},
            {"q": "At 3:15, what is the angle between the hour and minute hand of a clock?", "opts": ["7.5 degrees", "0 degrees", "15 degrees", "22.5 degrees"], "ans": "7.5 degrees", "cat": "Reasoning", "exp": "Minute hand is at 90 degrees. Hour hand moves 30 * 3 + 0.5 * 15 = 97.5 degrees. Difference = 7.5 degrees."},
            {"q": "In a row of 40 students, Riya is 11th from the left. What is her rank from the right?", "opts": ["30th", "29th", "31st", "28th"], "ans": "30th", "cat": "Reasoning", "exp": "Rank from right = Total - Rank from left + 1 = 40 - 11 + 1 = 30th."},
            {"q": "What comes next in the sequence: AZ, BY, CX, DW, ?", "opts": ["EV", "EU", "FV", "EW"], "ans": "EV", "cat": "Reasoning", "exp": "First letter +1 (A->B->C->D->E), second letter -1 (Z->Y->X->W->V)."},
            {"q": "If SUNDAY = 1 and MONDAY = 2, what is FRIDAY?", "opts": ["6", "5", "7", "4"], "ans": "6", "cat": "Reasoning", "exp": "Consecutive days of the week indexed from Sunday (1) to Friday (6)."},
            {"q": "A, B, C ages are in ratio 2:3:4. Their total sum of age is 54. Find B's age.", "opts": ["18", "12", "24", "27"], "ans": "18", "cat": "Reasoning", "exp": "2x + 3x + 4x = 9x = 54 => x = 6. B's age = 3 * 6 = 18."},
            {"q": "A man walks 6 km South, turns left and walks 4 km, then turns left again and walks 6 km. In which direction is he from the starting point?", "opts": ["East", "West", "North", "South"], "ans": "East", "cat": "Reasoning", "exp": "South 6 km and North 6 km cancel out. He is 4 km East of the starting point."},
            {"q": "Find the odd one out: Copper, Silver, Gold, Plastic", "opts": ["Plastic", "Copper", "Silver", "Gold"], "ans": "Plastic", "cat": "Reasoning", "exp": "Plastic is an insulator/polymer, whereas Copper, Silver, and Gold are metallic conductors."},
            {"q": "Statements: All cars are vehicles. All vehicles have wheels. Conclusion: All cars have wheels.", "opts": ["Definitely True", "Definitely False", "Cannot be determined", "Partially True"], "ans": "Definitely True", "cat": "Reasoning", "exp": "By transitive property of syllogism, Cars -> Vehicles -> Wheels, so All cars have wheels."},
            {"q": "If CLOCK is written as KCOLC, how is WATCH written?", "opts": ["HCTAW", "HACTW", "HCTWA", "HWACT"], "ans": "HCTAW", "cat": "Reasoning", "exp": "The letters of the word are simply reversed."},
            {"q": "Look at this series: 7, 10, 8, 11, 9, 12, ... What number should come next?", "opts": ["10", "13", "11", "14"], "ans": "10", "cat": "Reasoning", "exp": "Alternating pattern: +3, -2, +3, -2, +3, -2. 12 - 2 = 10."},
            {"q": "Six friends A, B, C, D, E, F are seated in a circle facing the center. A is opposite D. B is next to A. Where does E sit if C is opposite B?", "opts": ["Between C and D", "Opposite F", "Next to D", "Cannot be determined"], "ans": "Opposite F", "cat": "Reasoning", "exp": "In a 6-person circle, every person has a unique opposite partner. The remaining pair is E and F."},
            {"q": "Today is Monday. After 61 days, it will be which day?", "opts": ["Saturday", "Sunday", "Tuesday", "Wednesday"], "ans": "Saturday", "cat": "Reasoning", "exp": "61 mod 7 = 5 remainder. Monday + 5 days = Saturday."},

            # ── 2. QUANTITATIVE APTITUDE (20 Questions) ─────────────────────
            {"q": "A train 150 m long passes a pole in 15 seconds. What is its speed in km/h?", "opts": ["36", "40", "54", "30"], "ans": "36", "cat": "Quantitative", "exp": "Speed = 150 m / 15 s = 10 m/s. In km/h = 10 * (18/5) = 36 km/h."},
            {"q": "If 20% of a number is 50, what is 80% of that number?", "opts": ["200", "250", "150", "180"], "ans": "200", "cat": "Quantitative", "exp": "Number = 50 / 0.20 = 250. 80% of 250 = 200."},
            {"q": "A shopkeeper sells an item at Rs.600 with a 20% profit. What is the cost price?", "opts": ["Rs.500", "Rs.480", "Rs.520", "Rs.450"], "ans": "Rs.500", "cat": "Quantitative", "exp": "CP = SP / (1 + Profit%) = 600 / 1.20 = Rs.500."},
            {"q": "Two pipes fill a tank in 12 and 18 hours respectively. How long do they take together?", "opts": ["7.2 hours", "6 hours", "8 hours", "9 hours"], "ans": "7.2 hours", "cat": "Quantitative", "exp": "1/12 + 1/18 = 5/36 per hour. Total time = 36 / 5 = 7.2 hours."},
            {"q": "What is the simple interest on Rs.5000 at 8% per annum for 3 years?", "opts": ["Rs.1200", "Rs.1000", "Rs.1500", "Rs.800"], "ans": "Rs.1200", "cat": "Quantitative", "exp": "SI = (P * R * T) / 100 = (5000 * 8 * 3) / 100 = Rs.1200."},
            {"q": "If the ratio of boys to girls is 3:5 and total students are 160, how many boys are there?", "opts": ["60", "80", "100", "40"], "ans": "60", "cat": "Quantitative", "exp": "Boys = (3 / 8) * 160 = 60."},
            {"q": "What is the LCM of 12, 18, and 24?", "opts": ["72", "36", "48", "144"], "ans": "72", "cat": "Quantitative", "exp": "12 = 2^2 * 3, 18 = 2 * 3^2, 24 = 2^3 * 3. LCM = 2^3 * 3^2 = 8 * 9 = 72."},
            {"q": "A car covers 300 km in 5 hours. What is its average speed in km/h?", "opts": ["60 km/h", "50 km/h", "70 km/h", "55 km/h"], "ans": "60 km/h", "cat": "Quantitative", "exp": "Average Speed = Total Distance / Total Time = 300 / 5 = 60 km/h."},
            {"q": "Find the compound interest on Rs.10,000 at 10% per annum for 2 years compounded annually.", "opts": ["Rs.2100", "Rs.2000", "Rs.2200", "Rs.1900"], "ans": "Rs.2100", "cat": "Quantitative", "exp": "Amount = 10000 * (1.1)^2 = 12100. CI = 12100 - 10000 = Rs.2100."},
            {"q": "A number is increased by 25% and then decreased by 20%. What is the net percentage change?", "opts": ["0%", "+5%", "-5%", "+10%"], "ans": "0%", "cat": "Quantitative", "exp": "100 -> 125 -> 125 * 0.80 = 100. Net change = 0%."},
            {"q": "What is 15% of 240?", "opts": ["36", "32", "40", "28"], "ans": "36", "cat": "Quantitative", "exp": "0.15 * 240 = 36."},
            {"q": "If a:b = 2:3 and b:c = 4:5, find the ratio a:c.", "opts": ["8:15", "2:5", "4:9", "6:10"], "ans": "8:15", "cat": "Quantitative", "exp": "a/c = (a/b) * (b/c) = (2/3) * (4/5) = 8/15."},
            {"q": "A person walks 4 km East, then 3 km North. What is the shortest distance from the start?", "opts": ["5 km", "7 km", "4 km", "6 km"], "ans": "5 km", "cat": "Quantitative", "exp": "By Pythagoras theorem: sqrt(4^2 + 3^2) = sqrt(16 + 9) = sqrt(25) = 5 km."},
            {"q": "What is the area of a circle with radius 7 cm? (Take pi = 22/7)", "opts": ["154 sq cm", "144 sq cm", "132 sq cm", "176 sq cm"], "ans": "154 sq cm", "cat": "Quantitative", "exp": "Area = pi * r^2 = (22/7) * 7 * 7 = 154 sq cm."},
            {"q": "If 6 workers complete a job in 10 days, how many days will 4 workers take at the same pace?", "opts": ["15 days", "12 days", "18 days", "20 days"], "ans": "15 days", "cat": "Quantitative", "exp": "Total work = 6 * 10 = 60 man-days. Days for 4 workers = 60 / 4 = 15 days."},
            {"q": "In how many different ways can the letters of the word 'LEAD' be arranged?", "opts": ["24", "12", "6", "120"], "ans": "24", "cat": "Quantitative", "exp": "The word has 4 distinct letters. Permutations = 4! = 4 * 3 * 2 * 1 = 24."},
            {"q": "What is the probability of getting a sum of 7 when two standard dice are rolled?", "opts": ["1/6", "1/12", "5/36", "7/36"], "ans": "1/6", "cat": "Quantitative", "exp": "Favorable pairs: (1,6), (2,5), (3,4), (4,3), (5,2), (6,1) = 6 pairs out of 36. Prob = 6/36 = 1/6."},
            {"q": "A boat travels 24 km downstream in 2 hours and 18 km upstream in 3 hours. Find the boat speed in still water.", "opts": ["9 km/h", "8 km/h", "10 km/h", "7 km/h"], "ans": "9 km/h", "cat": "Quantitative", "exp": "Downstream speed = 12 km/h, Upstream speed = 6 km/h. Speed in still water = (12 + 6)/2 = 9 km/h."},
            {"q": "The average of five consecutive even numbers is 26. What is the largest of these numbers?", "opts": ["30", "28", "32", "26"], "ans": "30", "cat": "Quantitative", "exp": "The numbers are 22, 24, 26, 28, 30. The largest number is 30."},
            {"q": "A vendor buys apples at 6 for Rs.10 and sells them at 4 for Rs.10. Find his profit percentage.", "opts": ["50%", "40%", "33.3%", "25%"], "ans": "50%", "cat": "Quantitative", "exp": "CP of 1 apple = Rs.10/6. SP of 1 apple = Rs.10/4. Profit% = ((10/4 - 10/6) / (10/6)) * 100 = 50%."},

            # ── 3. TECHNICAL MCQ (25 Questions) ────────────────────────────
            {"q": "What is the time complexity of searching an element in a balanced Binary Search Tree?", "opts": ["O(log n)", "O(n)", "O(n^2)", "O(1)"], "ans": "O(log n)", "cat": "Technical", "exp": "In a balanced BST, the tree height is O(log n), so search takes O(log n) time."},
            {"q": "Which data structure operates on a Last-In, First-Out (LIFO) basis?", "opts": ["Stack", "Queue", "LinkedList", "Tree"], "ans": "Stack", "cat": "Technical", "exp": "Stack follows LIFO order where elements inserted last are popped first."},
            {"q": "What does SQL stand for?", "opts": ["Structured Query Language", "Sequential Query Language", "Standard Query Language", "Simple Query Language"], "ans": "Structured Query Language", "cat": "Technical", "exp": "SQL stands for Structured Query Language used to interact with relational databases."},
            {"q": "Which OSI layer is responsible for logical routing of packets?", "opts": ["Network Layer", "Data Link Layer", "Transport Layer", "Session Layer"], "ans": "Network Layer", "cat": "Technical", "exp": "The Network layer (Layer 3) handles IP addressing and packet routing across networks."},
            {"q": "What is the primary key in a relational database?", "opts": ["A unique identifier for each record", "The first column in a table", "A foreign key reference", "An index column"], "ans": "A unique identifier for each record", "cat": "Technical", "exp": "A primary key uniquely identifies each row in a database table without duplicate or NULL values."},
            {"q": "Which sorting algorithm has an average time complexity of O(n log n) and is guaranteed O(n log n) worst case?", "opts": ["Merge Sort", "Bubble Sort", "Quick Sort", "Insertion Sort"], "ans": "Merge Sort", "cat": "Technical", "exp": "Merge Sort consistently divides and merges in O(n log n) even in the worst case."},
            {"q": "What does HTTP stand for in networking?", "opts": ["HyperText Transfer Protocol", "HyperText Transmission Protocol", "High Transfer Text Protocol", "Hyper Transfer Tech Protocol"], "ans": "HyperText Transfer Protocol", "cat": "Technical", "exp": "HTTP is HyperText Transfer Protocol, the foundation for web communication."},
            {"q": "Which of the following is NOT one of the core Object-Oriented Programming (OOP) principles?", "opts": ["Compilation", "Inheritance", "Encapsulation", "Polymorphism"], "ans": "Compilation", "cat": "Technical", "exp": "The 4 core OOP pillars are Encapsulation, Abstraction, Inheritance, and Polymorphism."},
            {"q": "In Python, what is the output of len([1, 2, 3])?", "opts": ["3", "2", "4", "1"], "ans": "3", "cat": "Technical", "exp": "The len() function returns the number of items in an iterable, which is 3."},
            {"q": "What is a Deadlock in operating systems?", "opts": ["A state where two or more processes wait indefinitely for resources held by each other", "A thread that finishes execution early", "A memory overflow condition", "CPU running at 100% capacity"], "ans": "A state where two or more processes wait indefinitely for resources held by each other", "cat": "Technical", "exp": "Deadlock occurs when processes are blocked waiting for resources held by each other."},
            {"q": "What is the result of 2 ** 10 in Python?", "opts": ["1024", "512", "2048", "20"], "ans": "1024", "cat": "Technical", "exp": "The ** operator computes exponentiation: 2^10 = 1024."},
            {"q": "Which application layer protocol is specifically used to send outgoing emails?", "opts": ["SMTP", "HTTP", "FTP", "POP3"], "ans": "SMTP", "cat": "Technical", "exp": "SMTP (Simple Mail Transfer Protocol) is used to push/send emails across servers."},
            {"q": "What is the maximum value that an 8-bit unsigned integer can represent?", "opts": ["255", "256", "127", "128"], "ans": "255", "cat": "Technical", "exp": "An 8-bit unsigned integer ranges from 0 to (2^8 - 1) = 255."},
            {"q": "Which data structure is typically used to implement Breadth-First Search (BFS) in graphs?", "opts": ["Queue", "Stack", "Heap", "Priority Queue"], "ans": "Queue", "cat": "Technical", "exp": "BFS explores neighbors level-by-level using a First-In-First-Out Queue."},
            {"q": "What does RAM stand for in computer hardware?", "opts": ["Random Access Memory", "Read Access Memory", "Rapid Access Module", "Register Access Memory"], "ans": "Random Access Memory", "cat": "Technical", "exp": "RAM stands for Random Access Memory, the main volatile working memory of a computer."},
            {"q": "Which command is commonly used to test network latency and packet reachability?", "opts": ["ping", "tracert", "ipconfig", "netstat"], "ans": "ping", "cat": "Technical", "exp": "The ping command sends ICMP Echo Request messages to test host reachability."},
            {"q": "What does CSS stand for in web development?", "opts": ["Cascading Style Sheets", "Creative Style Script", "Computer Style Sheets", "Colorful Style Syntax"], "ans": "Cascading Style Sheets", "cat": "Technical", "exp": "CSS stands for Cascading Style Sheets, used to style HTML documents."},
            {"q": "Which of the following is an example of a NoSQL document database?", "opts": ["MongoDB", "MySQL", "PostgreSQL", "Oracle DB"], "ans": "MongoDB", "cat": "Technical", "exp": "MongoDB stores data in flexible JSON/BSON document structures, making it a NoSQL database."},
            {"q": "In Python, which of the following data types is immutable?", "opts": ["Tuple", "List", "Dictionary", "Set"], "ans": "Tuple", "cat": "Technical", "exp": "Tuples cannot be modified after creation, making them immutable."},
            {"q": "What is the standard port number for secure HTTPS traffic?", "opts": ["443", "80", "8080", "22"], "ans": "443", "cat": "Technical", "exp": "HTTPS runs on port 443 by default (HTTP runs on port 80)."},
            {"q": "What is the worst-case time complexity of QuickSort?", "opts": ["O(n^2)", "O(n log n)", "O(n)", "O(log n)"], "ans": "O(n^2)", "cat": "Technical", "exp": "When pivot selection is unbalanced (e.g. already sorted list with last element pivot), QuickSort degrades to O(n^2)."},
            {"q": "What does ACID stand for in database transaction management?", "opts": ["Atomicity, Consistency, Isolation, Durability", "Accuracy, Control, Integrity, Data", "Automated, Concurrent, Indexed, Distributed", "Authentication, Cache, Input, Delivery"], "ans": "Atomicity, Consistency, Isolation, Durability", "cat": "Technical", "exp": "ACID properties ensure reliable and fault-tolerant transaction processing in DBMS."},
            {"q": "What is thrashing in an operating system virtual memory context?", "opts": ["High page fault activity causing OS to spend more time swapping than executing", "CPU cache invalidation", "Disk head collision error", "Memory leakage in user space"], "ans": "High page fault activity causing OS to spend more time swapping than executing", "cat": "Technical", "exp": "Thrashing occurs when virtual memory resources are overused, causing non-stop page faults."},
            {"q": "Which layer of the OSI model does a Router operate on?", "opts": ["Network Layer (Layer 3)", "Data Link Layer (Layer 2)", "Transport Layer (Layer 4)", "Physical Layer (Layer 1)"], "ans": "Network Layer (Layer 3)", "cat": "Technical", "exp": "Routers make forwarding decisions using Layer 3 IP addresses."},
            {"q": "In Git version control, which command creates and switches to a new branch simultaneously?", "opts": ["git checkout -b <branch>", "git branch -n <branch>", "git switch -a <branch>", "git commit -b <branch>"], "ans": "git checkout -b <branch>", "cat": "Technical", "exp": "'git checkout -b <name>' creates the branch and immediately checks it out."},

            # ── 4. VERBAL / ENGLISH APTITUDE (15 Questions) ────────────────
            {"q": "Choose the word most opposite in meaning to 'Benevolent':", "opts": ["Malevolent", "Generous", "Kind", "Charitable"], "ans": "Malevolent", "cat": "Verbal", "exp": "Benevolent means wishing good or kind; malevolent means wishing evil or harm."},
            {"q": "Select the correctly spelt word:", "opts": ["Accommodation", "Accomodation", "Acommodation", "Accomodatoin"], "ans": "Accommodation", "cat": "Verbal", "exp": "The correct spelling has double 'c' and double 'm': Accommodation."},
            {"q": "Choose the synonym of 'Eloquent':", "opts": ["Articulate", "Silent", "Clumsy", "Confused"], "ans": "Articulate", "cat": "Verbal", "exp": "Eloquent means fluent or persuasive in speaking or writing, synonymous with articulate."},
            {"q": "Identify the error in this sentence: 'He is one of the best player in the team.'", "opts": ["player (should be players)", "one of", "in the", "He is"], "ans": "player (should be players)", "cat": "Verbal", "exp": "The phrase 'one of the...' must be followed by a plural noun ('players')."},
            {"q": "Fill in the blank with appropriate preposition: 'She is good __ mathematics.'", "opts": ["at", "in", "on", "with"], "ans": "at", "cat": "Verbal", "exp": "The idiom is 'good at' when referring to proficiency in a skill or subject."},
            {"q": "Which word is the antonym of 'Transparent'?", "opts": ["Opaque", "Clear", "Visible", "Glossy"], "ans": "Opaque", "cat": "Verbal", "exp": "Transparent means allowing light through; opaque means impenetrable to light."},
            {"q": "Complete the analogy: Book : Library :: Painting : ?", "opts": ["Gallery", "Museum", "Studio", "Shop"], "ans": "Gallery", "cat": "Verbal", "exp": "A collection of books is in a library; a collection of paintings is in a gallery."},
            {"q": "What does the idiom 'Bite the bullet' mean?", "opts": ["To face a difficult situation with courage", "To get into an argument", "To taste metal", "To act impulsively"], "ans": "To face a difficult situation with courage", "cat": "Verbal", "exp": "'Bite the bullet' means enduring an unavoidable painful or difficult situation with grit."},
            {"q": "Choose the correctly punctuated sentence:", "opts": ["Let's eat, grandma!", "Lets eat, grandma!", "Let's eat grandma!", "Lets eat grandma!"], "ans": "Let's eat, grandma!", "cat": "Verbal", "exp": "The vocative comma before 'grandma' and apostrophe in 'Let's' are required for grammatical sense."},
            {"q": "Find the odd one out: Rose, Lily, Lotus, Mango", "opts": ["Mango", "Rose", "Lily", "Lotus"], "ans": "Mango", "cat": "Verbal", "exp": "Mango is a fruit; Rose, Lily, and Lotus are flowers."},
            {"q": "What is the meaning of the idiom 'A blessing in disguise'?", "opts": ["A good thing that seemed bad at first", "An unexpected prize", "A hidden secret", "A magical gift"], "ans": "A good thing that seemed bad at first", "cat": "Verbal", "exp": "It refers to an apparent misfortune that eventually results in something unexpectedly good."},
            {"q": "Choose the antonym of 'Diligent':", "opts": ["Lazy", "Careful", "Hardworking", "Energetic"], "ans": "Lazy", "cat": "Verbal", "exp": "Diligent means hardworking and conscientious; lazy is its direct antonym."},
            {"q": "Fill in the blank: 'Neither of the students __ completed the assignment.'", "opts": ["has", "have", "were", "are"], "ans": "has", "cat": "Verbal", "exp": "'Neither' is singular and requires the singular verb 'has'."},
            {"q": "Choose the synonym of 'Meticulous':", "opts": ["Thorough", "Careless", "Rapid", "Messy"], "ans": "Thorough", "cat": "Verbal", "exp": "Meticulous means showing great attention to detail; thorough and careful."},
            {"q": "Identify the passive voice of: 'The chef cooked a delicious meal.'", "opts": ["A delicious meal was cooked by the chef.", "A delicious meal is cooked by the chef.", "A delicious meal had been cooked by the chef.", "The meal was being cooked by the chef."], "ans": "A delicious meal was cooked by the chef.", "cat": "Verbal", "exp": "Simple past 'cooked' converts to 'was cooked' in passive voice."},
        ]

        QUESTIONS_PER_ROUND = 20

        def get_shuffled_round_questions():
            sampled = random.sample(APTI_QUESTION_POOL, QUESTIONS_PER_ROUND)
            round_qs = []
            for q in sampled:
                q_copy = dict(q)
                shuffled_opts = list(q["opts"])
                random.shuffle(shuffled_opts)
                q_copy["opts"] = shuffled_opts
                round_qs.append(q_copy)
            return round_qs

        # ── Init session state ──
        if "apti_round_no" not in st.session_state:
            st.session_state.apti_round_no = 1
        if "apti_questions_shuffled" not in st.session_state or "apti_questions" not in st.session_state or len(st.session_state.get("apti_questions", [])) == 0:
            st.session_state.apti_questions = get_shuffled_round_questions()
            st.session_state.apti_questions_shuffled = True
            st.session_state.apti_current_idx = 0
            st.session_state.apti_answers = {}
            st.session_state.apti_submitted = False

        # ── Scoped Styling for Aptitude Test UI ──
        st.markdown("""
        <style>
        /* 1. Force all non-primary buttons to white with dark slate text */
        button[kind="secondary"],
        .stButton > button:not([kind="primary"]):not([kind="primaryFormSubmit"]) {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1.5px solid #cbd5e1 !important;
            font-weight: 700 !important;
            border-radius: 10px !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
        }
        button[kind="secondary"]:hover,
        .stButton > button:not([kind="primary"]):not([kind="primaryFormSubmit"]):hover {
            background-color: #f1f5f9 !important;
            color: #0f172a !important;
            border-color: #94a3b8 !important;
        }

        /* 2. Palette Buttons */
        div[class*="st-key-pal_"] button {
            height: 38px !important;
            min-height: 38px !important;
            padding: 2px 4px !important;
            font-size: 13px !important;
            font-weight: 800 !important;
            border-radius: 8px !important;
        }
        /* Answered button in palette: soft green with emerald border */
        div[class*="st-key-pal_ans_"] button:not([kind="primary"]) {
            background-color: #ecfdf5 !important;
            color: #065f46 !important;
            border: 1.5px solid #10b981 !important;
        }
        div[class*="st-key-pal_ans_"] button:not([kind="primary"]):hover {
            background-color: #d1fae5 !important;
            color: #064e3b !important;
            border-color: #059669 !important;
        }
        /* Unanswered button in palette: clean white with dark slate text */
        div[class*="st-key-pal_unans_"] button:not([kind="primary"]) {
            background-color: #ffffff !important;
            color: #334155 !important;
            border: 1.5px solid #cbd5e1 !important;
        }
        div[class*="st-key-pal_unans_"] button:not([kind="primary"]):hover {
            background-color: #f1f5f9 !important;
            color: #0f172a !important;
            border-color: #94a3b8 !important;
        }
        /* Active button in palette: primary blue */
        div[class*="st-key-pal_"] button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb, #4f46e5) !important;
            color: #ffffff !important;
            border: none !important;
            box-shadow: 0 2px 8px rgba(37,99,235,0.35) !important;
        }

        /* 3. RADIO OPTIONS - Strictly scoped to apti_quiz_radio_box container only */
        div[class*="st-key-apti_quiz_radio_box"] div[data-testid="stRadio"] {
            margin-top: 12px !important;
            background: transparent !important;
        }
        div[class*="st-key-apti_quiz_radio_box"] div[data-testid="stRadio"] > div[role="radiogroup"] {
            display: flex !important;
            flex-direction: column !important;
            gap: 10px !important;
        }
        div[class*="st-key-apti_quiz_radio_box"] div[data-testid="stRadio"] label[data-baseweb="radio"] {
            background-color: #ffffff !important;
            border: 1.5px solid #cbd5e1 !important;
            border-radius: 12px !important;
            padding: 12px 18px !important;
            margin: 0 !important;
            cursor: pointer !important;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04) !important;
            transition: all 0.15s ease-in-out !important;
        }
        div[class*="st-key-apti_quiz_radio_box"] div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {
            border-color: #6366f1 !important;
            background-color: #f8faff !important;
            transform: translateX(3px) !important;
        }
        div[class*="st-key-apti_quiz_radio_box"] div[data-testid="stRadio"] label,
        div[class*="st-key-apti_quiz_radio_box"] div[data-testid="stRadio"] label *,
        div[class*="st-key-apti_quiz_radio_box"] div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p,
        div[class*="st-key-apti_quiz_radio_box"] div[data-testid="stRadio"] p,
        div[class*="st-key-apti_quiz_radio_box"] div[data-testid="stRadio"] span,
        div[class*="st-key-apti_quiz_radio_box"] div[data-testid="stRadio"] div {
            color: #0f172a !important;
            opacity: 1 !important;
            visibility: visible !important;
        }
        div[class*="st-key-apti_quiz_radio_box"] div[data-testid="stRadio"] label[data-baseweb="radio"] p {
            font-size: 15px !important;
            font-weight: 600 !important;
            line-height: 1.4 !important;
            margin: 0 0 0 6px !important;
        }

        /* ── Keep Sidebar Radio Navigation strictly compact as in original design ── */
        [data-testid="stSidebar"] div[data-testid="stRadio"] {
            margin: 0 !important;
            padding: 0 !important;
        }
        [data-testid="stSidebar"] div[data-testid="stRadio"] > div[role="radiogroup"] {
            gap: 2px !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        [data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"] {
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 4px 8px !important;
            margin: 0 !important;
            transform: none !important;
        }
        [data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {
            background: rgba(255, 255, 255, 0.08) !important;
            border: none !important;
            transform: none !important;
        }
        [data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"] * {
            color: #c7d2fe !important;
        }
        [data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"] p {
            color: #c7d2fe !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            line-height: 1.2 !important;
            margin: 0 !important;
        }

        /* 4. Action buttons styling */
        div[class*="st-key-apti_btn_prev"] button {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1.5px solid #cbd5e1 !important;
            font-weight: 700 !important;
        }
        div[class*="st-key-apti_btn_prev"] button:hover {
            background-color: #f1f5f9 !important;
            color: #0f172a !important;
            border-color: #94a3b8 !important;
        }
        div[class*="st-key-apti_btn_clear"] button {
            background-color: #fff1f2 !important;
            color: #e11d48 !important;
            border: 1.5px solid #fecdd3 !important;
            font-weight: 700 !important;
        }
        div[class*="st-key-apti_btn_clear"] button:hover {
            background-color: #ffe4e6 !important;
            color: #be123c !important;
            border-color: #fda4af !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # ── Page Header ──
        st.markdown("""
        <div style="background: linear-gradient(135deg, #064e3b 0%, #065f46 50%, #047857 100%);
                    padding: 24px 28px; border-radius: 16px; color: white;
                    box-shadow: 0 10px 25px -5px rgba(6,78,59,0.3); margin-bottom: 20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                <div>
                    <h1 style="font-size:28px; font-weight:800; color:#fff; margin:0 0 6px 0;">
                        Aptitude Preparation
                    </h1>
                    <div style="font-size:14px; color:#a7f3d0; font-weight:500;">
                        20 Practice MCQs per round &nbsp;·&nbsp; Logical Reasoning &nbsp;·&nbsp; Quantitative &nbsp;·&nbsp; Technical &nbsp;·&nbsp; Verbal
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        q_list    = st.session_state.apti_questions
        cur_idx   = st.session_state.apti_current_idx
        answers   = st.session_state.apti_answers
        submitted = st.session_state.apti_submitted

        # ── RESULTS SCREEN ──
        if submitted:
            correct   = sum(1 for i, q in enumerate(q_list) if answers.get(i) == q["ans"])
            answered  = sum(1 for i in range(QUESTIONS_PER_ROUND) if i in answers and answers[i] is not None)
            skipped   = QUESTIONS_PER_ROUND - answered
            wrong     = answered - correct
            total     = QUESTIONS_PER_ROUND
            pct       = int((correct / total) * 100)

            if pct >= 80:
                grade_col, grade_label = "#16a34a", "Outstanding! Placement Ready!"
            elif pct >= 65:
                grade_col, grade_label = "#0284c7", "Great Performance!"
            elif pct >= 50:
                grade_col, grade_label = "#d97706", "Good Effort! Keep Practicing!"
            elif pct >= 35:
                grade_col, grade_label = "#ea580c", "Fair! Focus on Weak Areas"
            else:
                grade_col, grade_label = "#dc2626", "Needs Improvement! Try Again"

            # Main Score Card
            st.markdown(f"""
            <div style="text-align:center; padding:32px 24px; background:linear-gradient(180deg, #f0fdf4 0%, #ffffff 100%);
                        border-radius:18px; border:2px solid #86efac; box-shadow:0 8px 24px rgba(22,163,74,0.12); margin-bottom:24px;">
                <div style="font-size:44px; font-weight:900; color:{grade_col}; margin:10px 0 4px 0;">
                    {correct} / {total} Correct
                </div>
                <div style="font-size:20px; font-weight:700; color:{grade_col};">{grade_label}</div>
                <div style="font-size:14px; color:#6b7280; margin-top:8px;">Round {st.session_state.apti_round_no} Final Result &nbsp;·&nbsp; Overall Score: <b>{pct}%</b></div>
            </div>
            """, unsafe_allow_html=True)

            # Answer Review
            st.markdown("#### Detailed Answer Review & Solutions")
            for i, q in enumerate(q_list):
                user_ans   = answers.get(i, None)
                if user_ans is None:
                    status_text = "Skipped"
                    bg          = "#f9fafb"
                    border_col  = "#9ca3af"
                elif user_ans == q["ans"]:
                    status_text = "Correct"
                    bg          = "#f0fdf4"
                    border_col  = "#16a34a"
                else:
                    status_text = "Incorrect"
                    bg          = "#fff1f2"
                    border_col  = "#dc2626"

                user_display = f"<b>{user_ans}</b>" if user_ans else "<i style='color:#9ca3af;'>Not answered</i>"
                exp_text = q.get("exp", "")

                st.markdown(f"""
                <div style="background:{bg}; border-radius:12px; padding:16px 20px;
                            margin-bottom:12px; border-left:5px solid {border_col}; box-shadow:0 2px 8px rgba(0,0,0,0.04);">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                        <span style="font-weight:700; font-size:15px; color:#111827;">
                            Q{i+1}. [{q['cat']}] {q['q']}
                        </span>
                        <span style="font-size:12px; font-weight:700; color:{border_col}; text-transform:uppercase;">{status_text}</span>
                    </div>
                    <div style="font-size:13.5px; color:#374151; margin-top:6px;">
                        Your Choice: {user_display} &nbsp;&nbsp;|&nbsp;&nbsp; Correct Answer: <b style="color:#16a34a;">{q['ans']}</b>
                    </div>
                    {f'<div style="font-size:13px; color:#4b5563; background:rgba(0,0,0,0.03); padding:8px 12px; border-radius:8px; margin-top:8px;"><b>Explanation:</b> {exp_text}</div>' if exp_text else ''}
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Start Next Round (Different Questions)", type="primary", use_container_width=True):
                st.session_state.apti_round_no    += 1
                st.session_state.apti_questions    = get_shuffled_round_questions()
                st.session_state.apti_questions_shuffled = True
                st.session_state.apti_current_idx  = 0
                st.session_state.apti_answers      = {}
                st.session_state.apti_submitted    = False
                st.rerun()

        # ── QUIZ SCREEN ──
        else:
            answered_count = sum(1 for i in range(QUESTIONS_PER_ROUND) if i in answers and answers[i] is not None)
            progress = answered_count / QUESTIONS_PER_ROUND

            # Progress Bar & Round Status
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="font-weight:700; color:#065f46; font-size:15px;">
                    🎯 Round {st.session_state.apti_round_no} &nbsp;·&nbsp; Question {cur_idx + 1} of {QUESTIONS_PER_ROUND}
                </span>
                <span style="font-size:13px; font-weight:600; color:#047857;">
                    {answered_count} of {QUESTIONS_PER_ROUND} Answered ({int(progress * 100)}%)
                </span>
            </div>
            """, unsafe_allow_html=True)
            st.progress(progress)

            # ── Question Palette / Navigator (Quick jump to any question) ──
            st.markdown("<div style='font-size:12px; font-weight:700; color:#6b7280; text-transform:uppercase; margin:14px 0 6px 0;'>Question Palette:</div>", unsafe_allow_html=True)
            pal_cols1 = st.columns(10)
            pal_cols2 = st.columns(10)
            pal_cols = pal_cols1 + pal_cols2

            for i, pcol in enumerate(pal_cols):
                is_curr = (i == cur_idx)
                is_ans  = (i in answers and answers[i] is not None)
                label   = f"✓ {i+1}" if is_ans else f"{i+1}"
                btn_type = "primary" if is_curr else "secondary"
                btn_prefix = "ans" if is_ans else "unans"

                with pcol:
                    if st.button(label, key=f"pal_{btn_prefix}_{i}_r{st.session_state.apti_round_no}", type=btn_type, use_container_width=True):
                        st.session_state.apti_current_idx = i
                        st.rerun()

            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

            # Current Question Card
            q = q_list[cur_idx]
            st.markdown(f"""
            <div style="background:#ffffff; border-radius:14px; padding:24px 28px;
                        box-shadow:0 4px 16px rgba(0,0,0,0.06); margin:12px 0 18px 0;
                        border-left:5px solid #059669; border-top:1px solid #e5e7eb; border-right:1px solid #e5e7eb; border-bottom:1px solid #e5e7eb;">
                <div style="font-size:11px; font-weight:700; color:#059669;
                            text-transform:uppercase; letter-spacing:1px; margin-bottom:10px;">
                    Category: {q['cat']}
                </div>
                <div style="font-size:18px; font-weight:700; color:#111827; line-height:1.5;">
                    Q{cur_idx + 1}. {q['q']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Options Radio with high-contrast card styling
            prev_ans = answers.get(cur_idx, None)
            safe_index = q["opts"].index(prev_ans) if prev_ans in q["opts"] else None

            with st.container(key="apti_quiz_radio_box"):
                user_choice = st.radio(
                    "Select your answer:",
                    options=q["opts"],
                    index=safe_index,
                    key=f"apti_q_{cur_idx}_r{st.session_state.apti_round_no}",
                )

            # If option selected, update session_state answers
            if user_choice is not None and user_choice != prev_ans:
                st.session_state.apti_answers[cur_idx] = user_choice

            # Navigation buttons
            st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
            col_prev, col_clear, col_next = st.columns([1, 1, 1])

            with col_prev:
                if cur_idx > 0:
                    if st.button("⬅ Previous", key=f"apti_btn_prev_{cur_idx}", use_container_width=True):
                        if user_choice is not None:
                            st.session_state.apti_answers[cur_idx] = user_choice
                        st.session_state.apti_current_idx -= 1
                        st.rerun()

            with col_clear:
                if cur_idx in answers and answers[cur_idx] is not None:
                    if st.button("✖ Clear Answer", key=f"apti_btn_clear_{cur_idx}", use_container_width=True):
                        st.session_state.apti_answers.pop(cur_idx, None)
                        st.rerun()

            with col_next:
                if cur_idx < QUESTIONS_PER_ROUND - 1:
                    if st.button("Next ➡", key=f"apti_btn_next_{cur_idx}", type="primary", use_container_width=True):
                        if user_choice is not None:
                            st.session_state.apti_answers[cur_idx] = user_choice
                        st.session_state.apti_current_idx += 1
                        st.rerun()
                else:
                    if st.button("✅ Submit Exam", key=f"apti_btn_submit_{cur_idx}", type="primary", use_container_width=True):
                        if user_choice is not None:
                            st.session_state.apti_answers[cur_idx] = user_choice
                        st.session_state.apti_submitted = True
                        st.rerun()

    # ---------------- 3. MESSAGES / CHAT (WHATSAPP UI) ----------------
    elif selected_nav == "Messages":
        # Get all accepted connected peers
        connected_peers_raw = db_fetchall(
            """
            SELECT CASE WHEN sender = :u THEN receiver ELSE sender END AS peer
            FROM connections
            WHERE (sender = :u OR receiver = :u) AND status = 'accepted'
            """,
            {"u": st.session_state.username},
        )
        connected_peers = [p[0] for p in connected_peers_raw]

        if not connected_peers:
            st.markdown(
                """
                <div class="admin-card-box" style="text-align:center; padding:48px 20px; margin-top:20px;">
                    <div style="font-size:20px; font-weight:800; color:#111b21; margin-bottom:8px;">No Connected Chats Yet</div>
                    <div style="font-size:14px; color:#64748b; max-width:480px; margin:0 auto 18px auto;">
                        To chat, send connection requests to students and alumni in the <b>Alumni Directory</b>, or accept incoming requests on your <b>Dashboard</b>.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            # Handle 1-click contact selection via URL query param
            if "chat" in st.query_params and st.query_params["chat"] in connected_peers:
                st.session_state.active_wa_chat = st.query_params["chat"]
                try:
                    del st.query_params["chat"]
                except Exception:
                    pass

            if "active_wa_chat" not in st.session_state or st.session_state.active_wa_chat not in connected_peers:
                st.session_state.active_wa_chat = connected_peers[0]

            # 2-Column WhatsApp Web Layout
            col_chats, col_thread = st.columns([1.1, 2.0])

            # ── LEFT PANE: WhatsApp Chat List ──
            with col_chats:
                st.markdown(
                    """<div style="background:#f0f2f5; padding:12px 14px; border-radius:14px 14px 0 0; border:1px solid #e2e8f0; border-bottom:none; display:flex; justify-content:space-between; align-items:center;"><div style="font-size:20px; font-weight:800; color:#111b21;">Chats</div></div>""",
                    unsafe_allow_html=True,
                )

                wa_search = st.text_input("Search chats", placeholder="Search or start a new chat...", label_visibility="collapsed", key="wa_search_input").strip().lower()

                st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

                # Filter peers based on search
                filtered_peers = []
                for peer in connected_peers:
                    p_info = load_profile_from_db(peer)
                    p_name = p_info["name"] or f"@{peer}"
                    if wa_search and (wa_search not in peer.lower() and wa_search not in p_name.lower()):
                        continue
                    filtered_peers.append((peer, p_name))

                if not filtered_peers:
                    st.caption("No matching contacts found.")
                else:
                    for peer, p_name in filtered_peers:
                        c_row = db_fetchone(
                            "SELECT cleared_at FROM cleared_chats WHERE username=:u AND peer=:p",
                            {"u": st.session_state.username, "p": peer},
                        )
                        last_cleared_at = c_row[0] if c_row else None

                        if last_cleared_at:
                            last_msg_row = db_fetchone(
                                """
                                SELECT message, created_at, sender, is_read
                                FROM messages
                                WHERE ((sender=:u AND receiver=:p) OR (sender=:p AND receiver=:u))
                                  AND created_at > :c_at
                                ORDER BY created_at DESC
                                LIMIT 1
                                """,
                                {"u": st.session_state.username, "p": peer, "c_at": last_cleared_at},
                            )
                            unread_row = db_fetchone(
                                """
                                SELECT COUNT(*) FROM messages
                                WHERE sender=:p AND receiver=:u AND is_read=0
                                  AND created_at > :c_at
                                """,
                                {"u": st.session_state.username, "p": peer, "c_at": last_cleared_at},
                            )
                        else:
                            last_msg_row = db_fetchone(
                                """
                                SELECT message, created_at, sender, is_read
                                FROM messages
                                WHERE (sender=:u AND receiver=:p) OR (sender=:p AND receiver=:u)
                                ORDER BY created_at DESC
                                LIMIT 1
                                """,
                                {"u": st.session_state.username, "p": peer},
                            )
                            unread_row = db_fetchone(
                                """
                                SELECT COUNT(*) FROM messages
                                WHERE sender=:p AND receiver=:u AND is_read=0
                                """,
                                {"u": st.session_state.username, "p": peer},
                            )

                        unread_count = unread_row[0] if unread_row else 0

                        last_snippet = "Tap to chat"
                        last_time_str = ""
                        check_prefix_html = ""

                        if last_msg_row:
                            m_text, m_time, m_sender, m_is_read = last_msg_row
                            last_snippet = (m_text[:22] + "...") if len(m_text) > 22 else m_text
                            last_time_str = str(m_time)[11:16] if m_time else ""
                            if m_sender == st.session_state.username:
                                tick_color = "#38bdf8" if m_is_read == 1 else "#94a3b8"
                                check_prefix_html = f'<span style="color:{tick_color}; font-weight:800; font-size:13px;">✓✓ </span>'

                        is_active = (st.session_state.active_wa_chat == peer)
                        bg_color = "#f1f5f9" if is_active else "#ffffff"
                        card_border = "border: 1px solid #cbd5e1;" if is_active else "border: 1px solid #f1f5f9;"
                        border_accent = '<div style="position:absolute; left:0; top:0; bottom:0; width:4px; background:#059669; border-top-left-radius:14px; border-bottom-left-radius:14px;"></div>' if is_active else ''

                        # WhatsApp-style unread badge
                        has_unread = unread_count > 0 and not is_active
                        if has_unread:
                            badge_html = f'<div style="background:#25d366; color:#ffffff; border-radius:50%; min-width:20px; height:20px; display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:800; padding:0 4px; flex-shrink:0;">{unread_count}</div>'
                            last_time_color = "#25d366"
                            snippet_color = "#0f172a"
                            snippet_weight = "600"
                        else:
                            badge_html = ""
                            last_time_color = "#64748b"
                            snippet_color = "#64748b"
                            snippet_weight = "400"

                        # WhatsApp Contact Card with unread badge
                        card_html = f"""<div class="wa-contact-card-item" style="background:{bg_color}; {card_border} padding:12px 14px; border-radius:14px; display:flex; align-items:center; gap:12px; position:relative; box-shadow:0 1px 3px rgba(0,0,0,0.03); height:72px; box-sizing:border-box;">{border_accent}{get_avatar_html(peer, size=44)}<div style="flex:1; min-width:0; overflow:hidden;"><div style="display:flex; justify-content:space-between; align-items:center;"><div style="font-weight:700; font-size:15px; color:#0f172a; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{p_name}</div><div style="font-size:12px; color:{last_time_color}; flex-shrink:0; font-weight:{'700' if has_unread else '400'};">{last_time_str}</div></div><div style="display:flex; justify-content:space-between; align-items:center; margin-top:3px;"><div style="font-size:13px; color:{snippet_color}; font-weight:{snippet_weight}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; flex:1;">{check_prefix_html}{last_snippet}</div>{badge_html}</div></div></div>"""
                        st.markdown(card_html, unsafe_allow_html=True)
                        if st.button(" ", key=f"btn_card_{peer}", use_container_width=True):
                            st.session_state.active_wa_chat = peer
                            st.rerun()

            # ── RIGHT PANE: WhatsApp Active Chat Window ──
            with col_thread:
                active_target = st.session_state.active_wa_chat
                target_info = load_profile_from_db(active_target)
                target_display = target_info["name"] or f"@{active_target}"

                # Mark incoming messages from active target as read (turns ticks from gray to blue)
                db_exec(
                    """
                    UPDATE messages SET is_read = 1
                    WHERE receiver = :me AND sender = :target AND is_read = 0
                    """,
                    {"me": st.session_state.username, "target": active_target},
                )

                # Calculate real online/offline status
                recent_act = db_fetchone(
                    """
                    SELECT created_at FROM messages
                    WHERE sender = :u
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    {"u": active_target},
                )
                is_online = False
                if recent_act and recent_act[0]:
                    if (datetime.now() - recent_act[0]).total_seconds() < 600:
                        is_online = True

                status_label = "● online" if is_online else "offline"
                status_color = "#10b981" if is_online else "#8696a0"

                # WhatsApp Seamless Header Bar
                with st.container(key="wa_chat_header"):
                    hdr_col1, hdr_col2 = st.columns([1, 0.08], gap="small", vertical_alignment="center")
                    with hdr_col1:
                        st.markdown(
                            f"""
                            <div style="display:flex; align-items:center; gap:12px;">
                                {get_avatar_html(active_target, size=40)}
                                <div style="flex:1; min-width:0;">
                                    <div style="font-weight:800; font-size:15px; color:#111b21; margin:0; line-height:1.2; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{target_display}</div>
                                    <div style="font-size:11px; color:{status_color}; font-weight:600; margin-top:2px;">{status_label}</div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    with hdr_col2:
                        with st.popover("⋮", help="Chat options"):
                            st.markdown(f"<div style='font-weight:700; font-size:13px; color:#0f172a; margin-bottom:8px; border-bottom:1px solid #e2e8f0; padding-bottom:6px;'><b>{target_display}</b></div>", unsafe_allow_html=True)
                            if st.button("Delete chat", key=f"delete_chat_{active_target}", use_container_width=True):
                                db_exec(
                                    """
                                    INSERT INTO cleared_chats (username, peer, cleared_at)
                                    VALUES (:u, :p, CURRENT_TIMESTAMP)
                                    ON DUPLICATE KEY UPDATE cleared_at = CURRENT_TIMESTAMP
                                    """,
                                    {"u": st.session_state.username, "p": active_target},
                                )
                                st.success("Chat deleted for you!")
                                st.rerun()

                # Fetch chat history for this user respecting per-user cleared_chats
                c_row = db_fetchone(
                    "SELECT cleared_at FROM cleared_chats WHERE username=:u AND peer=:p",
                    {"u": st.session_state.username, "p": active_target},
                )
                last_cleared_at = c_row[0] if c_row else None

                if last_cleared_at:
                    chat_messages = db_fetchall(
                        """
                        SELECT sender, receiver, message, created_at, is_read
                        FROM messages
                        WHERE ((sender=:u AND receiver=:target) OR (sender=:target AND receiver=:u))
                          AND created_at > :c_at
                        ORDER BY created_at ASC
                        """,
                        {"u": st.session_state.username, "target": active_target, "c_at": last_cleared_at},
                    )
                else:
                    chat_messages = db_fetchall(
                        """
                        SELECT sender, receiver, message, created_at, is_read
                        FROM messages
                        WHERE (sender=:u AND receiver=:target) OR (sender=:target AND receiver=:u)
                        ORDER BY created_at ASC
                        """,
                        {"u": st.session_state.username, "target": active_target},
                    )

                # Assemble messages with reverse layout so latest message stays pinned to bottom
                chat_bubbles = []
                for cmsg in reversed(chat_messages):
                    csender, creceiv, ctext, ctime, c_is_read = cmsg
                    is_me = (csender == st.session_state.username)
                    msg_time_str = str(ctime)[11:16] if ctime else ""
                    clean_text = html.escape(ctext).replace("\n", "<br>")

                    if is_me:
                        tick_color = "#53bdeb" if c_is_read == 1 else "#8696a0"
                        b = (
                            f'<div style="display:flex;justify-content:flex-end;margin-bottom:8px;width:100%;">'
                            f'<div style="background:#d9fdd3;color:#111b21;border-radius:10px 10px 0px 10px;padding:7px 12px;max-width:75%;box-shadow:0 1px 2px rgba(11,20,26,0.12);font-size:14px;line-height:1.35;word-wrap:break-word;">'
                            f'<div>{clean_text}</div>'
                            f'<div style="font-size:10px;color:#667781;text-align:right;margin-top:2px;display:flex;justify-content:flex-end;align-items:center;gap:4px;">'
                            f'<span>{msg_time_str}</span><span style="color:{tick_color};font-weight:800;">✓✓</span>'
                            f'</div></div></div>'
                        )
                    else:
                        b = (
                            f'<div style="display:flex;justify-content:flex-start;margin-bottom:8px;width:100%;">'
                            f'<div style="background:#ffffff;color:#111b21;border-radius:10px 10px 10px 0px;padding:7px 12px;max-width:75%;box-shadow:0 1px 2px rgba(11,20,26,0.12);font-size:14px;line-height:1.35;word-wrap:break-word;">'
                            f'<div>{clean_text}</div>'
                            f'<div style="font-size:10px;color:#667781;text-align:right;margin-top:2px;">{msg_time_str}</div>'
                            f'</div></div>'
                        )
                    chat_bubbles.append(b)

                if not chat_bubbles:
                    chat_bubbles = ['<div style="text-align:center;padding:40px 10px;color:#667781;font-size:13px;">Messages are private & secure. Send a message to begin!</div>']

                all_bubbles_html = "".join(chat_bubbles)
                canvas_html = (
                    f'<div class="wa-chat-canvas" style="background:#efeae2;background-image:radial-gradient(#dfd7cb 0.75px,transparent 0.75px);background-size:14px 14px;border:1px solid #e2e8f0;border-top:none;border-bottom:none;padding:16px 14px;height:420px;max-height:420px;overflow-y:auto;display:flex;flex-direction:column-reverse;">'
                    f'{all_bubbles_html}'
                    f'</div>'
                )
                st.markdown(canvas_html, unsafe_allow_html=True)

                # WhatsApp Message Input Bar - Stays fixed below canvas
                with st.form("wa_chat_send_form", clear_on_submit=True):
                    in_col, btn_col = st.columns([5.5, 1.2])
                    with in_col:
                        msg_text = st.text_input("Type a message", placeholder="Type a message...", label_visibility="collapsed")
                    with btn_col:
                        sent = st.form_submit_button("Send", use_container_width=True)

                    if sent and msg_text.strip():
                        db_exec(
                            """
                            INSERT INTO messages (sender, receiver, message, is_read)
                            VALUES (:s, :r, :m, 0)
                            """,
                            {"s": st.session_state.username, "r": active_target, "m": msg_text.strip()},
                        )
                        st.rerun()



    # ---------------- 4. MY PROFILE ----------------
    elif selected_nav == "My Profile":
        st.markdown(
            """
            <div style="margin-bottom: 20px;">
                <h1 style="font-size: 28px; font-weight: 800; color: #0f172a; margin: 0 0 4px 0;">My Profile</h1>
                <div style="font-size: 13px; color: #64748b;">Manage your account preferences, academic history, and contact details.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        my_avatar_html = get_avatar_html(st.session_state.username, size=90)
        st.markdown(
            f"""<div style="display:flex; flex-direction:column; align-items:center; justify-content:center; margin-bottom:20px; padding:16px; background:#ffffff; border-radius:16px; border:1px solid #e2e8f0; box-shadow:0 1px 3px rgba(0,0,0,0.03);">{my_avatar_html}<div style="font-size:18px; font-weight:800; color:#0f172a; margin-top:10px;">{p["name"] or st.session_state.username}</div><div style="font-size:13px; color:#64748b;">@{st.session_state.username}</div></div>""",
            unsafe_allow_html=True,
        )

        st.subheader("Profile Details")

        li_email = ""
        if st.session_state.get("linkedin_profile"):
            li_email = st.session_state.linkedin_profile.get("email") or ""

        with st.form("profile_form", clear_on_submit=False):
            st.markdown('<div style="font-weight:700; font-size:14px; color:#0f172a; margin-bottom:4px;">Full Name</div>', unsafe_allow_html=True)
            name = st.text_input("Full Name", value=p["name"], placeholder="Enter your full name (e.g. Abhishek Khangar)", label_visibility="collapsed")

            st.markdown('<div style="font-weight:700; font-size:14px; color:#0f172a; margin-bottom:4px; margin-top:10px;">Email Address</div>', unsafe_allow_html=True)
            email = st.text_input("Email (from signup)", value=(p["email"] or li_email), placeholder="Enter your email address (e.g. example@gmail.com)", label_visibility="collapsed")

            st.markdown('<div style="font-weight:700; font-size:14px; color:#0f172a; margin-bottom:4px; margin-top:10px;">Bio / About You</div>', unsafe_allow_html=True)
            bio = st.text_area("Bio", value=p["bio"], placeholder="Write a brief bio about yourself, interests, skills, or achievements...", label_visibility="collapsed")

            st.markdown('<div style="font-weight:700; font-size:14px; color:#0f172a; margin-bottom:4px; margin-top:10px;">LinkedIn Profile URL</div>', unsafe_allow_html=True)
            linkedin_url = st.text_input("LinkedIn Profile URL", value=p["linkedin"], placeholder="https://www.linkedin.com/in/your-profile", label_visibility="collapsed")

            st.markdown('<div style="font-weight:700; font-size:14px; color:#0f172a; margin-bottom:4px; margin-top:10px;">GitHub Profile URL</div>', unsafe_allow_html=True)
            github_url = st.text_input("GitHub URL", value=p["github"], placeholder="https://github.com/your-username", label_visibility="collapsed")

            st.markdown('<div style="font-weight:700; font-size:14px; color:#0f172a; margin-bottom:4px; margin-top:10px;">Batch / Graduation Years</div>', unsafe_allow_html=True)
            year = st.text_input("Batch / Years", value=p["year"], placeholder="e.g. 2023 - 2027", label_visibility="collapsed")

            st.markdown('<div style="font-weight:700; font-size:14px; color:#0f172a; margin-bottom:4px; margin-top:10px;">Department / Major</div>', unsafe_allow_html=True)
            dept = st.text_input("Department", value=p["department"], placeholder="e.g. Computer Science & Engineering", label_visibility="collapsed")

            st.markdown('<div style="font-weight:700; font-size:14px; color:#0f172a; margin-bottom:4px; margin-top:10px;">Current Company / Role</div>', unsafe_allow_html=True)
            company = st.text_input("Company / Role", value=p["company"], placeholder="e.g. Software Engineer at Google / Student", label_visibility="collapsed")

            st.markdown('<div style="font-weight:700; font-size:14px; color:#0f172a; margin-bottom:4px; margin-top:10px;">Profile Picture</div>', unsafe_allow_html=True)
            pic = st.file_uploader("Profile picture (optional)", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
            submitted = st.form_submit_button("Save Profile")

        if submitted:
            li = normalize_url(linkedin_url)
            gh = normalize_url(github_url)

            current_pic = db_fetchone("SELECT profile_pic FROM alumni WHERE username=:u", {"u": st.session_state.username})
            pic_path = (current_pic[0] if current_pic else "") or ""

            if pic is not None:
                os.makedirs("profile_pics", exist_ok=True)
                pic_path = os.path.join("profile_pics", f"{st.session_state.username}_avatar.png")
                try:
                    img = Image.open(pic)
                    img = img.convert("RGB")
                    w, h = img.size
                    min_dim = min(w, h)
                    left = (w - min_dim) // 2
                    top = (h - min_dim) // 2
                    right = left + min_dim
                    bottom = top + min_dim
                    cropped = img.crop((left, top, right, bottom))
                    resized = cropped.resize((300, 300), Image.Resampling.LANCZOS)
                    resized.save(pic_path, "PNG")
                except Exception:
                    with open(pic_path, "wb") as f:
                        f.write(pic.getbuffer())

            db_exec(
                """
                INSERT INTO alumni (username, name, bio, linkedin, github, year, department, company, profile_pic)
                VALUES (:u,:n,:b,:li,:gh,:y,:d,:c,:p)
                ON DUPLICATE KEY UPDATE
                    name=VALUES(name),
                    bio=VALUES(bio),
                    linkedin=VALUES(linkedin),
                    github=VALUES(github),
                    year=VALUES(year),
                    department=VALUES(department),
                    company=VALUES(company),
                    profile_pic=VALUES(profile_pic)
                """,
                {
                    "u": st.session_state.username.strip(),
                    "n": name,
                    "b": bio,
                    "li": li,
                    "gh": gh,
                    "y": year,
                    "d": dept,
                    "c": company,
                    "p": pic_path,
                },
            )

            db_exec(
                "UPDATE users SET email=:e WHERE username=:u",
                {"e": email, "u": st.session_state.username.strip()},
            )

            st.success("Profile saved ✅")
            st.rerun()


# ---------------- ADMIN UI ----------------
def admin_dashboard():
    # Admin Custom CSS matching target screenshots
    st.markdown(
        """
        <style>
        /* Light Page Background */
        .stApp, body, [data-testid="stAppViewContainer"] {
            background-color: #f8fafc !important;
            color: #0f172a !important;
        }

        /* ── Streamlit Header & Sidebar Toggle Fix ── */
        header[data-testid="stHeader"],
        [data-testid="stHeader"],
        .stAppHeader {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            background: transparent !important;
            background-color: transparent !important;
            box-shadow: none !important;
            border: none !important;
            height: 60px !important;
            min-height: 60px !important;
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            z-index: 99999 !important;
            pointer-events: none !important;
        }

        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"],
        div[data-testid="stSidebarCollapsedControl"],
        button[aria-label="Expand sidebar"],
        button[aria-label="Open sidebar"] {
            display: inline-flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            pointer-events: auto !important;
            position: fixed !important;
            top: 12px !important;
            left: 12px !important;
            background: #1e1b4b !important;
            color: #ffffff !important;
            border: 1.5px solid #ffffff !important;
            border-radius: 8px !important;
            padding: 6px 10px !important;
            box-shadow: 0 4px 14px rgba(30, 27, 75, 0.5) !important;
            cursor: pointer !important;
            z-index: 9999999 !important;
        }

        [data-testid="stSidebarCollapsedControl"] button,
        [data-testid="collapsedControl"] button {
            background: transparent !important;
            border: none !important;
            color: #ffffff !important;
            pointer-events: auto !important;
        }

        /* High Contrast Button Styling */
        button, .stButton > button, div.stDownloadButton > button {
            font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
            font-size: 14px !important;
            font-weight: 700 !important;
        }

        /* Primary Blue/Purple Gradient Buttons */
        button[kind="primary"],
        button[kind="primaryFormSubmit"],
        div.btn-purple-approve button,
        div.btn-chat-purple button,
        div.stDownloadButton button {
            background: linear-gradient(135deg, #2563eb, #6366f1) !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35) !important;
            border-radius: 12px !important;
            padding: 10px 18px !important;
            width: 100% !important;
        }
        button[kind="primary"]:hover,
        button[kind="primaryFormSubmit"]:hover,
        div.btn-purple-approve button:hover,
        div.btn-chat-purple button:hover,
        div.stDownloadButton button:hover {
            background: linear-gradient(135deg, #1d4ed8, #4f46e5) !important;
            color: #ffffff !important;
        }

        /* Secondary / Outline Buttons */
        button[kind="secondary"],
        div.btn-outline-reject button,
        div.btn-view-profile button,
        div.btn-back-outline button {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
            font-weight: 700 !important;
            border-radius: 12px !important;
            padding: 10px 18px !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
            width: 100% !important;
            text-align: center !important;
        }
        button[kind="secondary"]:hover,
        div.btn-outline-reject button:hover,
        div.btn-view-profile button:hover,
        div.btn-back-outline button:hover {
            background-color: #f8fafc !important;
            color: #0f172a !important;
            border-color: #94a3b8 !important;
        }

        /* ── Accept Request Button override (key-based, highest specificity) ── */
        div.btn-accept-green button,
        div[class*="st-key-acc_"] button {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
            background-color: #10b981 !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: 700 !important;
            border-radius: 10px !important;
            box-shadow: 0 3px 10px rgba(16,185,129,0.3) !important;
        }
        div.btn-accept-green button *,
        div[class*="st-key-acc_"] button * {
            color: #ffffff !important;
            font-weight: 700 !important;
        }
        div.btn-accept-green button:hover,
        div[class*="st-key-acc_"] button:hover {
            background: linear-gradient(135deg,#059669,#047857) !important;
        }

        /* ── Decline Request Button override (key-based, highest specificity) ── */
        div.btn-decline-red button,
        div[class*="st-key-dec_"] button {
            background: #fef2f2 !important;
            background-color: #fef2f2 !important;
            color: #dc2626 !important;
            border: 1.5px solid #fca5a5 !important;
            font-weight: 700 !important;
            border-radius: 10px !important;
            box-shadow: 0 1px 3px rgba(220,38,38,0.08) !important;
        }
        div.btn-decline-red button *,
        div[class*="st-key-dec_"] button * {
            color: #dc2626 !important;
            font-weight: 700 !important;
        }
        div.btn-decline-red button:hover,
        div[class*="st-key-dec_"] button:hover {
            background: #fee2e2 !important;
            color: #b91c1c !important;
            border-color: #f87171 !important;
        }

        /* ── WhatsApp Seamless Chat Header & Blue Options Button ── */
        div[class*="st-key-wa_chat_header"] {
            background: #f0f2f5 !important;
            background-color: #f0f2f5 !important;
            border: 1px solid #e2e8f0 !important;
            border-bottom: 1px solid #d1d7db !important;
            border-radius: 14px 14px 0 0 !important;
            padding: 10px 16px !important;
            min-height: 60px !important;
            height: 60px !important;
            box-sizing: border-box !important;
            display: flex !important;
            align-items: center !important;
            margin-bottom: 0 !important;
        }
        div[class*="st-key-wa_chat_header"] > div {
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        div[class*="st-key-wa_chat_header"] div[data-testid="stHorizontalBlock"] {
            align-items: center !important;
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        div[class*="st-key-wa_chat_header"] div[data-testid="stColumn"] {
            display: flex !important;
            align-items: center !important;
            padding: 0 !important;
        }
        div[class*="st-key-wa_chat_header"] div[data-testid="stColumn"]:first-child {
            justify-content: flex-start !important;
        }
        div[class*="st-key-wa_chat_header"] div[data-testid="stColumn"]:last-child {
            justify-content: flex-end !important;
        }
        div[class*="st-key-wa_chat_header"] div[data-testid="stPopover"] {
            display: flex !important;
            align-items: center !important;
            justify-content: flex-end !important;
            margin: 0 !important;
            padding: 0 !important;
            width: auto !important;
        }
        /* Blue Box for Options Button (formerly black box) */
        div[class*="st-key-wa_chat_header"] div[data-testid="stPopover"] > button {
            background: #2563eb !important;
            background-color: #2563eb !important;
            border: none !important;
            color: #ffffff !important;
            font-size: 20px !important;
            font-weight: 800 !important;
            box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35) !important;
            padding: 0 !important;
            min-height: 36px !important;
            height: 36px !important;
            width: 36px !important;
            min-width: 36px !important;
            cursor: pointer !important;
            border-radius: 8px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin: 0 0 0 auto !important;
            transition: all 0.2s ease !important;
        }
        div[class*="st-key-wa_chat_header"] div[data-testid="stPopover"] > button:hover {
            background: #1d4ed8 !important;
            background-color: #1d4ed8 !important;
            color: #ffffff !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.5) !important;
            transform: translateY(-1px) !important;
        }
        div[class*="st-key-wa_chat_header"] div[data-testid="stPopover"] > button *,
        div[class*="st-key-wa_chat_header"] div[data-testid="stPopover"] > button span,
        div[class*="st-key-wa_chat_header"] div[data-testid="stPopover"] > button p {
            color: #ffffff !important;
            font-size: 20px !important;
            font-weight: 800 !important;
            line-height: 1 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        /* Hide default Streamlit dropdown arrow inside chat header popover button */
        div[class*="st-key-wa_chat_header"] div[data-testid="stPopover"] button svg,
        div[class*="st-key-wa_chat_header"] div[data-testid="stPopover"] button [data-testid="stIcon"],
        div[class*="st-key-wa_chat_header"] div[data-testid="stPopover"] button span:has(svg) {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            height: 0 !important;
        }
        /* Remove gap between chat header and messages canvas */
        div:has(> div[class*="st-key-wa_chat_header"]),
        div[data-testid="stElementContainer"]:has(div[class*="st-key-wa_chat_header"]) {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }
        div:has(> div[class*="st-key-wa_chat_header"]) + div,
        div[data-testid="stElementContainer"]:has(div[class*="st-key-wa_chat_header"]) + div[data-testid="stElementContainer"],
        div[data-testid="stElementContainer"]:has(.wa-chat-canvas) {
            margin-top: -1rem !important;
            padding-top: 0 !important;
        }
        /* Link Buttons (LinkedIn / GitHub) — Balanced Theme */
        a[data-testid="stLinkButton"] {
            background: linear-gradient(135deg, #2563eb, #4f46e5) !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: 700 !important;
            border-radius: 12px !important;
            padding: 10px 18px !important;
            box-shadow: 0 3px 10px rgba(37, 99, 235, 0.28) !important;
            width: 100% !important;
            text-align: center !important;
            transition: all 0.18s ease-in-out !important;
            opacity: 1 !important;
            visibility: visible !important;
        }
        a[data-testid="stLinkButton"]:hover,
        a[data-testid="stLinkButton"]:focus,
        a[data-testid="stLinkButton"]:active {
            background: linear-gradient(135deg, #1d4ed8, #4338ca) !important;
            color: #ffffff !important;
            box-shadow: 0 5px 16px rgba(37, 99, 235, 0.42) !important;
            text-decoration: none !important;
            transform: translateY(-1px) !important;
        }
        a[data-testid="stLinkButton"] * {
            color: #ffffff !important;
            opacity: 1 !important;
            visibility: visible !important;
        }

        /* Block Button (Amber / Warning) */
        div.btn-block-amber button {
            background: linear-gradient(135deg, #f59e0b, #d97706) !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: 700 !important;
            box-shadow: 0 3px 10px rgba(217, 119, 6, 0.3) !important;
            border-radius: 12px !important;
            padding: 10px 18px !important;
            width: 100% !important;
        }
        div.btn-block-amber button:hover {
            background: linear-gradient(135deg, #d97706, #b45309) !important;
            color: #ffffff !important;
        }

        /* Delete Button (Red / Danger) */
        div.btn-delete-red button {
            background: linear-gradient(135deg, #ef4444, #dc2626) !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: 700 !important;
            box-shadow: 0 3px 10px rgba(220, 38, 38, 0.3) !important;
            border-radius: 12px !important;
            padding: 10px 18px !important;
            width: 100% !important;
        }
        div.btn-delete-red button:hover {
            background: linear-gradient(135deg, #dc2626, #b91c1c) !important;
            color: #ffffff !important;
        }

        /* Top Header Styling */
        .admin-nav-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0 16px 0;
            border-bottom: 1px solid #e2e8f0;
            margin-bottom: 24px;
        }

        /* Cards */
        .admin-card-box {
            background: #ffffff !important;
            border-radius: 20px !important;
            padding: 24px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.02) !important;
            border: 1px solid #eef2f6 !important;
            margin-bottom: 20px !important;
        }

        /* KPI Metric Cards */
        .kpi-container {
            background: #ffffff !important;
            border-radius: 20px !important;
            padding: 20px 22px !important;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.03) !important;
            border: 1px solid #f1f5f9 !important;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }
        .kpi-title {
            font-size: 11px;
            font-weight: 700;
            color: #64748b;
            letter-spacing: 0.6px;
            text-transform: uppercase;
            margin-bottom: 6px;
        }
        .kpi-val {
            font-size: 30px;
            font-weight: 800;
            color: #0f172a;
            line-height: 1.1;
        }
        .kpi-badge-blue {
            background: #dbeafe;
            color: #2563eb;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 10px;
            margin-left: 6px;
        }
        .kpi-badge-red {
            background: #fef2f2;
            color: #ef4444;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 10px;
            margin-left: 6px;
        }

        /* Badges */
        .role-badge-alumni {
            background: #f3e8ff !important;
            color: #9333ea !important;
            font-size: 12px !important;
            font-weight: 700 !important;
            padding: 4px 12px !important;
            border-radius: 12px !important;
        }
        .role-badge-student {
            background: #dbeafe !important;
            color: #2563eb !important;
            font-size: 12px !important;
            font-weight: 700 !important;
            padding: 4px 12px !important;
            border-radius: 12px !important;
        }
        .status-badge-active {
            background: #f1f5f9 !important;
            color: #475569 !important;
            font-size: 12px !important;
            font-weight: 600 !important;
            padding: 4px 10px !important;
            border-radius: 12px !important;
        }

        /* ── Remove extra top space ── */
        .block-container {
            padding-top: 0rem !important;
            margin-top: 0rem !important;
        }

        /* ── Sidebar gradient styling ── */
        [data-testid="stSidebar"] {
            background: linear-gradient(160deg, #1e1b4b 0%, #312e81 55%, #4338ca 100%) !important;
            border-right: none !important;
        }
        [data-testid="stSidebar"] * {
            color: #e0e7ff !important;
        }
        [data-testid="stSidebar"] .stRadio label {
            color: #c7d2fe !important;
            font-weight: 600 !important;
        }
        [data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
            color: #c7d2fe !important;
        }
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
            color: #a5b4fc !important;
        }
        /* Highlighted selected nav item */
        [data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div {
            background: rgba(165,180,252,0.2) !important;
            border-radius: 8px !important;
        }

        /* ── Search bar styling ── */
        [data-testid="stTextInput"] input {
            background: #ffffff !important;
            color: #0f172a !important;
            border: 2px solid #c7d2fe !important;
            border-radius: 12px !important;
            font-size: 14px !important;
            padding: 10px 14px !important;
        }
        [data-testid="stTextInput"] input:focus {
            border-color: #6366f1 !important;
            box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
        }
        [data-testid="stTextInput"] input::placeholder {
            color: #94a3b8 !important;
        }

        /* ── Admin top header bar ── */
        .admin-nav-header {
            padding-top: 4px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar Navigation
    st.sidebar.markdown(
        """
        <div style="font-size: 22px; font-weight: 800; color: #ffffff; display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.5">
                <circle cx="12" cy="12" r="3"></circle>
                <circle cx="19" cy="5" r="2"></circle>
                <circle cx="5" cy="5" r="2"></circle>
                <circle cx="5" cy="19" r="2"></circle>
                <circle cx="19" cy="19" r="2"></circle>
            </svg>
            360 Connect
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav_options = ["Dashboard", "Alumni Directory", "User Management", "Export Data", "Logout"]
    selected_nav = st.sidebar.radio("Navigation", nav_options, label_visibility="collapsed")
    st.sidebar.caption(f"Signed in as: **{st.session_state.username}** (Admin)")

    if selected_nav == "Logout":
        logout()
        return

    # ---------------- 1. DASHBOARD OVERVIEW ----------------
    if "Dashboard" in selected_nav:
        st.markdown(
            """
            <div style="margin-bottom: 24px;">
                <h1 style="font-size: 30px; font-weight: 800; color: #0f172a; margin: 0 0 4px 0;">Dashboard Overview</h1>
                <div style="font-size: 14px; color: #64748b; font-weight: 500;">
                    Welcome back. Here is the latest data across your university network.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        total_students = db_fetchone("SELECT COUNT(*) FROM users WHERE role='student'")[0]
        total_alumni = db_fetchone("SELECT COUNT(*) FROM users WHERE role='alumni'")[0]
        verified_alumni = db_fetchone("SELECT COUNT(*) FROM users WHERE role='alumni' AND linkedin_verified=1")[0]
        pending_approvals = db_fetchone("SELECT COUNT(*) FROM users WHERE status != 'approved'")[0]

        # 4 Metric KPI Cards Grid
        k1, k2, k3, k4 = st.columns(4)

        with k1:
            st.markdown(
                f"""
                <div class="kpi-container">
                    <div>
                        <div class="kpi-title">TOTAL STUDENTS</div>
                        <div class="kpi-val">{total_students:,} <span class="kpi-badge-blue">+2.4%</span></div>
                    </div>
                    <div style="font-size: 32px; opacity: 0.8;"></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with k2:
            st.markdown(
                f"""
                <div class="kpi-container">
                    <div>
                        <div class="kpi-title">TOTAL ALUMNI</div>
                        <div class="kpi-val">{total_alumni:,} <span class="kpi-badge-blue">+1.1%</span></div>
                    </div>
                    <div style="font-size: 32px; opacity: 0.8;"></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with k3:
            pct = int((verified_alumni / max(1, total_alumni)) * 100)
            st.markdown(
                f"""
                <div class="kpi-container" style="border: 1px solid #e0e7ff;">
                    <div>
                        <div class="kpi-title">VERIFIED ALUMNI <span style="color:#6366f1;">✔</span></div>
                        <div class="kpi-val">{verified_alumni:,} <span style="font-size:12px; color:#64748b; font-weight:600;">{pct}% of total</span></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with k4:
            st.markdown(
                f"""
                <div class="kpi-container" style="border: 1px solid #fee2e2;">
                    <div>
                        <div class="kpi-title" style="color:#dc2626;">PENDING APPROVALS</div>
                        <div class="kpi-val" style="color:#dc2626;">{pending_approvals} <span class="kpi-badge-red">Requires Action</span></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        col_left, col_right = st.columns([1.1, 1])

        # User Distribution Chart Card (Dynamic DB-driven SVG Donut Chart)
        with col_left:
            total_users = total_alumni + total_students
            if total_users > 0:
                alumni_pct_val = round((total_alumni / total_users) * 100, 1)
                student_pct_val = round((total_students / total_users) * 100, 1)
                a_dash = int(round((total_alumni / total_users) * 100))
            else:
                alumni_pct_val = 50.0
                student_pct_val = 50.0
                a_dash = 50

            s_dash = 100 - a_dash
            a_offset = 25
            s_offset = (25 - a_dash) % 100

            chart_html = f"""<div class="admin-card-box"><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 16px;"><h3 style="font-size: 18px; font-weight: 700; color: #0f172a; margin: 0;">User Distribution</h3><span style="font-size: 18px; color: #94a3b8; cursor: pointer;">•••</span></div><div style="text-align: center; padding: 10px 0;"><svg width="180" height="180" viewBox="0 0 42 42" class="donut"><circle class="donut-hole" cx="21" cy="21" r="15.91549430918954" fill="#fff"></circle><circle class="donut-ring" cx="21" cy="21" r="15.91549430918954" fill="transparent" stroke="#e2e8f0" stroke-width="3"></circle><circle class="donut-segment" cx="21" cy="21" r="15.91549430918954" fill="transparent" stroke="#2563eb" stroke-width="3.8" stroke-dasharray="{a_dash} {100 - a_dash}" stroke-dashoffset="{a_offset}"></circle><circle class="donut-segment" cx="21" cy="21" r="15.91549430918954" fill="transparent" stroke="#6366f1" stroke-width="3.8" stroke-dasharray="{s_dash} {100 - s_dash}" stroke-dashoffset="{s_offset}"></circle><text x="50%" y="44%" dominant-baseline="middle" text-anchor="middle" font-size="6" font-weight="800" fill="#0f172a">100%</text><text x="50%" y="57%" dominant-baseline="middle" text-anchor="middle" font-size="2.8" font-weight="600" fill="#64748b">Total ({total_users})</text></svg></div><div style="display: flex; justify-content: space-around; font-size: 12px; font-weight: 600; color: #475569; margin-top: 14px;"><div><span style="color: #2563eb;">●</span> Alumni: {alumni_pct_val}% ({total_alumni})</div><div><span style="color: #6366f1;">●</span> Student: {student_pct_val}% ({total_students})</div></div></div>"""
            st.markdown(chart_html, unsafe_allow_html=True)


        # Recent Registrations Table Card
        with col_right:
            st.markdown(
                """
                <div class="admin-card-box">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 16px;">
                        <div>
                            <h3 style="font-size: 18px; font-weight: 700; color: #0f172a; margin: 0;">Recent Registrations</h3>
                            <div style="font-size: 12px; color: #64748b;">Users awaiting verification</div>
                        </div>
                        <a href="#" style="font-size: 13px; font-weight: 700; color: #2563eb; text-decoration: none;">View All →</a>
                    </div>
                """,
                unsafe_allow_html=True,
            )

            recent_users = db_fetchall(
                """
                SELECT username, email, role, status, created_at
                FROM users
                ORDER BY created_at DESC
                LIMIT 5
                """
            )

            for u_rec in recent_users:
                uname, uemail, urole, ustat, ucreated = u_rec
                role_class = "role-badge-alumni" if urole == "alumni" else "role-badge-student"
                initials = uname[:2].upper()

                st.markdown(
                    f"""
                    <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f1f5f9;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            {get_avatar_html(uname, size=38)}
                            <div>
                                <div style="font-weight: 700; color: #0f172a; font-size: 14px;">{uname}</div>
                                <div style="font-size: 12px; color: #64748b;">{uemail}</div>
                            </div>
                        </div>
                        <span class="{role_class}">{urole.capitalize()}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- 2. ALUMNI DIRECTORY ----------------
    elif "Directory" in selected_nav:
        st.markdown(
            """
            <div style="margin-bottom: 20px;">
                <h1 style="font-size: 28px; font-weight: 800; color: #0f172a; margin: 0 0 4px 0;">Alumni Directory</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )

        q = st.text_input("Search", placeholder="Search alumni by name, department, or company...", label_visibility="collapsed", key="dir_search_input").strip().lower()

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        rows = db_fetchall(
            """
            SELECT a.username, a.name, a.bio, a.department, a.company, a.linkedin, a.github, a.year,
                   u.email, u.status, u.linkedin_verified
            FROM alumni a
            LEFT JOIN users u ON u.username = a.username
            ORDER BY a.updated_at DESC
            LIMIT 500
            """
        )

        filtered = []
        for r in rows:
            u, name, bio, dept, comp, li, gh, yr, email, status, verified = r
            blob = f"{u} {name or ''} {bio or ''} {dept or ''} {comp or ''} {yr or ''}".lower()
            if q and q not in blob:
                continue
            filtered.append(r)

        if not filtered:
            st.info("No matching alumni profiles found.")
        else:
            for idx, r in enumerate(filtered):
                u, name, bio, dept, comp, li, gh, yr, email, status, verified = r
                disp_name = name or f"@{u}"

                # Pre-build optional HTML parts to avoid nested f-string issues
                formatted_yr = format_batch_year(yr)
                yr_html   = f"<div style='font-size:13px;font-weight:700;color:#2563eb;margin-top:3px;'>{formatted_yr}</div>" if formatted_yr else ""
                dept_html = f"<div style='font-size:12px;color:#475569;margin-top:2px;'>{dept}</div>" if dept else ""
                comp_html = f"<div style='font-size:12px;color:#64748b;margin-top:2px;'>{comp}</div>" if comp else ""

                st.markdown(
                    f"""
                    <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:4px solid #6366f1;
                                border-radius:12px; padding:14px 18px; margin-bottom:8px;
                                display:flex; align-items:center; gap:14px;">
                        <div style="width:52px;height:52px;border-radius:50%;
                                    background:linear-gradient(135deg,#6366f1,#2563eb);
                                    color:#fff;font-size:19px;font-weight:800;
                                    display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                            {disp_name[:2].upper()}
                        </div>
                        <div style="flex:1;min-width:0;">
                            <div style="font-size:16px;font-weight:800;color:#0f172a;">{disp_name}</div>
                            {yr_html}{dept_html}{comp_html}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if li or gh:
                    btn_cols = st.columns([1.4, 1.4, 3])
                    with btn_cols[0]:
                        if li:
                            st.link_button("Open LinkedIn", normalize_url(li), use_container_width=True)
                    with btn_cols[1]:
                        if gh:
                            st.link_button("Open GitHub", normalize_url(gh), use_container_width=True)

                st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)



    # ---------------- 3. USER MANAGEMENT ----------------
    elif "Management" in selected_nav:
        st.markdown(
            """
            <div style="margin-bottom: 20px;">
                <h1 style="font-size: 28px; font-weight: 800; color: #0f172a; margin: 0 0 4px 0;">User Management</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )

        q_mgmt = st.text_input("Search", placeholder="Search by name or email...", label_visibility="collapsed", key="mgmt_search_val").strip().lower()

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        users_list = db_fetchall(
            """
            SELECT username, email, role, status, linkedin_verified, created_at
            FROM users
            ORDER BY created_at DESC
            """
        )

        if not users_list:
            st.info("No users found in database.")
        else:
            for urow in users_list:
                uname, uemail, urole, ustat, uver, ucreated = urow

                if q_mgmt and q_mgmt not in uname.lower() and q_mgmt not in uemail.lower():
                    continue

                role_badge = "role-badge-alumni" if urole == "alumni" else "role-badge-student"

                with st.container(border=True):
                    cu1, cu2 = st.columns([0.8, 3])
                    with cu1:
                        st.markdown(get_avatar_html(uname, size=54), unsafe_allow_html=True)
                    with cu2:
                        st.markdown(
                            f"""
                            <div style="font-size: 17px; font-weight: 700; color: #0f172a;">{uname}</div>
                            <div style="font-size: 13px; color: #64748b; margin-bottom: 8px;">{uemail}</div>
                            <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px;">
                                <span class="{role_badge}">{urole.capitalize()}</span>
                                <span class="status-badge-active">{ustat.capitalize()}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Action Buttons
                        if ustat != "approved":
                            ca_a, ca_r = st.columns(2)
                            with ca_a:
                                st.markdown('<div class="btn-purple-approve">', unsafe_allow_html=True)
                                if st.button("Approve", key=f"appr_{uname}", use_container_width=True):
                                    db_exec("UPDATE users SET status='approved' WHERE username=:u", {"u": uname})
                                    st.success(f"{uname} approved")
                                    st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)
                            with ca_r:
                                st.markdown('<div class="btn-outline-reject">', unsafe_allow_html=True)
                                if st.button("Reject", key=f"rej_{uname}", use_container_width=True):
                                    db_exec("UPDATE users SET status='blocked' WHERE username=:u", {"u": uname})
                                    st.warning(f"{uname} rejected")
                                    st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)
                        else:
                            cb_b, cb_d = st.columns(2)
                            with cb_b:
                                st.markdown('<div class="btn-block-amber">', unsafe_allow_html=True)
                                if st.button("Block", key=f"blk_{uname}", use_container_width=True):
                                    db_exec("UPDATE users SET status='blocked' WHERE username=:u", {"u": uname})
                                    st.warning(f"{uname} blocked")
                                    st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)
                            with cb_d:
                                st.markdown('<div class="btn-delete-red">', unsafe_allow_html=True)
                                if st.button("Delete", key=f"del_{uname}", use_container_width=True):
                                    db_exec("DELETE FROM alumni WHERE username=:u", {"u": uname})
                                    db_exec("DELETE FROM users WHERE username=:u", {"u": uname})
                                    st.error(f"{uname} deleted")
                                    st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)


    # ---------------- 4. EXPORT DATA ----------------
    elif "Export" in selected_nav:
        st.markdown(
            """
            <div style="margin-bottom: 20px;">
                <h1 style="font-size: 28px; font-weight: 800; color: #0f172a; margin: 0 0 4px 0;">Export Alumni Data</h1>
                <div style="font-size: 14px; color: #64748b;">Export verified university alumni records, department details, and contact info to CSV format.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        rows = db_fetchall(
            """
            SELECT u.username, u.email,
                   a.name, a.department, a.company, a.year, a.linkedin, a.github
            FROM users u
            LEFT JOIN alumni a ON a.username = u.username
            WHERE u.role='alumni'
            """
        )

        formatted_rows = []
        for r in rows:
            uname, uemail, aname, adept, acomp, ayr, ali, agh = r
            batch_yr = format_batch_year(ayr) if ayr else ""
            formatted_rows.append([
                uname,
                uemail,
                aname or "",
                adept or "",
                acomp or "",
                batch_yr,
                ali or "",
                agh or "",
            ])

        df = df_with_sno(
            formatted_rows,
            [
                "Username",
                "Email",
                "Name",
                "Department",
                "Company",
                "Batch (Start - End Year)",
                "LinkedIn URL",
                "GitHub URL",
            ],
        )

        csv = df.to_csv(index=False).encode("utf-8")

        st.markdown(
            f"""
            <div style="margin-bottom: 14px;">
                <div style="font-size: 16px; font-weight: 800; color: #1e293b; margin-bottom: 2px;">Alumni Records Ready</div>
                <div style="font-size: 13px; color: #64748b;">{len(formatted_rows)} total alumni records available</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("""
        <style>
        div.btn-export-csv div[data-testid="stDownloadButton"] > button,
        div.btn-export-csv button {
            background: linear-gradient(135deg, #4361ee 0%, #3a86ff 100%) !important;
            background-color: #4361ee !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 12px !important;
            font-size: 15px !important;
            font-weight: 700 !important;
            padding: 12px 0 !important;
            width: 100% !important;
            cursor: pointer !important;
            box-shadow: 0 4px 14px rgba(67, 97, 238, 0.35) !important;
            margin-bottom: 18px !important;
            transition: all 0.18s ease-in-out !important;
        }
        div.btn-export-csv div[data-testid="stDownloadButton"] > button *,
        div.btn-export-csv button * {
            color: #ffffff !important;
            font-weight: 700 !important;
            font-size: 15px !important;
        }
        div.btn-export-csv div[data-testid="stDownloadButton"] > button:hover,
        div.btn-export-csv button:hover {
            background: linear-gradient(135deg, #3730a3 0%, #4361ee 100%) !important;
            box-shadow: 0 6px 20px rgba(67, 97, 238, 0.55) !important;
            transform: translateY(-1px) !important;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="btn-export-csv">', unsafe_allow_html=True)
        st.download_button("Download CSV", data=csv, file_name="alumni_export.csv", mime="text/csv", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        show_df(df)



# ---------------- MAIN ROUTER ----------------
if not st.session_state.logged_in:
    login_signup_page()
else:
    if st.session_state.role == "admin":
        admin_dashboard()
    else:
        alumni_dashboard()

