import streamlit as st

from core.db import db_exec, db_fetchall, db_fetchone
from core.utils import df_with_sno, show_df, normalize_url
from ui.common import logout

def admin_dashboard():
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
        import pandas as pd

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
