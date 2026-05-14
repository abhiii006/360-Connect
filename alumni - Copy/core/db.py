import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

def _sec(name, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default

MYSQL_USER = _sec("MYSQL_USER", "alumni_user")
MYSQL_PASS = _sec("MYSQL_PASS", "StrongPass@123")
MYSQL_HOST = _sec("MYSQL_HOST", "127.0.0.1")
MYSQL_DB   = _sec("MYSQL_DB", "alumni_db")
MYSQL_PORT = int(_sec("MYSQL_PORT", 3306))

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
