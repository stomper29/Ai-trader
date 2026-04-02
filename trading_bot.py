"""
AI TRADING BOT — Enhanced Stock Trader
Strategies: Momentum | Mean Reversion | Macro Alignment
Risk: Max 2% per trade | Target: 20-30% annual growth
"""

import os
import json
import time
import schedule
from datetime import datetime, timedelta
import anthropic
import alpaca_trade_api as tradeapi

# ── KEYS ──────────────────────────────────────────────
ALPACA_KEY    = os.environ.get("ALPACA_KEY")
ALPACA_SECRET = os.environ.get("ALPACA_SECRET")
ALPACA_BASE   = os.environ.get("ALPACA_BASE", "https://paper-api.alpaca.markets")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_KEY")

TRADE_LOG     = "trade_log.json"
MAX_RISK_PCT  = 0.02   # 2% max risk per trade
MIN_CONFIDENCE = 70    # minimum AI confidence to execute
MAX_POSITION_PCT = 0.20  # max 20% of portfolio per position

# ── INIT ──────────────────────────────────────────────
alpaca = tradeapi.REST(ALPACA_KEY, ALPACA_SECRET, ALPACA_BASE)
claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

SYSTEM_PROMPT = """
You are an elite quantitative trading AI combining the best strategies of:
- Renaissance Technologies: statistical arbitrage, pattern recognition, signal processing
- Paul Tudor Jones: macro trend following, disciplined risk management, never average losers
- Warren Buffett: fundamental value, wide moat companies, margin of safety
- George Soros: macro momentum, reflexivity theory, regime change detection
- Jim Simons: mathematical edge, mean-reversion, quantitative signals

CORE STRATEGIES:
1. MOMENTUM: Buy assets trending strongly upward with high volume confirmation (>1.5x avg vol)
2. MEAN REVERSION: Buy oversold (RSI < 30) assets near strong support with catalyst
3. MACRO ALIGNMENT: Only trade in direction of macro trend; sit out in uncertainty
4. RISK FIRST: Never risk more than 1-2% of portfolio per trade; cut losers fast at -1%
5. PATTERN RECOGNITION: Identify high-probability setups: breakouts, wedges, cup-and-handle
6. EARNINGS EDGE: Trade momentum into earnings for companies with strong estimate revisions
7. SECTOR ROTATION: Follow institutional money flows between sectors

RISK RULES (NON-NEGOTIABLE):
- Maximum position size: 20% of portfolio
- Always set stop-loss at key technical level
- Take-profit at 2:1 minimum reward-to-risk
- Do NOT trade: first 30 minutes of market open, last 30 minutes before close
- Avoid: stocks with spread > 0.5%, low-volume stocks (<500k daily)

GOAL: Consistent 20-30% annual return through disciplined execution.
Win rate target: 55%+ with 2:1 R:R minimum.
"""

# ── ACCOUNT ───────────────────────────────────────────
def get_account():
    acc = alpaca.get_account()
    return {
        "balance":    float(acc.portfolio_value),
        "cash":       float(acc.cash),
        "buying_power": float(acc.buying_power),
        "day_trade_count": int(acc.daytrade_count),
    }

def get_positions():
    positions = alpaca.list_positions()
    return [{
        "symbol":    p.symbol,
        "qty":       float(p.qty),
        "avg_entry": float(p.avg_entry_price),
        "current":   float(p.current_price),
        "pnl_pct":   float(p.unrealized_plpc) * 100,
        "market_val": float(p.market_value),
    } for p in positions]

def get_open_orders():
    orders = alpaca.list_orders(status="open")
    return [{"id": o.id, "symbol": o.symbol, "side": o.side, "qty": float(o.qty)} for o in orders]

# ── SCAN & TRADE ───────────────────────────────────────
def scan_and_trade():
    now = datetime.now()
    print(f"\n{'='*60}")
    print(f"MARKET SCAN  {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    account   = get_account()
    positions = get_positions()
    orders    = get_open_orders()

    print(f"Portfolio : ${account['balance']:>12,.2f}")
    print(f"Cash      : ${account['cash']:>12,.2f}")
    print(f"Positions : {len(positions)} open")
    print(f"Orders    : {len(orders)} pending")

    max_position = account['balance'] * MAX_POSITION_PCT

    message = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""
CURRENT PORTFOLIO STATE:
- Portfolio value: ${account['balance']:,.2f}
- Available cash: ${account['cash']:,.2f}
- Buying power: ${account['buying_power']:,.2f}
- Open positions: {json.dumps(positions, indent=2)}
- Pending orders: {json.dumps(orders, indent=2)}

YOUR MISSION:
Search the market RIGHT NOW and find the best trades available.

SCAN FOR:
1. Top 3 momentum stocks with breakout + volume surge today (>1.5x avg volume)
2. Top 2 oversold stocks (RSI < 30) near strong support with reversal signal
3. Any earnings plays with strong estimate revisions in next 48 hours
4. Major macro events / Fed news affecting markets today
5. Any positions above that should be SOLD (stop-loss hit or take-profit reached)

CONSTRAINTS:
- Only stocks confidence >= {MIN_CONFIDENCE}%
- Max per position: ${max_position:,.2f} (20% portfolio)
- Do NOT buy stocks already in our open positions (unless adding to winner)
- Prefer liquid names: S&P 500 / Nasdaq 100 constituents

Return ONLY a valid JSON array. Nothing before or after it.
Each trade object:
{{
  "action": "buy" | "sell",
  "ticker": "SYMBOL",
  "qty": <integer shares>,
  "order_type": "market" | "limit",
  "limit_price": <float or null>,
  "stop_loss": <float>,
  "take_profit": <float>,
  "strategy": "momentum" | "mean_reversion" | "earnings" | "macro" | "exit",
  "reasoning": "<concise reason, max 100 chars>",
  "confidence": <integer 0-100>
}}

Return JSON array only.
"""
        }]
    )

    response_text = ""
    for block in message.content:
        if hasattr(block, "text"):
            response_text += block.text

    try:
        start = response_text.find('[')
        end   = response_text.rfind(']') + 1
        if start >= 0 and end > start:
            trades = json.loads(response_text[start:end])
            execute_trades(trades, account)
        else:
            print("No valid trade signals returned.")
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw response: {response_text[:300]}")

# ── EXECUTE ────────────────────────────────────────────
def execute_trades(trades, account):
    if not trades:
        print("No trades to execute.")
        return

    executed = 0
    for trade in trades:
        ticker = trade.get('ticker', '').upper()
        action = trade.get('action', '').lower()
        qty    = int(trade.get('qty', 0))
        conf   = trade.get('confidence', 0)
        strat  = trade.get('strategy', 'unknown')

        if not ticker or not action or qty <= 0:
            continue
        if conf < MIN_CONFIDENCE:
            print(f"  SKIP {ticker} — confidence {conf}% below threshold")
            continue

        cost_est = qty * (trade.get('limit_price') or 0)
        if action == 'buy' and cost_est > account['cash']:
            print(f"  SKIP {ticker} — insufficient cash")
            continue

        print(f"\n  {action.upper()} {qty}x {ticker}  [{strat}]  {conf}% conf")
        print(f"  Reason: {trade.get('reasoning','')[:80]}")
        if trade.get('stop_loss'):
            print(f"  SL: ${trade['stop_loss']:.2f}  TP: ${trade.get('take_profit',0):.2f}")

        try:
            if trade['order_type'] == 'limit' and trade.get('limit_price'):
                alpaca.submit_order(
                    symbol=ticker, qty=qty, side=action,
                    type='limit', time_in_force='day',
                    limit_price=str(trade['limit_price'])
                )
            else:
                alpaca.submit_order(
                    symbol=ticker, qty=qty, side=action,
                    type='market', time_in_force='day'
                )
            log_trade(trade)
            print(f"  OK — order submitted")
            executed += 1
        except Exception as e:
            print(f"  FAIL — {e}")

    print(f"\nExecuted {executed}/{len(trades)} trades")

# ── STOP LOSS MONITOR ─────────────────────────────────
def monitor_stops():
    """Check open positions and exit if stop-loss or take-profit hit."""
    positions = get_positions()
    for pos in positions:
        if pos['pnl_pct'] <= -2.0:
            print(f"STOP LOSS: {pos['symbol']} at {pos['pnl_pct']:.1f}% — exiting")
            try:
                alpaca.submit_order(
                    symbol=pos['symbol'],
                    qty=int(pos['qty']),
                    side='sell',
                    type='market',
                    time_in_force='day'
                )
                log_trade({
                    "action": "sell", "ticker": pos['symbol'],
                    "qty": pos['qty'], "strategy": "stop_loss",
                    "reasoning": f"Stop loss at {pos['pnl_pct']:.1f}%",
                    "confidence": 100
                })
            except Exception as e:
                print(f"  Stop loss order failed: {e}")

# ── LOGGING ────────────────────────────────────────────
def log_trade(trade):
    entry = {"timestamp": datetime.now().isoformat(), **trade}
    with open(TRADE_LOG, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def load_recent_trades(n=30):
    try:
        with open(TRADE_LOG, 'r') as f:
            lines = f.readlines()
        return [json.loads(l) for l in lines[-n:] if l.strip()]
    except Exception:
        return []

# ── DAILY LEARNING ────────────────────────────────────
def daily_learning():
    print(f"\n{'='*60}")
    print("DAILY LEARNING CYCLE")
    print(f"{'='*60}")

    recent = load_recent_trades(30)
    if not recent:
        print("No trade history to analyze.")
        return

    account = get_account()

    message = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""
PERFORMANCE REVIEW — {datetime.now().strftime('%Y-%m-%d')}

Recent trades (last 30):
{json.dumps(recent, indent=2)}

Portfolio value: ${account['balance']:,.2f}

TASKS:
1. Calculate: win rate, avg win %, avg loss %, profit factor
2. Identify: which strategy performed best/worst
3. Search web: current market regime, sector rotation, upcoming catalysts
4. Search: any stocks on our watchlist with upcoming earnings this week
5. Recommend: strategy adjustments for next 5 trading days

Return JSON:
{{
  "winRate": <float 0-1>,
  "profitFactor": <float>,
  "bestStrategy": "<name>",
  "worstStrategy": "<name>",
  "marketRegime": "<bull/bear/sideways/volatile>",
  "topSectors": ["<sector1>", "<sector2>"],
  "adjustments": ["<action1>", "<action2>"],
  "watchlist": ["TICK1", "TICK2", "TICK3"],
  "summary": "<2 sentence analysis>"
}}
"""
        }]
    )

    for block in message.content:
        if hasattr(block, "text") and block.text:
            print(block.text[:500])
            try:
                data = json.loads(block.text)
                with open("daily_report.json", 'a') as f:
                    entry = {"date": datetime.now().date().isoformat(), **data}
                    f.write(json.dumps(entry) + '\n')
            except Exception:
                pass

# ── MAIN ──────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  AI STOCK TRADING BOT  —  ACTIVE")
    print("=" * 60)
    print(f"  Strategy : Momentum + Mean Reversion + Macro")
    print(f"  Risk     : Max {MAX_RISK_PCT*100:.0f}% per trade")
    print(f"  Min Conf : {MIN_CONFIDENCE}%")
    print(f"  Target   : 20-30% annual return")
    print(f"  Exchange : Alpaca ({'Paper' if 'paper' in ALPACA_BASE else 'Live'})")
    print("=" * 60)

    # Run immediately on start
    scan_and_trade()

    # Schedule recurring tasks
    schedule.every(15).minutes.do(scan_and_trade)
    schedule.every(5).minutes.do(monitor_stops)
    schedule.every().day.at("18:00").do(daily_learning)

    print("\nScheduler running — Ctrl+C to stop")
    while True:
        schedule.run_pending()
        time.sleep(30)
