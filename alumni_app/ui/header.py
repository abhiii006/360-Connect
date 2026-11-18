import streamlit as st
from core.utils import inject_css

def render_header_compact():
    inject_css()
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
