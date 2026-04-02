"""
AUTO ACCEPT BOT
Automatically reads signals from the crypto scanner and trading bot,
applies configurable rules/filters, and executes approved trades
without human intervention. Includes circuit breakers and daily limits.
"""

import os
import json
import time
import schedule
import threading
from datetime import datetime, date
from pathlib import Path
import anthropic
import alpaca_trade_api as tradeapi
import db

# ── KEYS ──────────────────────────────────────────────
ALPACA_KEY    = os.environ.get("ALPACA_KEY")
ALPACA_SECRET = os.environ.get("ALPACA_SECRET")
ALPACA_BASE   = os.environ.get("ALPACA_BASE", "https://paper-api.alpaca.markets")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_KEY")

# ── RISK CONFIGURATION ────────────────────────────────
RULES = {
    # Signal quality thresholds
    "min_confidence":       72,     # minimum confidence % to auto-execute
    "min_tier":             2,      # minimum signal tier (1=best, 3=spec)

    # Position sizing
    "max_position_pct":     0.10,   # max 10% of portfolio per position
    "max_notional_usd":     5000,   # max $ per single trade
    "min_notional_usd":     50,     # min $ per single trade

    # Daily circuit breakers
    "max_daily_trades":     20,     # max trades per day
    "max_daily_loss_pct":   0.03,   # stop trading for the day if portfolio drops 3%
    "max_concurrent_pos":   10,     # max open positions at once

    # Asset filters
    "allowed_actions":      ["buy", "sell"],
    "blocked_coins":        [],     # coins you never want to trade
    "allowed_coins":        [],     # if non-empty, ONLY trade these coins

    # Crypto-specific
    "crypto_max_pct":       0.30,   # max 30% of portfolio in crypto total
    "stocks_max_pct":       0.70,   # max 70% in stocks total

    # Stop loss enforcement
    "enforce_stop_loss":    True,
    "default_sl_pct":       0.03,   # 3% default stop if signal has none
    "auto_exit_loss_pct":   0.05,   # auto-exit any position down 5%
}

SIGNAL_FILE      = "crypto_signals.json"
STOCK_SIGNAL_FILE = "trade_log.json"
AUTO_LOG         = "auto_accept_log.json"

# ── STATE ─────────────────────────────────────────────
state = {
    "daily_trades":    0,
    "daily_pnl_pct":   0.0,
    "portfolio_start": 0.0,
    "last_reset_date": None,
    "paused":          False,
    "pause_reason":    "",
    "total_auto_trades": 0,
    "total_blocked":   0,
}

# ── INIT ──────────────────────────────────────────────
alpaca = tradeapi.REST(ALPACA_KEY, ALPACA_SECRET, ALPACA_BASE)
claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

# ── DAILY RESET ───────────────────────────────────────
def daily_reset():
    today = date.today()
    if state["last_reset_date"] != today:
        print(f"\n[AUTO-BOT] Daily reset — {today}")
        try:
            acc = alpaca.get_account()
            state["portfolio_start"] = float(acc.portfolio_value)
        except Exception:
            pass
        state["daily_trades"]    = 0
        state["daily_pnl_pct"]   = 0.0
        state["paused"]          = False
        state["pause_reason"]    = ""
        state["last_reset_date"] = today

def update_daily_pnl():
    try:
        acc = alpaca.get_account()
        current = float(acc.portfolio_value)
        start   = state["portfolio_start"]
        if start > 0:
            state["daily_pnl_pct"] = (current - start) / start
    except Exception:
        pass

# ── CIRCUIT BREAKERS ──────────────────────────────────
def check_circuit_breakers() -> tuple[bool, str]:
    """Returns (is_ok, reason_if_blocked)."""
    daily_reset()
    update_daily_pnl()

    if state["paused"]:
        return False, f"Manually paused: {state['pause_reason']}"

    if state["daily_trades"] >= RULES["max_daily_trades"]:
        return False, f"Daily trade limit reached ({RULES['max_daily_trades']})"

    if state["daily_pnl_pct"] <= -RULES["max_daily_loss_pct"]:
        reason = f"Daily loss limit hit ({state['daily_pnl_pct']*100:.1f}%)"
        state["paused"]       = True
        state["pause_reason"] = reason
        return False, reason

    try:
        positions = alpaca.list_positions()
        if len(positions) >= RULES["max_concurrent_pos"]:
            return False, f"Max concurrent positions ({RULES['max_concurrent_pos']}) reached"
    except Exception:
        pass

    return True, ""

# ── SIGNAL FILTER ─────────────────────────────────────
def evaluate_signal(signal: dict, asset_type: str = "crypto") -> tuple[bool, str]:
    """
    Applies all rules to a signal.
    Returns (approved, reason).
    """
    action     = signal.get("action", "").lower()
    confidence = signal.get("confidence", 0)
    tier       = signal.get("tier", 3)
    coin       = signal.get("coin", signal.get("ticker", "")).upper()

    # Action filter
    if action not in RULES["allowed_actions"]:
        return False, f"Action '{action}' not in allowed list"

    # Confidence threshold
    if confidence < RULES["min_confidence"]:
        return False, f"Confidence {confidence}% < minimum {RULES['min_confidence']}%"

    # Tier filter
    if isinstance(tier, int) and tier > RULES["min_tier"]:
        return False, f"Tier {tier} below minimum tier {RULES['min_tier']}"

    # Blocked coins
    if coin in RULES["blocked_coins"]:
        return False, f"{coin} is on the blocked list"

    # Allowed coins filter (if whitelist is set)
    if RULES["allowed_coins"] and coin not in RULES["allowed_coins"]:
        return False, f"{coin} not in allowed coins whitelist"

    # Portfolio size check
    try:
        acc = alpaca.get_account()
        portfolio_val = float(acc.portfolio_value)
        cash          = float(acc.cash)

        max_pos = min(
            portfolio_val * RULES["max_position_pct"],
            RULES["max_notional_usd"]
        )
        min_pos = RULES["min_notional_usd"]

        size_pct = signal.get("position_size_pct", signal.get("qty", 0))

        if isinstance(size_pct, float) and size_pct > 0:
            notional = portfolio_val * (size_pct / 100)
        else:
            notional = max_pos * 0.5  # default half of max

        notional = min(notional, max_pos)

        if notional < min_pos:
            return False, f"Position size ${notional:.0f} below minimum ${min_pos}"

        if action == "buy" and notional > cash:
            return False, f"Insufficient cash (need ${notional:.0f}, have ${cash:.0f})"

    except Exception as e:
        return False, f"Account check failed: {e}"

    return True, "APPROVED"

# ── AI SECOND OPINION ─────────────────────────────────
def ai_second_opinion(signal: dict) -> tuple[bool, str]:
    """
    For high-value trades, ask Claude for a second opinion before executing.
    """
    try:
        acc = alpaca.get_account()
        portfolio_val = float(acc.portfolio_value)
    except Exception:
        return True, "Account unavailable — proceeding"

    size_pct  = signal.get("position_size_pct", 2)
    notional  = portfolio_val * (size_pct / 100)

    # Only use second opinion for larger trades
    if notional < 500:
        return True, "Small trade — no second opinion needed"

    coin       = signal.get("coin", signal.get("ticker", ""))
    action     = signal.get("action", "")
    confidence = signal.get("confidence", 0)
    reasoning  = signal.get("reasoning", "")
    catalyst   = signal.get("catalyst", "")

    response = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"""
Quick risk check for this trade signal:
- Asset: {coin}
- Action: {action}
- Position: ${notional:,.0f} ({size_pct}% of portfolio)
- Confidence: {confidence}%
- Catalyst: {catalyst}
- Reasoning: {reasoning}

Should this trade be AUTO-EXECUTED right now?
Any obvious red flags? Known scams or extreme market risks for {coin}?

Reply ONLY with: EXECUTE or BLOCK
Then one sentence of explanation.
"""
        }]
    )

    reply = ""
    for block in response.content:
        if hasattr(block, "text"):
            reply += block.text

    reply_upper = reply.strip().upper()
    if reply_upper.startswith("BLOCK"):
        return False, f"AI second opinion: {reply[:100]}"
    return True, f"AI cleared: {reply[:80]}"

# ── EXECUTION ─────────────────────────────────────────
ALPACA_CRYPTO_MAP = {
    "BTC": "BTCUSD", "ETH": "ETHUSD", "LTC": "LTCUSD",
    "BCH": "BCHUSD", "LINK": "LINKUSD", "UNI": "UNIUSD",
    "AAVE": "AAVEUSD", "SOL": "SOLUSD", "AVAX": "AVAXUSD",
    "MATIC": "MATICUSD", "DOT": "DOTUSD",
}

def execute_signal(signal: dict, asset_type: str = "crypto"):
    try:
        acc = alpaca.get_account()
        portfolio_val = float(acc.portfolio_value)
    except Exception as e:
        print(f"  [AUTO] Cannot get account: {e}")
        return False

    coin    = signal.get("coin", signal.get("ticker", "")).upper()
    action  = signal.get("action", "").lower()
    size_pct = signal.get("position_size_pct", 2)
    notional = min(portfolio_val * (size_pct / 100), RULES["max_notional_usd"])

    if asset_type == "crypto":
        symbol = ALPACA_CRYPTO_MAP.get(coin, f"{coin}USD")
        try:
            alpaca.submit_order(
                symbol=symbol,
                notional=round(notional, 2),
                side=action,
                type='market',
                time_in_force='gtc'
            )
            _log_auto_trade(signal, notional, symbol, "executed")
            state["daily_trades"] += 1
            state["total_auto_trades"] += 1
            print(f"  [AUTO] EXECUTED: {action.upper()} ${notional:.0f} {symbol}")
            return True
        except Exception as e:
            print(f"  [AUTO] FAILED: {e}")
            _log_auto_trade(signal, notional, symbol, f"failed: {e}")
            return False

    elif asset_type == "stock":
        ticker = coin
        qty    = signal.get("qty", 1)
        order_type = signal.get("order_type", "market")
        try:
            if order_type == "limit" and signal.get("limit_price"):
                alpaca.submit_order(
                    symbol=ticker, qty=qty, side=action,
                    type='limit', time_in_force='day',
                    limit_price=str(signal["limit_price"])
                )
            else:
                alpaca.submit_order(
                    symbol=ticker, qty=qty, side=action,
                    type='market', time_in_force='day'
                )
            _log_auto_trade(signal, notional, ticker, "executed")
            state["daily_trades"] += 1
            state["total_auto_trades"] += 1
            print(f"  [AUTO] EXECUTED: {action.upper()} {qty}x {ticker}")
            return True
        except Exception as e:
            print(f"  [AUTO] FAILED: {e}")
            _log_auto_trade(signal, notional, ticker, f"failed: {e}")
            return False

    return False

def _log_auto_trade(signal, notional, symbol, status):
    try:
        db.log_auto_trade(
            symbol=symbol,
            action=signal.get("action", ""),
            notional=notional,
            status=status,
            confidence=signal.get("confidence", 0),
            reasoning=signal.get("reasoning", ""),
            daily_count=state["daily_trades"],
        )
    except Exception as e:
        print(f"  [DB] log_auto_trade failed: {e}")
    # Local backup
    entry = {
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol, "notional": notional,
        "status": status, "daily_count": state["daily_trades"],
        **signal
    }
    with open(AUTO_LOG, 'a') as f:
        f.write(json.dumps(entry) + '\n')

# ── SIGNAL PROCESSOR ──────────────────────────────────
def _load_new_signals_db(last_crypto_ts: str, last_stock_ts: str) -> list[dict]:
    """
    Pull unprocessed signals from the database.
    Returns combined list of crypto + stock signals newer than the given timestamps.
    """
    signals = []

    # Crypto signals from DB
    try:
        rows = db.get_recent_crypto_signals(50)
        for row in rows:
            ts = row.get("timestamp", "")
            if ts > last_crypto_ts:
                row["_source_ts"]  = ts
                row["_asset_type"] = "crypto"
                row["coin"]        = row.get("coin", "")
                # Reconstruct entry_zone for compatibility
                row["entry_zone"]  = {"low": row.get("entry_low"), "high": row.get("entry_high")}
                row["take_profit_1"] = row.get("take_profit_1")
                signals.append(row)
    except Exception as e:
        print(f"  [DB] crypto signal load failed: {e}")
        # Fallback to file
        signals += _load_new_signals_file(SIGNAL_FILE, last_crypto_ts, "crypto")

    # Stock signals from DB
    try:
        rows = db.get_recent_trades(50)
        for row in rows:
            ts = row.get("timestamp", "")
            if ts > last_stock_ts:
                row["_source_ts"]  = ts
                row["_asset_type"] = "stock"
                signals.append(row)
    except Exception as e:
        print(f"  [DB] stock signal load failed: {e}")
        signals += _load_new_signals_file(STOCK_SIGNAL_FILE, last_stock_ts, "stock")

    return signals

def _load_new_signals_file(signal_file: str, last_processed: str, asset_type: str) -> list[dict]:
    """Fallback: read signal file and return entries newer than last_processed."""
    signals = []
    try:
        with open(signal_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    ts = entry.get("timestamp", "")
                    if ts > last_processed:
                        if "signals" in entry:
                            for sig in entry["signals"]:
                                sig["_source_ts"]  = ts
                                sig["_asset_type"] = asset_type
                                signals.append(sig)
                        else:
                            entry["_source_ts"]  = ts
                            entry["_asset_type"] = asset_type
                            signals.append(entry)
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        pass
    return signals

class AutoAcceptBot:
    def __init__(self):
        self.last_crypto_ts = ""
        self.last_stock_ts  = ""
        self.running        = False

    def process_signals(self):
        ok, reason = check_circuit_breakers()
        if not ok:
            print(f"\n[AUTO-BOT] Circuit breaker: {reason}")
            return

        all_signals = _load_new_signals_db(self.last_crypto_ts, self.last_stock_ts)

        if not all_signals:
            return

        print(f"\n[AUTO-BOT] {len(all_signals)} new signal(s) to evaluate")

        for signal in all_signals:
            asset_type = signal.get("_asset_type", "crypto")
            ts         = signal.get("_source_ts", "")

            # Update last processed timestamps
            if asset_type == "crypto" and ts > self.last_crypto_ts:
                self.last_crypto_ts = ts
            elif asset_type == "stock" and ts > self.last_stock_ts:
                self.last_stock_ts = ts

            coin = signal.get("coin", signal.get("ticker", "UNKNOWN")).upper()
            conf = signal.get("confidence", 0)

            print(f"\n  Evaluating: {signal.get('action','?').upper()} {coin}  {conf}%")

            # Step 1: Rule-based filter
            ok, reason = evaluate_signal(signal, asset_type)
            if not ok:
                print(f"  BLOCKED — {reason}")
                state["total_blocked"] += 1
                _log_auto_trade(signal, 0, coin, f"blocked: {reason}")
                continue

            # Step 2: AI second opinion (for larger trades)
            ai_ok, ai_reason = ai_second_opinion(signal)
            if not ai_ok:
                print(f"  BLOCKED (AI) — {ai_reason}")
                state["total_blocked"] += 1
                _log_auto_trade(signal, 0, coin, f"ai_blocked: {ai_reason}")
                continue

            print(f"  APPROVED — {ai_reason}")

            # Step 3: Execute
            execute_signal(signal, asset_type)

            # Check circuit breakers again after each trade
            ok, reason = check_circuit_breakers()
            if not ok:
                print(f"\n[AUTO-BOT] Circuit breaker triggered after trade: {reason}")
                break

    def monitor_exits(self):
        """Auto-exit positions that exceed max loss threshold."""
        try:
            positions = alpaca.list_positions()
        except Exception:
            return

        for pos in positions:
            pnl_pct = float(pos.unrealized_plpc)
            if pnl_pct <= -RULES["auto_exit_loss_pct"]:
                symbol = pos.symbol
                qty    = abs(float(pos.qty))
                print(f"\n[AUTO-BOT] EMERGENCY EXIT: {symbol} at {pnl_pct*100:.1f}%")
                try:
                    alpaca.submit_order(
                        symbol=symbol,
                        qty=int(qty),
                        side='sell',
                        type='market',
                        time_in_force='day'
                    )
                    _log_auto_trade(
                        {"action": "sell", "coin": symbol,
                         "reasoning": f"auto-exit: {pnl_pct*100:.1f}% loss", "confidence": 100},
                        0, symbol, "auto_exit_executed"
                    )
                except Exception as e:
                    print(f"  Exit failed: {e}")

    def print_status(self):
        daily_reset()
        update_daily_pnl()
        try:
            acc = alpaca.get_account()
            portfolio_val = float(acc.portfolio_value)
            positions     = alpaca.list_positions()
        except Exception:
            portfolio_val = 0
            positions     = []

        print(f"\n{'='*60}")
        print(f"  AUTO-BOT STATUS  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}")
        print(f"  Status         : {'PAUSED - ' + state['pause_reason'] if state['paused'] else 'RUNNING'}")
        print(f"  Portfolio      : ${portfolio_val:>12,.2f}")
        print(f"  Daily P&L      : {state['daily_pnl_pct']*100:>+.2f}%")
        print(f"  Trades today   : {state['daily_trades']}/{RULES['max_daily_trades']}")
        print(f"  Open positions : {len(positions)}/{RULES['max_concurrent_pos']}")
        print(f"  Total executed : {state['total_auto_trades']}")
        print(f"  Total blocked  : {state['total_blocked']}")
        print(f"{'='*60}")

    def run(self):
        self.running = True
        db.init_db()
        print("=" * 60)
        print("  AUTO ACCEPT BOT  —  ACTIVE")
        print("=" * 60)
        print(f"  Min confidence : {RULES['min_confidence']}%")
        print(f"  Max position   : {RULES['max_position_pct']*100:.0f}% / ${RULES['max_notional_usd']:.0f}")
        print(f"  Daily limit    : {RULES['max_daily_trades']} trades")
        print(f"  Loss circuit   : -{RULES['max_daily_loss_pct']*100:.0f}% daily")
        print(f"  Auto exit      : -{RULES['auto_exit_loss_pct']*100:.0f}% per position")
        print("=" * 60)

        daily_reset()

        # Initialize timestamps to "now" so we only pick up future signals
        self.last_crypto_ts = datetime.now().isoformat()
        self.last_stock_ts  = datetime.now().isoformat()

        schedule.every(1).minutes.do(self.process_signals)
        schedule.every(5).minutes.do(self.monitor_exits)
        schedule.every(15).minutes.do(self.print_status)
        schedule.every().day.at("00:01").do(daily_reset)

        self.print_status()
        print("\nWatching for signals — Ctrl+C to stop\n")

        while self.running:
            schedule.run_pending()
            time.sleep(15)

# ── MANUAL CONTROLS ───────────────────────────────────
def pause_bot(reason: str = "manual pause"):
    state["paused"]       = True
    state["pause_reason"] = reason
    print(f"[AUTO-BOT] Paused: {reason}")

def resume_bot():
    state["paused"]       = False
    state["pause_reason"] = ""
    print("[AUTO-BOT] Resumed")

def update_rules(**kwargs):
    """Dynamically update risk rules at runtime."""
    for key, value in kwargs.items():
        if key in RULES:
            old = RULES[key]
            RULES[key] = value
            print(f"[AUTO-BOT] Rule updated: {key} = {old} → {value}")
        else:
            print(f"[AUTO-BOT] Unknown rule: {key}")

# ── MAIN ──────────────────────────────────────────────
if __name__ == "__main__":
    bot = AutoAcceptBot()
    bot.run()
