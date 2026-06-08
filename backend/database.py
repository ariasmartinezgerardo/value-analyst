"""
database.py — SQLAlchemy persistence layer for Value Analyst App.
Supports SQLite locally and PostgreSQL in production.
"""

import os
import json
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint, select, insert, delete, update, func

# ─── Setup Engine ────────────────────────────────────────────────
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'value_analyst.db')
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}")

metadata = MetaData()

users_table = Table(
    'users', metadata,
    Column('id', Integer, primary_key=True),
    Column('username', String(255), unique=True, nullable=False),
    Column('password_hash', String(255), nullable=False),
    Column('role', String(50), nullable=False, server_default='user'),
    Column('created_at', DateTime, default=datetime.utcnow)
)

portfolio_table = Table(
    'portfolio', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
    Column('ticker', String(50), nullable=False),
    Column('added_at', DateTime, default=datetime.utcnow),
    Column('notes', String(1000), server_default=''),
    Column('purchase_price', Float, nullable=True),
    Column('shares', Float, nullable=True),
    Column('list_type', String(50), server_default='watchlist'),
    UniqueConstraint('user_id', 'ticker', name='uix_user_ticker')
)

history_table = Table(
    'analysis_history', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
    Column('fecha_consulta', String(50), nullable=False),
    Column('ticker', String(50), nullable=False),
    Column('empresa', String(255), server_default=''),
    Column('sector', String(255), server_default=''),
    Column('precio_mercado', Float),
    Column('eps_hist', Float),
    Column('eps_actual', Float),
    Column('eps_tendencia', String(50), server_default=''),
    Column('fcf_hist', Float),
    Column('fcf_actual', Float),
    Column('fcf_tendencia', String(50), server_default=''),
    Column('roic_hist', Float),
    Column('roic_actual', Float),
    Column('roic_tendencia', String(50), server_default=''),
    Column('per_actual', Float),
    Column('ev_fcf_actual', Float),
    Column('valor_intrinseco_graham', Float),
    Column('valor_intrinseco_dcf', Float),
    Column('margen_seguridad', Float),
    Column('ms_absoluto', Float),
    Column('ms_relativo', Float),
    Column('estado_semaforo', String(50), server_default=''),
    Column('alerta_compra', Integer, server_default='0'),
    Column('calidad', String(50), server_default=''),
    Column('non_gaap_flag', String(50), server_default=''),
    Column('raw_data', String, server_default=''),
    UniqueConstraint('user_id', 'fecha_consulta', 'ticker', name='uix_history_user_fecha_ticker')
)

def init_db():
    metadata.create_all(engine)
    
    # Create default admin if users is empty
    with engine.begin() as conn:
        count = conn.scalar(select(func.count()).select_from(users_table))
        if count == 0:
            import bcrypt
            pw_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt(rounds=10)).decode('utf-8')
            conn.execute(insert(users_table).values(
                username='admin',
                password_hash=pw_hash,
                role='admin'
            ))

# ─── CRUD Functions ──────────────────────────────────────────────

def create_user(username: str, password_hash: str) -> int:
    with engine.begin() as conn:
        res = conn.execute(insert(users_table).values(
            username=username.lower().strip(),
            password_hash=password_hash
        ))
        return res.inserted_primary_key[0]

def get_user_by_username(username: str):
    with engine.connect() as conn:
        row = conn.execute(
            select(users_table).where(users_table.c.username == username.lower().strip())
        ).mappings().first()
        return dict(row) if row else None

def get_user_by_id(user_id: int):
    with engine.connect() as conn:
        row = conn.execute(
            select(users_table).where(users_table.c.id == user_id)
        ).mappings().first()
        return dict(row) if row else None

def get_all_users_stats():
    with engine.connect() as conn:
        stmt = select(
            users_table.c.id,
            users_table.c.username,
            users_table.c.role,
            users_table.c.created_at,
            func.count(portfolio_table.c.id).label('portfolio_count')
        ).select_from(
            users_table.outerjoin(portfolio_table, users_table.c.id == portfolio_table.c.user_id)
        ).group_by(users_table.c.id).order_by(users_table.c.created_at.desc())
        
        rows = conn.execute(stmt).mappings().all()
        results = []
        for r in rows:
            d = dict(r)
            if isinstance(d['created_at'], datetime):
                d['created_at'] = d['created_at'].isoformat()
            results.append(d)
        return results

def delete_user_and_data(user_id: int) -> bool:
    with engine.begin() as conn:
        res = conn.execute(delete(users_table).where(users_table.c.id == user_id))
        return res.rowcount > 0

def get_portfolio(user_id: int):
    with engine.connect() as conn:
        stmt = select(
            portfolio_table.c.ticker,
            portfolio_table.c.added_at,
            portfolio_table.c.notes,
            portfolio_table.c.purchase_price,
            portfolio_table.c.shares,
            portfolio_table.c.list_type
        ).where(portfolio_table.c.user_id == user_id).order_by(portfolio_table.c.added_at.desc())
        
        rows = conn.execute(stmt).mappings().all()
        results = []
        for r in rows:
            d = dict(r)
            if isinstance(d['added_at'], datetime):
                d['added_at'] = d['added_at'].isoformat()
            results.append(d)
        return results

def add_to_portfolio(user_id: int, ticker: str, notes: str = '', list_type: str = 'watchlist') -> bool:
    from sqlalchemy.exc import IntegrityError
    with engine.begin() as conn:
        try:
            conn.execute(insert(portfolio_table).values(
                user_id=user_id,
                ticker=ticker.upper().strip(),
                notes=notes,
                list_type=list_type
            ))
            return True
        except IntegrityError:
            return False

def remove_from_portfolio(user_id: int, ticker: str) -> bool:
    with engine.begin() as conn:
        res = conn.execute(
            delete(portfolio_table)
            .where(portfolio_table.c.user_id == user_id)
            .where(portfolio_table.c.ticker == ticker.upper().strip())
        )
        return res.rowcount > 0

def update_portfolio_position(user_id: int, ticker: str, purchase_price: float = None, shares: float = None, list_type: str = None) -> bool:
    """Update purchase price, shares, and/or list_type for a portfolio position."""
    with engine.begin() as conn:
        values = {}
        if purchase_price is not None:
            values['purchase_price'] = purchase_price
        if shares is not None:
            values['shares'] = shares
        if list_type is not None:
            values['list_type'] = list_type
        if not values:
            return False
        res = conn.execute(
            update(portfolio_table)
            .where(portfolio_table.c.user_id == user_id)
            .where(portfolio_table.c.ticker == ticker.upper().strip())
            .values(**values)
        )
        return res.rowcount > 0

def save_analysis(user_id: int, data: dict):
    from sqlalchemy.exc import IntegrityError
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    ticker = data.get('ticker', '').upper().strip()
    
    with engine.begin() as conn:
        try:
            conn.execute(insert(history_table).values(
                user_id=user_id,
                fecha_consulta=timestamp,
                ticker=ticker,
                empresa=data.get('empresa', ''),
                sector=data.get('sector', ''),
                precio_mercado=data.get('current_price'),
                eps_hist=data.get('eps_hist_avg'),
                eps_actual=data.get('eps_ttm'),
                eps_tendencia=data.get('eps_trend', ''),
                fcf_hist=data.get('fcf_real_hist_avg'),
                fcf_actual=data.get('fcf_real_ttm'),
                fcf_tendencia=data.get('fcf_trend', ''),
                roic_hist=data.get('roic_hist_avg'),
                roic_actual=data.get('roic_current'),
                roic_tendencia=data.get('roic_trend', ''),
                per_actual=data.get('per_actual'),
                ev_fcf_actual=data.get('ev_fcf_actual'),
                valor_intrinseco_graham=data.get('graham_value'),
                valor_intrinseco_dcf=data.get('dcf_value'),
                margen_seguridad=data.get('margen_seguridad'),
                ms_absoluto=data.get('ms_absoluto'),
                ms_relativo=data.get('ms_relativo'),
                estado_semaforo=data.get('estado_semaforo', ''),
                alerta_compra=data.get('alerta_compra', 0),
                calidad=data.get('calidad', ''),
                non_gaap_flag=data.get('non_gaap_flag', ''),
                raw_data=json.dumps(data)
            ))
        except IntegrityError:
            pass

def get_history(user_id: int, ticker: str = None, limit: int = 500):
    with engine.connect() as conn:
        if ticker:
            stmt = select(history_table).where(
                (history_table.c.user_id == user_id) & 
                (history_table.c.ticker == ticker.upper().strip())
            ).order_by(history_table.c.fecha_consulta.desc()).limit(limit)
        else:
            stmt = select(history_table).where(
                history_table.c.user_id == user_id
            ).order_by(history_table.c.fecha_consulta.desc()).limit(limit)
            
        rows = conn.execute(stmt).mappings().all()
        return [dict(r) for r in rows]

def get_latest_analysis(user_id: int, ticker: str):
    with engine.connect() as conn:
        stmt = select(history_table).where(
            (history_table.c.user_id == user_id) & 
            (history_table.c.ticker == ticker.upper().strip())
        ).order_by(history_table.c.fecha_consulta.desc()).limit(1)
        row = conn.execute(stmt).mappings().first()
        return dict(row) if row else None
