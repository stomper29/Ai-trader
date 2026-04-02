"""
Database module — MySQL via Railway
All bots use this module for persistent storage.
Set DATABASE_URL env var or individual DB_* vars.
"""

import os
import json
import time
from datetime import datetime
from urllib.parse import urlparse

import mysql.connector
from mysql.connector import pooling

# ── CONNECTION CONFIG ─────────────────────────────────
def _parse_url(url: str) -> dict:
    p = urlparse(url)
    return {
        "host":     p.hostname,
        "port":     p.port or 3306,
        "user":     p.username,
        "password": p.password,
        "database": (p.path or "/railway").lstrip("/") or "railway",
    }

_DB_URL = os.environ.get(
    "DATABASE_URL",
    "mysql://root:zJiIVtuGZLYkAoLoWVNxwwFhAsyyrNkc@mainline.proxy.rlwy.net:24601/railway"
)
_CFG = _parse_url(_DB_URL)

# Connection pool (size 5 — enough for all bots running in threads)
_pool: pooling.MySQLConnectionPool | None = None

def _get_pool() -> pooling.MySQLConnectionPool:
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="aitrader",
            pool_size=5,
            pool_reset_session=True,
            host=_CFG["host"],
            port=_CFG["port"],
            user=_CFG["user"],
            password=_CFG["password"],
            database=_CFG["database"],
            connection_timeout=10,
            autocommit=True,
        )
    return _pool

def get_conn():
    """Get a connection from the pool (with retry)."""
    for attempt in range(3):
        try:
            return _get_pool().get_connection()
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)

# ── SCHEMA SETUP ─────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS trade_log (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    timestamp     DATETIME     NOT NULL,
    ticker        VARCHAR(20)  NOT NULL,
    action        VARCHAR(10)  NOT NULL,
    qty           FLOAT,
    order_type    VARCHAR(20),
    limit_price   FLOAT,
    stop_loss     FLOAT,
    take_profit   FLOAT,
    strategy      VARCHAR(50),
    confidence    INT,
    reasoning     TEXT,
    status        VARCHAR(50)  DEFAULT 'submitted',
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ticker (ticker),
    INDEX idx_timestamp (timestamp)
);

CREATE TABLE IF NOT EXISTS crypto_signals (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    timestamp        DATETIME     NOT NULL,
    scan_type        VARCHAR(20),
    coin             VARCHAR(20)  NOT NULL,
    pair             VARCHAR(20),
    action           VARCHAR(10)  NOT NULL,
    timeframe        VARCHAR(30),
    entry_low        FLOAT,
    entry_high       FLOAT,
    stop_loss        FLOAT,
    take_profit_1    FLOAT,
    take_profit_2    FLOAT,
    take_profit_3    FLOAT,
    position_size_pct FLOAT,
    confidence       INT,
    tier             INT,
    catalyst         TEXT,
    on_chain_signal  TEXT,
    invalidation     TEXT,
    reasoning        TEXT,
    created_at       DATETIME     DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_coin (coin),
    INDEX idx_timestamp (timestamp)
);

CREATE TABLE IF NOT EXISTS auto_accept_log (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    timestamp     DATETIME     NOT NULL,
    symbol        VARCHAR(20),
    action        VARCHAR(10),
    notional      FLOAT,
    status        VARCHAR(100),
    confidence    INT,
    reasoning     TEXT,
    daily_count   INT,
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol (symbol),
    INDEX idx_status (status)
);

CREATE TABLE IF NOT EXISTS legal_sessions (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    session_id    VARCHAR(50)  NOT NULL UNIQUE,
    updated_at    DATETIME     NOT NULL,
    message_count INT          DEFAULT 0,
    history_json  LONGTEXT,
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id)
);

CREATE TABLE IF NOT EXISTS market_context (
    id                    INT AUTO_INCREMENT PRIMARY KEY,
    timestamp             DATETIME    NOT NULL,
    btc_price             FLOAT,
    eth_price             FLOAT,
    btc_dominance         FLOAT,
    fear_greed            INT,
    phase                 VARCHAR(30),
    trend                 VARCHAR(20),
    altseason_probability FLOAT,
    macro_notes           TEXT,
    summary               TEXT,
    created_at            DATETIME    DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp)
);

CREATE TABLE IF NOT EXISTS daily_reports (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    report_date     DATE         NOT NULL UNIQUE,
    win_rate        FLOAT,
    profit_factor   FLOAT,
    best_strategy   VARCHAR(50),
    worst_strategy  VARCHAR(50),
    market_regime   VARCHAR(30),
    top_sectors     TEXT,
    adjustments     TEXT,
    watchlist       TEXT,
    summary         TEXT,
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date (report_date)
);
"""

def init_db():
    """Create all tables if they don't exist."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        for statement in SCHEMA.strip().split(";"):
            stmt = statement.strip()
            if stmt:
                cur.execute(stmt)
        print("[DB] Schema initialized OK")
    finally:
        conn.close()

# ── TRADE LOG ─────────────────────────────────────────
def log_trade(trade: dict):
    """Insert a stock trade into trade_log."""
    sql = """
    INSERT INTO trade_log
        (timestamp, ticker, action, qty, order_type, limit_price,
         stop_loss, take_profit, strategy, confidence, reasoning, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    ts = trade.get("timestamp", datetime.now().isoformat())
    try:
        ts_dt = datetime.fromisoformat(ts)
    except Exception:
        ts_dt = datetime.now()

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, (
            ts_dt,
            trade.get("ticker", ""),
            trade.get("action", ""),
            trade.get("qty"),
            trade.get("order_type", "market"),
            trade.get("limit_price"),
            trade.get("stop_loss"),
            trade.get("take_profit"),
            trade.get("strategy", ""),
            trade.get("confidence"),
            trade.get("reasoning", "")[:500] if trade.get("reasoning") else "",
            trade.get("status", "submitted"),
        ))
    finally:
        conn.close()

def get_recent_trades(n: int = 30) -> list[dict]:
    """Fetch the most recent n trades."""
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM trade_log ORDER BY timestamp DESC LIMIT %s", (n,)
        )
        rows = cur.fetchall()
        for r in rows:
            if isinstance(r.get("timestamp"), datetime):
                r["timestamp"] = r["timestamp"].isoformat()
        return rows
    finally:
        conn.close()

# ── CRYPTO SIGNALS ────────────────────────────────────
def log_crypto_signal(signal: dict, scan_type: str = "full"):
    """Insert a crypto signal into crypto_signals."""
    ez = signal.get("entry_zone", {})
    entry_low  = ez.get("low")  if isinstance(ez, dict) else None
    entry_high = ez.get("high") if isinstance(ez, dict) else None

    ts = signal.get("_source_ts", signal.get("timestamp", datetime.now().isoformat()))
    try:
        ts_dt = datetime.fromisoformat(ts)
    except Exception:
        ts_dt = datetime.now()

    sql = """
    INSERT INTO crypto_signals
        (timestamp, scan_type, coin, pair, action, timeframe,
         entry_low, entry_high, stop_loss, take_profit_1, take_profit_2, take_profit_3,
         position_size_pct, confidence, tier, catalyst, on_chain_signal,
         invalidation, reasoning)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, (
            ts_dt, scan_type,
            signal.get("coin", ""),
            signal.get("pair", ""),
            signal.get("action", ""),
            signal.get("timeframe", ""),
            entry_low, entry_high,
            signal.get("stop_loss"),
            signal.get("take_profit_1"),
            signal.get("take_profit_2"),
            signal.get("take_profit_3"),
            signal.get("position_size_pct"),
            signal.get("confidence"),
            signal.get("tier"),
            (signal.get("catalyst", "") or "")[:500],
            (signal.get("on_chain_signal", "") or "")[:500],
            (signal.get("invalidation", "") or "")[:500],
            (signal.get("reasoning", "") or "")[:500],
        ))
    finally:
        conn.close()

def get_recent_crypto_signals(n: int = 20) -> list[dict]:
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM crypto_signals ORDER BY timestamp DESC LIMIT %s", (n,)
        )
        rows = cur.fetchall()
        for r in rows:
            if isinstance(r.get("timestamp"), datetime):
                r["timestamp"] = r["timestamp"].isoformat()
        return rows
    finally:
        conn.close()

def get_latest_crypto_timestamp() -> str:
    """Return the ISO timestamp of the most recent crypto signal (for polling)."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT MAX(timestamp) FROM crypto_signals")
        row = cur.fetchone()
        if row and row[0]:
            return row[0].isoformat()
        return ""
    finally:
        conn.close()

# ── AUTO ACCEPT LOG ───────────────────────────────────
def log_auto_trade(symbol: str, action: str, notional: float,
                   status: str, confidence: int, reasoning: str, daily_count: int):
    sql = """
    INSERT INTO auto_accept_log
        (timestamp, symbol, action, notional, status, confidence, reasoning, daily_count)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, (
            datetime.now(), symbol, action, notional,
            status[:100], confidence, (reasoning or "")[:500], daily_count
        ))
    finally:
        conn.close()

# ── LEGAL SESSIONS ────────────────────────────────────
def save_legal_session(session_id: str, history: list):
    sql = """
    INSERT INTO legal_sessions (session_id, updated_at, message_count, history_json)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        updated_at    = VALUES(updated_at),
        message_count = VALUES(message_count),
        history_json  = VALUES(history_json)
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, (
            session_id,
            datetime.now(),
            len(history),
            json.dumps(history),
        ))
    finally:
        conn.close()

def load_legal_session(session_id: str) -> list | None:
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT history_json FROM legal_sessions WHERE session_id = %s",
            (session_id,)
        )
        row = cur.fetchone()
        if row:
            return json.loads(row["history_json"])
        return None
    finally:
        conn.close()

def list_legal_sessions() -> list[dict]:
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT session_id, updated_at, message_count FROM legal_sessions "
            "ORDER BY updated_at DESC LIMIT 20"
        )
        rows = cur.fetchall()
        for r in rows:
            if isinstance(r.get("updated_at"), datetime):
                r["updated_at"] = r["updated_at"].isoformat()
        return rows
    finally:
        conn.close()

# ── MARKET CONTEXT ────────────────────────────────────
def save_market_context(data: dict):
    regime = data.get("market_regime", {})
    sql = """
    INSERT INTO market_context
        (timestamp, btc_price, eth_price, btc_dominance, fear_greed,
         phase, trend, altseason_probability, macro_notes, summary)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, (
            datetime.now(),
            data.get("btc_price"),
            data.get("eth_price"),
            regime.get("btc_dominance"),
            regime.get("fear_greed"),
            regime.get("phase", ""),
            regime.get("trend", ""),
            data.get("altseason_probability"),
            (data.get("macro_notes") or "")[:1000],
            (regime.get("summary") or "")[:1000],
        ))
    finally:
        conn.close()

# ── DAILY REPORTS ─────────────────────────────────────
def save_daily_report(data: dict):
    sql = """
    INSERT INTO daily_reports
        (report_date, win_rate, profit_factor, best_strategy, worst_strategy,
         market_regime, top_sectors, adjustments, watchlist, summary)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
        win_rate       = VALUES(win_rate),
        profit_factor  = VALUES(profit_factor),
        best_strategy  = VALUES(best_strategy),
        worst_strategy = VALUES(worst_strategy),
        market_regime  = VALUES(market_regime),
        top_sectors    = VALUES(top_sectors),
        adjustments    = VALUES(adjustments),
        watchlist      = VALUES(watchlist),
        summary        = VALUES(summary)
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, (
            datetime.now().date(),
            data.get("winRate"),
            data.get("profitFactor"),
            data.get("bestStrategy", ""),
            data.get("worstStrategy", ""),
            data.get("marketRegime", ""),
            json.dumps(data.get("topSectors", [])),
            json.dumps(data.get("adjustments", [])),
            json.dumps(data.get("watchlist", [])),
            (data.get("summary") or "")[:1000],
        ))
    finally:
        conn.close()

# ── HEALTH CHECK ──────────────────────────────────────
def health_check() -> bool:
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        conn.close()
        return True
    except Exception as e:
        print(f"[DB] Health check failed: {e}")
        return False

if __name__ == "__main__":
    print(f"[DB] Connecting to {_CFG['host']}:{_CFG['port']} / {_CFG['database']}")
    if health_check():
        print("[DB] Connection OK")
        init_db()
    else:
        print("[DB] Connection FAILED")
