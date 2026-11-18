import re
import pandas as pd
import streamlit as st

def inject_css():
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width:100% !important; padding-left:1.5rem !important; padding-right:1.5rem !important; }
        header[data-testid="stHeader"] {height: 0rem;}
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

def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "https://" + url
    return url

def df_with_sno(rows, columns):
    df = pd.DataFrame(rows, columns=columns)
    df = df.reset_index(drop=True)
    df.insert(0, "No.", range(1, len(df) + 1))
    return df

def show_df(df: pd.DataFrame):
    # Streamlit versions differ; keep safe fallback
    try:
        st.dataframe(df, use_container_width=True, hide_index=True)
    except TypeError:
        st.markdown(df.to_html(index=False), unsafe_allow_html=True)
