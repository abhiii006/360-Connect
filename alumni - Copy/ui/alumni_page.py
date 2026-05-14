import os
import streamlit as st

from core.db import db_exec, db_fetchall, db_fetchone
from core.utils import normalize_url
from core.linkedin_oauth import linkedin_config_ok, linkedin_auth_url, handle_linkedin_callback
from ui.common import logout

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

def alumni_dashboard():
    handle_linkedin_callback()

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

            current_pic = db_fetchone(
                "SELECT profile_pic FROM alumni WHERE username=:u",
                {"u": st.session_state.username},
            )
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
