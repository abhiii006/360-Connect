import os
import re
import bcrypt
import requests
import pandas as pd
import streamlit as st

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Alumni Management System",
    page_icon="🎓",
    layout="wide",
)

# ---------------- BASIC UI CSS ----------------
st.markdown(
    """
    <style>
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
    .card {
        border: 1px solid rgba(255,255,255,0.12);
        padding: 14px 16px;
        border-radius: 14px;
        background: rgba(255,255,255,0.03);
        margin-bottom: 12px;
    }
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        border: 1px solid rgba(255,255,255,0.15);
        background: rgba(0,255,120,0.08);
        margin-left: 8px;
    }
    .muted { opacity: 0.75; font-size: 13px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
<style>
/* Make Streamlit use full width */
.block-container {
    max-width: 100% !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
}

/* Remove extra top gap in some themes */
header[data-testid="stHeader"] {height: 0rem;}
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
                    🌐 360 Connect
                </div>
                <div style="font-size:11px;opacity:0.75;margin-top:2px;">
                    🎓 Alumni Management System
                </div>
            </div>
            <div style="font-size:11px;opacity:0.60;white-space:nowrap;">
                MySQL · LinkedIn Verified
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


# ✅ Add numbering column starting from 1
def df_with_sno(rows, columns):
    df = pd.DataFrame(rows, columns=columns)
    df = df.reset_index(drop=True)               # remove any df index
    df.insert(0, "No.", range(1, len(df) + 1))   # 1,2,3...
    return df


# ✅ Show df without any index in ALL streamlit versions
def show_df(df: pd.DataFrame):
    try:
        st.dataframe(df, use_container_width=True, hide_index=True)
    except TypeError:
        st.markdown(df.to_html(index=False), unsafe_allow_html=True)


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


def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = ""
    st.session_state.linkedin_profile = None
    st.session_state.login_mode = None
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
        "name": (prof[0] if prof else "") or "",
        "bio": (prof[1] if prof else "") or "",
        "linkedin": (prof[2] if prof else "") or "",
        "github": (prof[3] if prof else "") or "",
        "year": (prof[4] if prof else "") or "",
        "department": (prof[5] if prof else "") or "",
        "company": (prof[6] if prof else "") or "",
        "profile_pic": (prof[7] if prof else "") or "",
        "email": (user_meta[0] if user_meta else "") or "",
        "verified": (user_meta and user_meta[1] == 1),
    }


# ---------------- AUTH UI ----------------
def login_signup_page():
    # NOTE: header already rendered by router
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

        # Signup always visible here
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

        return  # stop here in step 1

    # -------- BACK BUTTON --------
    if st.button("⬅️ Back"):
        st.session_state.login_mode = None
        st.rerun()

    st.divider()

    # -------- STEP 2: LOGIN FORM --------
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


# ---------------- ALUMNI UI ----------------
def alumni_dashboard():
    render_header_compact()

    st.sidebar.title("🎓 Alumni")
    menu = st.sidebar.radio("Navigation", ["Dashboard", "My Profile", "Directory", "Logout"])
    st.sidebar.caption(f"Signed in as: **{st.session_state.username}**")

    if menu == "Dashboard":
        st.title("Dashboard")
        total = db_fetchone("SELECT COUNT(*) FROM alumni")[0]
        st.metric("Total Alumni Profiles", total)

    elif menu == "My Profile":
        p = load_profile_from_db(st.session_state.username)
        st.title("My Profile")

        st.subheader("LinkedIn Sync")
        cols = st.columns([1, 2])
        with cols[0]:
            if linkedin_config_ok():
                st.link_button("🔗 Connect LinkedIn", linkedin_auth_url(), use_container_width=True)
            else:
                st.info("LinkedIn not configured in secrets.toml")

        with cols[1]:
            if st.session_state.linkedin_profile:
                info = st.session_state.linkedin_profile
                st.success("LinkedIn Connected ✅")
                st.write({"name": info.get("name"), "email": info.get("email"), "id": info.get("sub")})
                if st.button("✅ Mark as LinkedIn Verified & Save ID"):
                    db_exec(
                        """
                        UPDATE users
                        SET linkedin_id=:lid, linkedin_email=:lem, linkedin_verified=1
                        WHERE username=:u
                        """,
                        {"lid": info.get("sub"), "lem": info.get("email"), "u": st.session_state.username},
                    )
                    st.success("LinkedIn verified saved ✅")
                    st.rerun()
            else:
                st.caption("Connect LinkedIn to verify identity.")

        st.subheader("Profile Details")
        if p["verified"]:
            st.markdown("**Status:** LinkedIn Verified <span class='badge'>✅ Verified</span>", unsafe_allow_html=True)
        else:
            st.markdown("**Status:** Not verified")

        li_email = ""
        if st.session_state.linkedin_profile:
            li_email = st.session_state.linkedin_profile.get("email") or ""

        with st.form("profile_form", clear_on_submit=False):
            name = st.text_input("Full Name", value=p["name"])
            email = st.text_input("Email (from signup)", value=(p["email"] or li_email))
            bio = st.text_area("Bio", value=p["bio"])

            linkedin_url = st.text_input("LinkedIn Profile URL", value=p["linkedin"])
            github_url = st.text_input("GitHub URL", value=p["github"])
            year = st.text_input("Graduation Year", value=p["year"])
            dept = st.text_input("Department", value=p["department"])
            company = st.text_input("Company / Role", value=p["company"])

            pic = st.file_uploader("Profile picture (optional)", type=["png", "jpg", "jpeg"])
            submitted = st.form_submit_button("💾 Save Profile")

        if submitted:
            li = normalize_url(linkedin_url)
            gh = normalize_url(github_url)

            current_pic = db_fetchone("SELECT profile_pic FROM alumni WHERE username=:u", {"u": st.session_state.username})
            pic_path = (current_pic[0] if current_pic else "") or ""

            if pic is not None:
                os.makedirs("profile_pics", exist_ok=True)
                pic_path = os.path.join("profile_pics", f"{st.session_state.username}_{pic.name}")
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

    elif menu == "Directory":
        st.title("Alumni Directory")
        q = st.text_input("Search by name / dept / company").strip().lower()

        rows = db_fetchall(
            """
            SELECT a.username, a.name, a.department, a.company, a.linkedin, a.github, u.linkedin_verified
            FROM alumni a
            LEFT JOIN users u ON u.username = a.username
            ORDER BY a.updated_at DESC
            LIMIT 200
            """
        )

        if not rows:
            st.info("No alumni profiles found yet.")
            return

        for r in rows:
            u, name, dept, comp, li, gh, v = r
            blob = f"{u} {name or ''} {dept or ''} {comp or ''}".lower()
            if q and q not in blob:
                continue

            badge = "<span class='badge'>LinkedIn Verified ✅</span>" if v == 1 else ""
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f"**{name or u}** <span class='muted'>@{u}</span> {badge}", unsafe_allow_html=True)
            st.markdown(f"<div class='muted'>{dept or '—'} • {comp or '—'}</div>", unsafe_allow_html=True)

            cols = st.columns(2)
            with cols[0]:
                if li:
                    st.link_button("Open LinkedIn", normalize_url(li), use_container_width=True)
            with cols[1]:
                if gh:
                    st.link_button("Open GitHub", normalize_url(gh), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "Logout":
        logout()


# ---------------- ADMIN UI ----------------
def admin_dashboard():
    render_header_compact()

    st.sidebar.title("👨‍💼 Admin")
    menu = st.sidebar.radio("Navigation", ["Dashboard", "Users", "Profiles", "Directory", "Export", "Logout"])
    st.sidebar.caption(f"Signed in as: **{st.session_state.username}**")

    if menu == "Dashboard":
        st.title("Admin Dashboard")
        total_users = db_fetchone("SELECT COUNT(*) FROM users")[0]
        total_alumni = db_fetchone("SELECT COUNT(*) FROM users WHERE role='alumni'")[0]
        verified = db_fetchone("SELECT COUNT(*) FROM users WHERE role='alumni' AND linkedin_verified=1")[0]
        profs = db_fetchone("SELECT COUNT(*) FROM alumni")[0]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Users", total_users)
        c2.metric("Total Alumni", total_alumni)
        c3.metric("LinkedIn Verified", verified)
        c4.metric("Profiles Created", profs)

    elif menu == "Users":
        st.title("Manage Users")

        rows = db_fetchall(
            """
            SELECT username, email, role, status, linkedin_verified, created_at
            FROM users
            ORDER BY created_at DESC
            """
        )

        df = df_with_sno(rows, ["Username", "Email", "Role", "Status", "LinkedIn Verified", "Created At"])
        show_df(df)

        st.divider()
        st.subheader("User Actions")

        usernames = [r[0] for r in rows if r[0] != "admin"]
        if not usernames:
            st.info("No users to manage.")
            return

        selected_user = st.selectbox("Select user", usernames)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("✅ Approve", use_container_width=True):
                db_exec("UPDATE users SET status='approved' WHERE username=:u", {"u": selected_user})
                st.success(f"{selected_user} approved")
                st.rerun()
        with col2:
            if st.button("⛔ Block", use_container_width=True):
                db_exec("UPDATE users SET status='blocked' WHERE username=:u", {"u": selected_user})
                st.warning(f"{selected_user} blocked")
                st.rerun()
        with col3:
            if st.button("🔁 Toggle Verified", use_container_width=True):
                db_exec(
                    """
                    UPDATE users
                    SET linkedin_verified = CASE WHEN linkedin_verified=1 THEN 0 ELSE 1 END
                    WHERE username=:u
                    """,
                    {"u": selected_user},
                )
                st.success("Verification updated")
                st.rerun()
        with col4:
            if st.button("🗑 Delete", use_container_width=True):
                db_exec("DELETE FROM alumni WHERE username=:u", {"u": selected_user})
                db_exec("DELETE FROM users WHERE username=:u", {"u": selected_user})
                st.error(f"{selected_user} deleted")
                st.rerun()

    elif menu == "Profiles":
        st.title("Alumni Profiles")

        rows = db_fetchall(
            """
            SELECT username, name, department, company, linkedin, github, updated_at
            FROM alumni
            ORDER BY updated_at DESC
            """
        )

        df = df_with_sno(rows, ["Username", "Name", "Department", "Company", "LinkedIn", "GitHub", "Updated At"])
        show_df(df)

    elif menu == "Directory":
        st.title("Alumni Directory (Admin)")
        q = st.text_input("Search by name / dept / company / username").strip().lower()

        rows = db_fetchall(
            """
            SELECT a.username, a.name, a.department, a.company, a.linkedin, a.github,
                   u.email, u.status, u.linkedin_verified
            FROM alumni a
            LEFT JOIN users u ON u.username = a.username
            ORDER BY a.updated_at DESC
            LIMIT 500
            """
        )

        if not rows:
            st.info("No alumni profiles found yet.")
            return

        filtered = []
        for r in rows:
            u, name, dept, comp, li, gh, email, status, verified = r
            blob = f"{u} {name or ''} {dept or ''} {comp or ''}".lower()
            if q and q not in blob:
                continue
            filtered.append(r)

        if not filtered:
            st.warning("No matches found.")
            return

        for i, r in enumerate(filtered, start=1):
            u, name, dept, comp, li, gh, email, status, verified = r

            badge = "<span class='badge'>LinkedIn Verified ✅</span>" if verified == 1 else ""
            st.markdown('<div class="card">', unsafe_allow_html=True)

            st.markdown(f"**{i}. {name or u}** <span class='muted'>@{u}</span> {badge}", unsafe_allow_html=True)
            st.markdown(
                f"<div class='muted'>{dept or '—'} • {comp or '—'} • {email or '—'} • {status or '—'}</div>",
                unsafe_allow_html=True,
            )

            c1, c2, c3 = st.columns([1, 1, 1])

            with c1:
                if li:
                    st.link_button("Open LinkedIn", normalize_url(li), use_container_width=True)
                else:
                    st.button("No LinkedIn", use_container_width=True, disabled=True)

            with c2:
                if gh:
                    st.link_button("Open GitHub", normalize_url(gh), use_container_width=True)
                else:
                    st.button("No GitHub", use_container_width=True, disabled=True)

            with c3:
                if st.button("Toggle Verified", key=f"admin_toggle_verified_{u}", use_container_width=True):
                    db_exec(
                        """
                        UPDATE users
                        SET linkedin_verified = CASE WHEN linkedin_verified=1 THEN 0 ELSE 1 END
                        WHERE username=:u
                        """,
                        {"u": u},
                    )
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "Export":
        st.title("Export Alumni Data")

        rows = db_fetchall(
            """
            SELECT u.username, u.email, u.linkedin_verified,
                   a.name, a.department, a.company, a.linkedin, a.github, a.year
            FROM users u
            LEFT JOIN alumni a ON a.username = u.username
            WHERE u.role='alumni'
            """
        )

        df = df_with_sno(
            rows,
            [
                "Username",
                "Email",
                "LinkedIn Verified",
                "Name",
                "Department",
                "Company",
                "LinkedIn URL",
                "GitHub URL",
                "Year",
            ],
        )

        show_df(df)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", data=csv, file_name="alumni_export.csv", mime="text/csv")

    elif menu == "Logout":
        logout()


# ---------------- MAIN ROUTER ----------------
if not st.session_state.logged_in:
    render_header_compact()  # ✅ compact on login
    login_signup_page()
else:
    # ✅ DO NOT use render_header_full anymore (removed)
    if st.session_state.role == "admin":
        admin_dashboard()
    else:
        alumni_dashboard()
