from core.db import db_exec, db_fetchone
from core.security import hash_password

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
