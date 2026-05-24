"""
database.py — SQLite persistence layer for Value Analyst App.
Manages portfolio tickers and cumulative analysis history.
"""

import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'value_analyst.db')


def _ensure_dir():
    """Ensure the data directory exists."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_connection():
    """Get a SQLite connection with row factory."""
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database tables with user support and perform migrations if necessary."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Ensure users table exists
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [col['name'] for col in cursor.fetchall()]
    
    if not user_columns:
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
    elif 'role' not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")

    # Seed default admin user (password: 'WarrenBuffett#2026') if users table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        import bcrypt
        pw_hash = bcrypt.hashpw(b"WarrenBuffett#2026", bcrypt.gensalt(rounds=10)).decode('utf-8')
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("admin", pw_hash, "admin"))

    # 2. Check and migrate portfolio table
    cursor.execute("PRAGMA table_info(portfolio)")
    portfolio_columns = [col['name'] for col in cursor.fetchall()]
    if not portfolio_columns:
        # Fresh table creation
        cursor.execute("""
            CREATE TABLE portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                added_at TEXT NOT NULL DEFAULT (datetime('now')),
                notes TEXT DEFAULT '',
                UNIQUE(user_id, ticker),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
    elif 'user_id' not in portfolio_columns:
        # Migration is needed
        cursor.execute("""
            CREATE TABLE portfolio_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                added_at TEXT NOT NULL DEFAULT (datetime('now')),
                notes TEXT DEFAULT '',
                UNIQUE(user_id, ticker),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        # Copy data assigning it to default user_id = 1
        cursor.execute("""
            INSERT OR IGNORE INTO portfolio_new (id, user_id, ticker, added_at, notes)
            SELECT id, 1, ticker, added_at, notes FROM portfolio
        """)
        cursor.execute("DROP TABLE portfolio")
        cursor.execute("ALTER TABLE portfolio_new RENAME TO portfolio")

    # 3. Check and migrate analysis_history table
    cursor.execute("PRAGMA table_info(analysis_history)")
    history_columns = [col['name'] for col in cursor.fetchall()]
    if not history_columns:
        # Fresh table creation
        cursor.execute("""
            CREATE TABLE analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                fecha_consulta TEXT NOT NULL,
                ticker TEXT NOT NULL,
                empresa TEXT DEFAULT '',
                sector TEXT DEFAULT '',
                precio_mercado REAL,
                eps_hist REAL,
                eps_actual REAL,
                eps_tendencia TEXT DEFAULT '',
                fcf_hist REAL,
                fcf_actual REAL,
                fcf_tendencia TEXT DEFAULT '',
                roic_hist REAL,
                roic_actual REAL,
                roic_tendencia TEXT DEFAULT '',
                per_actual REAL,
                ev_fcf_actual REAL,
                valor_intrinseco_graham REAL,
                valor_intrinseco_dcf REAL,
                margen_seguridad REAL,
                ms_absoluto REAL,
                ms_relativo REAL,
                estado_semaforo TEXT DEFAULT '',
                alerta_compra INTEGER DEFAULT 0,
                calidad TEXT DEFAULT '',
                non_gaap_flag TEXT DEFAULT '',
                raw_data TEXT DEFAULT '',
                UNIQUE(user_id, fecha_consulta, ticker),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
    elif 'user_id' not in history_columns:
        # Migration is needed
        cursor.execute("""
            CREATE TABLE analysis_history_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                fecha_consulta TEXT NOT NULL,
                ticker TEXT NOT NULL,
                empresa TEXT DEFAULT '',
                sector TEXT DEFAULT '',
                precio_mercado REAL,
                eps_hist REAL,
                eps_actual REAL,
                eps_tendencia TEXT DEFAULT '',
                fcf_hist REAL,
                fcf_actual REAL,
                fcf_tendencia TEXT DEFAULT '',
                roic_hist REAL,
                roic_actual REAL,
                roic_tendencia TEXT DEFAULT '',
                per_actual REAL,
                ev_fcf_actual REAL,
                valor_intrinseco_graham REAL,
                valor_intrinseco_dcf REAL,
                margen_seguridad REAL,
                ms_absoluto REAL,
                ms_relativo REAL,
                estado_semaforo TEXT DEFAULT '',
                alerta_compra INTEGER DEFAULT 0,
                calidad TEXT DEFAULT '',
                non_gaap_flag TEXT DEFAULT '',
                raw_data TEXT DEFAULT '',
                UNIQUE(user_id, fecha_consulta, ticker),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            INSERT OR IGNORE INTO analysis_history_new (
                id, user_id, fecha_consulta, ticker, empresa, sector, precio_mercado,
                eps_hist, eps_actual, eps_tendencia, fcf_hist, fcf_actual, fcf_tendencia,
                roic_hist, roic_actual, roic_tendencia, per_actual, ev_fcf_actual,
                valor_intrinseco_graham, valor_intrinseco_dcf, margen_seguridad,
                ms_absoluto, ms_relativo, estado_semaforo, alerta_compra, calidad,
                non_gaap_flag, raw_data
            )
            SELECT
                id, 1, fecha_consulta, ticker, empresa, sector, precio_mercado,
                eps_hist, eps_actual, eps_tendencia, fcf_hist, fcf_actual, fcf_tendencia,
                roic_hist, roic_actual, roic_tendencia, per_actual, ev_fcf_actual,
                valor_intrinseco_graham, valor_intrinseco_dcf, margen_seguridad,
                ms_absoluto, ms_relativo, estado_semaforo, alerta_compra, calidad,
                non_gaap_flag, raw_data
            FROM analysis_history
        """)
        cursor.execute("DROP TABLE analysis_history")
        cursor.execute("ALTER TABLE analysis_history_new RENAME TO analysis_history")

    conn.commit()
    conn.close()


# ─── User Management CRUD ──────────────────────────────────────────

def create_user(username: str, password_hash: str) -> int:
    """Create a new user and return their user ID."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username.lower().strip(), password_hash)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_user_by_username(username: str):
    """Retrieve user dictionary by username."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, username, password_hash, role, created_at FROM users WHERE username = ?",
        (username.lower().strip(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int):
    """Retrieve user dictionary by ID."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, username, password_hash, role, created_at FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_users_stats():
    """Retrieve all users with their portfolio count for the admin panel."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT u.id, u.username, u.role, u.created_at, COUNT(p.id) as portfolio_count 
        FROM users u 
        LEFT JOIN portfolio p ON u.id = p.user_id 
        GROUP BY u.id
        ORDER BY u.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_user_and_data(user_id: int) -> bool:
    """Delete a user. Portfolio and history are deleted automatically via ON DELETE CASCADE."""
    conn = get_connection()
    cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


# ─── Portfolio CRUD (User-isolated) ────────────────────────────────

def get_portfolio(user_id: int):
    """Get all tickers in a user's portfolio."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT ticker, added_at, notes FROM portfolio WHERE user_id = ? ORDER BY added_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_to_portfolio(user_id: int, ticker: str, notes: str = '') -> bool:
    """Add a ticker to a user's portfolio. Returns True if added, False if already exists."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO portfolio (user_id, ticker, notes) VALUES (?, ?, ?)",
            (user_id, ticker.upper().strip(), notes)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def remove_from_portfolio(user_id: int, ticker: str) -> bool:
    """Remove a ticker from a user's portfolio."""
    conn = get_connection()
    cursor = conn.execute(
        "DELETE FROM portfolio WHERE user_id = ? AND ticker = ?",
        (user_id, ticker.upper().strip())
    )
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


# ─── Analysis History (User-isolated) ──────────────────────────────

def save_analysis(user_id: int, data: dict):
    """
    Save an analysis record to history for a user (cumulative, never overwrite).
    """
    conn = get_connection()
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    conn.execute("""
        INSERT OR REPLACE INTO analysis_history (
            user_id, fecha_consulta, ticker, empresa, sector, precio_mercado,
            eps_hist, eps_actual, eps_tendencia,
            fcf_hist, fcf_actual, fcf_tendencia,
            roic_hist, roic_actual, roic_tendencia,
            per_actual, ev_fcf_actual,
            valor_intrinseco_graham, valor_intrinseco_dcf,
            margen_seguridad, ms_absoluto, ms_relativo, estado_semaforo, alerta_compra,
            calidad, non_gaap_flag, raw_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        timestamp,
        data.get('ticker', ''),
        data.get('empresa', ''),
        data.get('sector', ''),
        data.get('precio_mercado'),
        data.get('eps_hist'),
        data.get('eps_actual'),
        data.get('eps_tendencia', ''),
        data.get('fcf_hist'),
        data.get('fcf_actual'),
        data.get('fcf_tendencia', ''),
        data.get('roic_hist'),
        data.get('roic_actual'),
        data.get('roic_tendencia', ''),
        data.get('per_actual'),
        data.get('ev_fcf_actual'),
        data.get('valor_intrinseco_graham'),
        data.get('valor_intrinseco_dcf'),
        data.get('margen_seguridad'),
        data.get('ms_absoluto'),
        data.get('ms_relativo'),
        data.get('estado_semaforo', ''),
        data.get('alerta_compra', 0),
        data.get('calidad', ''),
        data.get('non_gaap_flag', ''),
        json.dumps(data.get('raw_data', {}))
    ))
    conn.commit()
    conn.close()


def get_history(user_id: int, ticker: str = None, limit: int = 500):
    """Get analysis history for a specific user. Optionally filter by ticker."""
    conn = get_connection()
    if ticker:
        rows = conn.execute(
            "SELECT * FROM analysis_history WHERE user_id = ? AND ticker = ? ORDER BY fecha_consulta DESC LIMIT ?",
            (user_id, ticker.upper().strip(), limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM analysis_history WHERE user_id = ? ORDER BY fecha_consulta DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_latest_analysis(user_id: int, ticker: str):
    """Get the most recent analysis for a ticker and a specific user."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM analysis_history WHERE user_id = ? AND ticker = ? ORDER BY fecha_consulta DESC LIMIT 1",
        (user_id, ticker.upper().strip())
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# Initialize on import
init_db()

