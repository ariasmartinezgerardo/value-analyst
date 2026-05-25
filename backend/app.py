"""
app.py — Flask API Server for Value Analyst App.
Serves the frontend and provides REST API endpoints for
portfolio management, analysis, scanning, and authentication.
"""

import os
import logging
import datetime
import time
from functools import wraps
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor, as_completed

import jwt
import database as db
from fetcher import fetch_company_data
from engine import run_full_analysis, generate_investment_thesis
from scanner import scan_opportunities

# ─── App Setup ────────────────────────────────────────────────────
app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'value-analyst-super-secret-key-12345')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
db.init_db()

# Prevent caching of static files (HTML, JS, CSS)
@app.after_request
def add_header(response):
    response.cache_control.max_age = 0
    response.cache_control.no_cache = True
    response.cache_control.no_store = True
    response.cache_control.must_revalidate = True
    return response


# ─── Auth Decorator ───────────────────────────────────────────────

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Check Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'error': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = db.get_user_by_id(data['user_id'])
            if not current_user:
                return jsonify({'error': 'User not found!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid!'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'error': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = db.get_user_by_id(data['user_id'])
            if not current_user:
                return jsonify({'error': 'User not found!'}), 401
            if current_user.get('role') != 'admin':
                return jsonify({'error': 'Admin privileges required!'}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid!'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated


# ─── Frontend Serving ────────────────────────────────────────────

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    file_path = os.path.join(app.static_folder, path)
    if os.path.isfile(file_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')


# ─── Authentication API ───────────────────────────────────────────

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user account."""
    data = request.get_json() or {}
    username = data.get('username', '').lower().strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
        
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
    existing_user = db.get_user_by_username(username)
    if existing_user:
        return jsonify({'error': 'Username is already taken'}), 409
        
    # Hash password using bcrypt
    import bcrypt
    pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=10)).decode('utf-8')
    
    try:
        user_id = db.create_user(username, pw_hash)
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({'error': 'Error creating user account'}), 500
        
    # Generate session token
    token = jwt.encode({
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    token_str = token.decode('utf-8') if isinstance(token, bytes) else token
    
    return jsonify({
        'message': 'User registered successfully',
        'token': token_str,
        'username': username,
        'role': 'user'
    }), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Log in an existing user and return a JWT."""
    data = request.get_json() or {}
    username = data.get('username', '').lower().strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
        
    user = db.get_user_by_username(username)
    if not user:
        return jsonify({'error': 'Invalid username or password'}), 401
        
    import bcrypt
    # Check password hash
    if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        return jsonify({'error': 'Invalid username or password'}), 401
        
    # Generate session token (valid for 30 days)
    token = jwt.encode({
        'user_id': user['id'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    token_str = token.decode('utf-8') if isinstance(token, bytes) else token
    
    return jsonify({
        'message': 'Logged in successfully',
        'token': token_str,
        'username': user['username'],
        'role': user.get('role', 'user')
    }), 200

# ─── Admin API (Admin-secured) ───────────────────────────────────

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def get_users(current_user):
    """Get all users for the admin panel."""
    users = db.get_all_users_stats()
    return jsonify({'users': users})

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(current_user, user_id):
    """Delete a user and all their data."""
    if current_user['id'] == user_id:
        return jsonify({'error': 'Cannot delete your own admin account'}), 400
    
    deleted = db.delete_user_and_data(user_id)
    if deleted:
        return jsonify({'message': f'User {user_id} deleted successfully'})
    else:
        return jsonify({'error': 'User not found'}), 404


# ─── Portfolio API (User-secured) ────────────────────────────────

@app.route('/api/portfolio', methods=['GET'])
@token_required
def get_portfolio(current_user):
    """Get all tickers in portfolio with latest analysis data for this user."""
    portfolio = db.get_portfolio(current_user['id'])
    enriched = []
    for item in portfolio:
        ticker = item['ticker']
        latest = db.get_latest_analysis(current_user['id'], ticker)
        enriched.append({
            'ticker': ticker,
            'added_at': item.get('added_at', ''),
            'empresa': latest.get('empresa', '') if latest else '',
            'precio_mercado': latest.get('precio_mercado') if latest else None,
            'margen_seguridad': latest.get('margen_seguridad') if latest else None,
            'calidad': latest.get('calidad', '') if latest else '',
            'roic_actual': latest.get('roic_actual') if latest else None,
            'per_actual': latest.get('per_actual') if latest else None,
            'estado_semaforo': latest.get('estado_semaforo', '') if latest else '',
            'last_updated': latest.get('fecha_consulta', '') if latest else '',
        })
    return jsonify({'portfolio': enriched})


@app.route('/api/portfolio', methods=['POST'])
@token_required
def add_ticker(current_user):
    """Add a ticker to the user's portfolio."""
    data = request.get_json() or {}
    ticker = data.get('ticker', '').upper().strip()
    if not ticker:
        return jsonify({'error': 'Ticker is required'}), 400

    added = db.add_to_portfolio(current_user['id'], ticker, data.get('notes', ''))
    if added:
        return jsonify({'message': f'{ticker} added to portfolio', 'ticker': ticker}), 201
    else:
        return jsonify({'error': f'{ticker} already in portfolio'}), 409


@app.route('/api/portfolio/<ticker>', methods=['DELETE'])
@token_required
def remove_ticker(current_user, ticker):
    """Remove a ticker from the user's portfolio."""
    removed = db.remove_from_portfolio(current_user['id'], ticker.upper().strip())
    if removed:
        return jsonify({'message': f'{ticker.upper()} removed from portfolio'})
    else:
        return jsonify({'error': f'{ticker.upper()} not found in portfolio'}), 404


# ─── Analysis API (User-secured) ─────────────────────────────────

@app.route('/api/company/<ticker>', methods=['GET'])
@token_required
def get_company_detail(current_user, ticker):
    """
    Fetch and analyze a single company for the authenticated user.
    Always fetches fresh data and saves to cumulative history.
    """
    ticker = ticker.upper().strip()
    logger.info(f"Analyzing {ticker} for user {current_user['username']}...")

    # Fetch data
    raw_data = fetch_company_data(ticker)
    if raw_data.get('error'):
        return jsonify({'error': raw_data['error']}), 404

    # Run analysis
    analysis = run_full_analysis(raw_data)
    if analysis.get('error'):
        return jsonify({'error': analysis['error']}), 500

    # Generate thesis
    analysis['thesis'] = generate_investment_thesis(analysis)

    # Save to history (cumulative, user-isolated)
    db.save_analysis(current_user['id'], {
        'ticker': analysis.get('ticker'),
        'empresa': analysis.get('empresa'),
        'sector': analysis.get('sector'),
        'precio_mercado': analysis.get('current_price'),
        'eps_hist': analysis.get('eps_hist_avg'),
        'eps_actual': analysis.get('eps_ttm'),
        'eps_tendencia': analysis.get('eps_trend'),
        'fcf_hist': analysis.get('fcf_real_hist_avg'),
        'fcf_actual': analysis.get('fcf_real_ttm'),
        'fcf_tendencia': analysis.get('fcf_trend'),
        'roic_hist': analysis.get('roic_hist_avg'),
        'roic_actual': analysis.get('roic_current'),
        'roic_tendencia': analysis.get('roic_trend'),
        'per_actual': analysis.get('per_actual'),
        'ev_fcf_actual': analysis.get('ev_fcf_actual'),
        'valor_intrinseco_graham': analysis.get('graham_value'),
        'valor_intrinseco_dcf': analysis.get('dcf_value'),
        'margen_seguridad': analysis.get('margen_seguridad'),
        'ms_absoluto': analysis.get('ms_absoluto'),
        'ms_relativo': analysis.get('ms_relativo'),
        'estado_semaforo': analysis.get('estado_semaforo'),
        'alerta_compra': analysis.get('alerta_compra'),
        'calidad': analysis.get('calidad'),
        'non_gaap_flag': analysis.get('non_gaap_flag'),
        'raw_data': raw_data
    })

    return jsonify(analysis)


@app.route('/api/update', methods=['POST'])
@token_required
def update_all(current_user):
    """
    Execute UPDATE: Refresh analysis for all portfolio companies of this user.
    Runs in parallel for speed.
    """
    portfolio = db.get_portfolio(current_user['id'])
    if not portfolio:
        return jsonify({'message': 'Portfolio is empty', 'results': []})

    tickers = [p['ticker'] for p in portfolio]
    results = []
    errors = []

    def analyze_ticker(ticker):
        raw_data = fetch_company_data(ticker)
        if raw_data.get('error'):
            return {'ticker': ticker, 'error': raw_data['error']}

        analysis = run_full_analysis(raw_data)
        if analysis.get('error'):
            return {'ticker': ticker, 'error': analysis['error']}

        # Save to history (user-isolated)
        db.save_analysis(current_user['id'], {
            'ticker': analysis.get('ticker'),
            'empresa': analysis.get('empresa'),
            'sector': analysis.get('sector'),
            'precio_mercado': analysis.get('current_price'),
            'eps_hist': analysis.get('eps_hist_avg'),
            'eps_actual': analysis.get('eps_ttm'),
            'eps_tendencia': analysis.get('eps_trend'),
            'fcf_hist': analysis.get('fcf_real_hist_avg'),
            'fcf_actual': analysis.get('fcf_real_ttm'),
            'fcf_tendencia': analysis.get('fcf_trend'),
            'roic_hist': analysis.get('roic_hist_avg'),
            'roic_actual': analysis.get('roic_current'),
            'roic_tendencia': analysis.get('roic_trend'),
            'per_actual': analysis.get('per_actual'),
            'ev_fcf_actual': analysis.get('ev_fcf_actual'),
            'valor_intrinseco_graham': analysis.get('graham_value'),
            'valor_intrinseco_dcf': analysis.get('dcf_value'),
            'margen_seguridad': analysis.get('margen_seguridad'),
            'ms_absoluto': analysis.get('ms_absoluto'),
            'ms_relativo': analysis.get('ms_relativo'),
            'estado_semaforo': analysis.get('estado_semaforo'),
            'alerta_compra': analysis.get('alerta_compra'),
            'calidad': analysis.get('calidad'),
            'non_gaap_flag': analysis.get('non_gaap_flag'),
            'raw_data': raw_data
        })

        return {
            'ticker': analysis.get('ticker'),
            'empresa': analysis.get('empresa'),
            'precio_mercado': analysis.get('current_price'),
            'margen_seguridad': analysis.get('margen_seguridad'),
            'calidad': analysis.get('calidad'),
            'error': None
        }

    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = {}
        for t in tickers:
            futures[executor.submit(analyze_ticker, t)] = t
            time.sleep(2) # Retardo de 2 segundos para no enfadar a Yahoo Finance

        for future in as_completed(futures):
            try:
                result = future.result()
                if result.get('error'):
                    errors.append(result)
                else:
                    results.append(result)
            except Exception as e:
                ticker = futures[future]
                errors.append({'ticker': ticker, 'error': str(e)})

    return jsonify({
        'message': f'Updated {len(results)} companies',
        'results': results,
        'errors': errors
    })


# ─── Explorer API (User-secured) ─────────────────────────────────

@app.route('/api/explore', methods=['GET'])
@token_required
def explore(current_user):
    """
    Scan for undervalued opportunities.
    Optional query params: max_per, min_roic, min_fcf_yield, min_mos
    """
    criteria = {
        'max_per': float(request.args.get('max_per', 20)),
        'min_roic': float(request.args.get('min_roic', 12)),
        'min_fcf_yield': float(request.args.get('min_fcf_yield', 5)),
        'min_mos': float(request.args.get('min_mos', 20)),
    }
    market = request.args.get('market', 'sp500')

    logger.info(f"User {current_user['username']} starting opportunity scan in {market} with criteria: {criteria}")
    opportunities = scan_opportunities(criteria=criteria, market=market)
    logger.info(f"Scan complete: {len(opportunities)} opportunities found")

    return jsonify({
        'criteria': criteria,
        'count': len(opportunities),
        'opportunities': opportunities
    })


# ─── History API (User-secured) ──────────────────────────────────

@app.route('/api/history', methods=['GET'])
@token_required
def get_history(current_user):
    """Get analysis history for the current user, optionally filtered by ticker."""
    ticker = request.args.get('ticker')
    limit = int(request.args.get('limit', 500))
    records = db.get_history(current_user['id'], ticker=ticker, limit=limit)
    return jsonify({'count': len(records), 'history': records})


# ─── Health Check ─────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'app': 'Value Analyst', 'version': '1.1.0', 'multiuser': True})


# ─── Run Server ──────────────────────────────────────────────────

if __name__ == '__main__':
    logger.info("🚀 Value Analyst API Server starting with secure multi-user support...")
    logger.info("📊 Open http://localhost:5000 in your browser")
    app.run(host='0.0.0.0', port=5000, debug=True)

