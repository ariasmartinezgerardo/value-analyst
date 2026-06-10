"""
telegram_bot.py — Naranjos Analyst Bot for Telegram.
Provides instant fundamental analysis of any public company
directly in Telegram chats via the Value Analyst engine.

Commands:
    /start          — Welcome message
    /a TICKER       — Full analysis (short alias)
    /analizar TICKER — Full analysis
    /help           — Show available commands

Usage:
    1. Set TELEGRAM_BOT_TOKEN in backend/.env
    2. pip install python-telegram-bot
    3. python telegram_bot.py
"""

import os
import sys
import asyncio
import logging
import html as html_module

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

# ─── Path Setup ──────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetcher import fetch_company_data
from engine import run_full_analysis, generate_investment_thesis

# ─── Load .env manually (no extra dependency) ────────────────────
def _load_env():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

_load_env()

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN no está definido.")
    print("   Crea un archivo backend/.env con: TELEGRAM_BOT_TOKEN=tu_token")
    sys.exit(1)

logger = logging.getLogger(__name__)

# ─── Currency Symbols ────────────────────────────────────────────
CURRENCY_SYMBOLS = {
    'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'CHF': 'CHF ',
    'SEK': 'kr', 'NOK': 'kr', 'DKK': 'kr', 'CAD': 'C$', 'AUD': 'A$',
    'HKD': 'HK$', 'SGD': 'S$', 'KRW': '₩', 'TWD': 'NT$', 'INR': '₹',
    'BRL': 'R$', 'MXN': 'MX$', 'ZAR': 'R',
}


# ─── Formatting Helpers ──────────────────────────────────────────

def _fmt_price(value, symbol='$'):
    """Format a price with currency symbol."""
    if value is None or value == 0:
        return 'N/A'
    return f"{symbol}{value:,.2f}"


def _fmt_pct(value, sign=True):
    """Format a percentage value."""
    if value is None:
        return 'N/A'
    prefix = '+' if sign and value > 0 else ''
    return f"{prefix}{value:.1f}%"


def _fmt_ratio(value, suffix='x'):
    """Format a ratio like PER or Debt/EBITDA."""
    if value is None:
        return 'N/A'
    return f"{value:.1f}{suffix}"


# ─── Analysis Formatter ─────────────────────────────────────────

def format_analysis_message(r: dict) -> str:
    """
    Format a run_full_analysis result dict into a beautiful
    Telegram HTML message with emojis and structured sections.
    """
    currency = r.get('currency', 'USD')
    sym = CURRENCY_SYMBOLS.get(currency, f'{currency} ')

    # ── Header ──
    empresa = html_module.escape(r.get('empresa', r.get('ticker', '?')))
    ticker = r.get('ticker', '?')
    archetype = r.get('archetype_label', '')
    sector = html_module.escape(r.get('sector', '') or '')

    lines = [
        "🍊 <b>NARANJOS ANALYST</b>",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
        f"📊 <b>{empresa}</b> (<code>{ticker}</code>)",
        f"{archetype} · {sector}",
        "",
    ]

    # ── Valoración Principal ──
    price = r.get('current_price', 0)
    intrinsic = r.get('intrinsic_value', 0)
    mos = r.get('margen_seguridad')
    semaforo = r.get('estado_semaforo', '')

    lines.append(f"💰 <b>Precio:</b> {_fmt_price(price, sym)}")
    lines.append(f"💎 <b>Valor Intrínseco:</b> {_fmt_price(intrinsic, sym)}")
    lines.append(f"📐 <b>Margen de Seguridad:</b> {_fmt_pct(mos)}")
    lines.append("")
    lines.append(f"🚦 <b>{semaforo}</b>")
    lines.append("")

    # ── Métricas Fundamentales ──
    lines.append("━━━ Métricas Fundamentales ━━━")

    roic = r.get('roic_hist')
    if roic is not None:
        lines.append(f"▫️ ROIC Medio: {_fmt_pct(roic, sign=False)} {r.get('roic_trend', '')}")

    roic_curr = r.get('roic_current')
    if roic_curr is not None:
        lines.append(f"▫️ ROIC Actual: {_fmt_pct(roic_curr, sign=False)}")

    per = r.get('per_actual')
    if per and per > 0:
        lines.append(f"▫️ PER: {_fmt_ratio(per)}")

    per_fwd = r.get('per_forward')
    if per_fwd and per_fwd > 0:
        lines.append(f"▫️ PER Forward: {_fmt_ratio(per_fwd)}")

    fcf_yield = r.get('fcf_yield')
    if fcf_yield is not None:
        lines.append(f"▫️ FCF Yield: {_fmt_pct(fcf_yield, sign=False)}")

    debt = r.get('net_debt_ebitda')
    if debt is not None:
        lines.append(f"▫️ Deuda Neta/EBITDA: {_fmt_ratio(debt)}")

    ic = r.get('interest_coverage')
    if ic is not None and ic < 50:  # Only show if meaningful
        lines.append(f"▫️ Cobertura Intereses: {_fmt_ratio(ic, suffix='')}")

    piotroski = r.get('piotroski_score')
    if piotroski is not None:
        emoji = '🟢' if piotroski >= 7 else '🟡' if piotroski >= 4 else '🔴'
        lines.append(f"▫️ Piotroski: {emoji} {piotroski}/9")

    wacc = r.get('wacc_used')
    if wacc:
        lines.append(f"▫️ WACC: {wacc*100:.1f}%")

    calidad = r.get('calidad')
    if calidad:
        lines.append(f"▫️ Calidad: {calidad}")

    # ── Márgenes ──
    gm = r.get('current_gross_margin')
    om = r.get('current_operating_margin')
    nm = r.get('current_net_margin')
    if any(v is not None for v in [gm, om, nm]):
        lines.append("")
        lines.append("━━━ Márgenes ━━━")
        if gm is not None:
            lines.append(f"▫️ Bruto: {_fmt_pct(gm * 100, sign=False)}")
        if om is not None:
            lines.append(f"▫️ Operativo: {_fmt_pct(om * 100, sign=False)}")
        if nm is not None:
            lines.append(f"▫️ Neto: {_fmt_pct(nm * 100, sign=False)}")

    # ── Métricas Growth (si aplican) ──
    growth = r.get('growth_metrics', {})
    if growth and growth.get('has_growth_metrics'):
        lines.append("")
        lines.append("━━━ Métricas Growth ━━━")

        peg = growth.get('peg_trailing')
        if peg is not None:
            sig = growth.get('peg_signal', '')
            sig_emoji = {'undervalued': '🟢', 'fair': '🟡', 'overvalued': '🔴'}.get(sig, '')
            lines.append(f"▫️ PEG: {peg:.2f} {sig_emoji} ({sig})")

        r40 = growth.get('rule_of_40')
        if r40 is not None:
            r40_sig = growth.get('rule_of_40_signal', '')
            r40_emoji = {'premium': '🟢', 'acceptable': '🟡', 'weak': '🔴'}.get(r40_sig, '')
            lines.append(f"▫️ Rule of 40: {r40:.0f} {r40_emoji} ({r40_sig})")

        evr = growth.get('ev_revenue_current')
        if evr is not None:
            lines.append(f"▫️ EV/Revenue: {evr:.1f}x")
            evr_fwd = growth.get('ev_revenue_forward_3y')
            if evr_fwd:
                lines.append(f"   └ Forward 3Y: {evr_fwd:.1f}x")

    # ── Modelos de Valoración ──
    lines.append("")
    lines.append("━━━ Modelos de Valoración ━━━")

    graham = r.get('graham_value', 0)
    dcf = r.get('dcf_value', 0)
    alt = r.get('alt_value')

    if graham and graham > 0:
        lines.append(f"▫️ Graham: {_fmt_price(graham, sym)}")
    if dcf and dcf > 0:
        lines.append(f"▫️ DCF: {_fmt_price(dcf, sym)}")
        tp = r.get('terminal_pct')
        if tp:
            tp_warn = ' ⚠️' if tp > 60 else ''
            lines.append(f"   └ Peso Terminal: {tp:.0f}%{tp_warn}")
    if alt and alt > 0:
        alt_label = html_module.escape(r.get('alt_model', 'Alternativo'))
        lines.append(f"▫️ {alt_label}: {_fmt_price(alt, sym)}")

    # ── Tesis de Inversión ──
    thesis = r.get('thesis', '')
    if thesis:
        max_len = 700
        if len(thesis) > max_len:
            thesis = thesis[:max_len].rsplit(' ', 1)[0] + '…'
        thesis = html_module.escape(thesis)
        lines.append("")
        lines.append("━━━ Tesis de Inversión ━━━")
        lines.append(f"<i>{thesis}</i>")

    # ── Alertas ──
    warnings = []
    if piotroski is not None and piotroski <= 3:
        warnings.append("⚠️ RIESGO VALUE TRAP (Piotroski ≤ 3)")
    if r.get('terminal_pct') and r['terminal_pct'] > 60:
        warnings.append(f"⚠️ {r['terminal_pct']:.0f}% del DCF es valor terminal")
    non_gaap = r.get('non_gaap_flag', '')
    if '🚫' in non_gaap:
        warnings.append("🚫 Posible manipulación Non-GAAP")
    elif '⚠️' in non_gaap:
        warnings.append("⚠️ Divergencia EBITDA — revisar ajustes")
    if not r.get('dividend_yield_valid', True) and r.get('dividend_yield_raw'):
        warnings.append(f"⚠️ Dividend Yield ({r['dividend_yield_raw']*100:.0f}%) poco fiable")

    if warnings:
        lines.append("")
        lines.append("━━━ ⚠️ Alertas ━━━")
        for w in warnings:
            lines.append(w)

    # ── Data Quality (transparency) ──
    dq_warnings = r.get('data_quality_warnings', [])
    if dq_warnings:
        lines.append("")
        lines.append("━━━ 🔍 Calidad de Datos ━━━")
        for w in dq_warnings:
            lines.append(html_module.escape(w))

    # ── Footer ──
    lines.append("")
    lines.append("<i>📊 Value Analyst v1.3.0</i>")

    return '\n'.join(lines)


# ─── Command Handlers ────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command — welcome message."""
    msg = (
        "🍊 <b>Bienvenido a Naranjos Analyst</b>\n\n"
        "Soy tu analista de inversión en valor personal.\n"
        "Dime un ticker y te haré un análisis fundamental completo "
        "con valoración DCF, Graham, Piotroski, y más.\n\n"
        "<b>Uso rápido:</b>\n"
        "<code>/a AAPL</code>  — Analizar Apple\n"
        "<code>/a PLTR</code>  — Analizar Palantir\n"
        "<code>/a ITX.MC</code> — Analizar Inditex\n\n"
        "Escribe <b>/help</b> para ver todos los comandos.\n\n"
        "<i>Powered by Value Analyst v1.3.0</i>"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command — show available commands."""
    msg = (
        "🍊 <b>Naranjos Analyst — Ayuda</b>\n\n"
        "<b>Comandos:</b>\n"
        "/a <code>TICKER</code>  — Análisis completo (atajo)\n"
        "/analizar <code>TICKER</code>  — Análisis completo\n"
        "/start — Mensaje de bienvenida\n"
        "/help — Esta ayuda\n\n"
        "<b>Tickers de ejemplo:</b>\n"
        "🇺🇸 USA: <code>AAPL</code> <code>MSFT</code> <code>GOOGL</code> <code>PLTR</code> <code>NVDA</code>\n"
        "🇪🇸 España: <code>ITX.MC</code> <code>IBE.MC</code> <code>SAN.MC</code>\n"
        "🇫🇷 Francia: <code>MC.PA</code> <code>OR.PA</code> <code>AIR.PA</code>\n"
        "🇩🇪 Alemania: <code>SAP.DE</code> <code>SIE.DE</code>\n"
        "🇬🇧 UK: <code>SHEL.L</code> <code>AZN.L</code>\n\n"
        "<b>¿Qué analiza?</b>\n"
        "▫️ Valor Intrínseco (Graham + DCF multi-fase)\n"
        "▫️ Margen de Seguridad y Semáforo\n"
        "▫️ ROIC, PER, FCF Yield, Deuda\n"
        "▫️ Piotroski F-Score (value traps)\n"
        "▫️ Métricas Growth (PEG, Rule of 40)\n"
        "▫️ Detección de arquetipo automática\n"
        "▫️ Tesis de inversión generada\n\n"
        "<i>El análisis tarda ~10-15 segundos por empresa.</i>"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def cmd_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /a and /analizar — run full analysis on a ticker."""
    if not context.args:
        await update.message.reply_text(
            "❌ Falta el ticker.\n\n"
            "Ejemplo: <code>/a AAPL</code>",
            parse_mode=ParseMode.HTML
        )
        return

    ticker = context.args[0].upper().strip()

    # Validate ticker format (basic check)
    if len(ticker) > 12 or not any(c.isalpha() for c in ticker):
        await update.message.reply_text(
            f"❌ <code>{html_module.escape(ticker)}</code> no parece un ticker válido.",
            parse_mode=ParseMode.HTML
        )
        return

    # Send "thinking" message
    thinking = await update.message.reply_text(
        f"⏳ Analizando <b>{html_module.escape(ticker)}</b>…\n\n"
        f"<i>Descargando datos de mercado y ejecutando\n"
        f"modelos de valoración (Graham, DCF, Piotroski)…</i>",
        parse_mode=ParseMode.HTML
    )

    try:
        # ── Fetch data (run in thread to avoid blocking) ──
        raw_data = await asyncio.to_thread(fetch_company_data, ticker)

        if raw_data.get('error'):
            await thinking.edit_text(
                f"❌ No se encontró <b>{html_module.escape(ticker)}</b>\n\n"
                f"<i>{html_module.escape(str(raw_data['error']))}</i>\n\n"
                f"Comprueba el símbolo en Yahoo Finance.",
                parse_mode=ParseMode.HTML
            )
            return

        # ── Run analysis ──
        analysis = await asyncio.to_thread(run_full_analysis, raw_data)

        if analysis.get('error'):
            await thinking.edit_text(
                f"❌ Error al analizar <b>{html_module.escape(ticker)}</b>\n\n"
                f"<i>{html_module.escape(str(analysis['error']))}</i>",
                parse_mode=ParseMode.HTML
            )
            return

        # ── Generate thesis ──
        analysis['thesis'] = generate_investment_thesis(analysis)

        # ── Format and send ──
        result_msg = format_analysis_message(analysis)

        # Telegram message limit is 4096 characters
        if len(result_msg) > 4096:
            # Split: send main analysis, then thesis separately
            # Find thesis section and split there
            thesis_marker = "━━━ Tesis de Inversión ━━━"
            if thesis_marker in result_msg:
                idx = result_msg.index(thesis_marker)
                part1 = result_msg[:idx].rstrip()
                part2 = result_msg[idx:]
                await thinking.edit_text(part1, parse_mode=ParseMode.HTML)
                await update.message.reply_text(part2, parse_mode=ParseMode.HTML)
            else:
                await thinking.edit_text(result_msg[:4090] + "…", parse_mode=ParseMode.HTML)
        else:
            await thinking.edit_text(result_msg, parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {e}", exc_info=True)
        try:
            await thinking.edit_text(
                f"❌ Error inesperado al analizar <b>{html_module.escape(ticker)}</b>\n\n"
                f"<i>{html_module.escape(str(e)[:200])}</i>",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass  # If we can't even edit the message, give up gracefully


# ─── Main ────────────────────────────────────────────────────────

def main():
    """Initialize and start the Telegram bot."""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    logger.info("🍊 Naranjos Analyst Bot — Initializing...")

    app = Application.builder().token(TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler('start', cmd_start))
    app.add_handler(CommandHandler('help', cmd_help))
    app.add_handler(CommandHandler('a', cmd_analyze))
    app.add_handler(CommandHandler('analizar', cmd_analyze))

    logger.info("🍊 Naranjos Analyst Bot — Listening for messages...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
