import os
import anthropic
import alpaca_trade_api as tradeapi
import schedule
import time
import json
from datetime import datetime

# ── KEYS (pulled privately from Railway environment) ──
ALPACA_KEY    = os.environ.get("ALPACA_KEY")
ALPACA_SECRET = os.environ.get("ALPACA_SECRET")
ALPACA_BASE   = "https://paper-api.alpaca.markets"
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_KEY")

# ── INIT ─────────────────────────────────────────────
alpaca = tradeapi.REST(ALPACA_KEY, ALPACA_SECRET, ALPACA_BASE)
claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

SYSTEM_PROMPT = """
You are an elite quantitative trading AI trained on the strategies of:
- Renaissance Technologies (statistical arbitrage, pattern recognition)
- Paul Tudor Jones (macro trend following, risk management)
- Warren Buffett (fundamental value identification)
- George Soros (macro momentum and reflexivity)

Your core strategies:
1. MOMENTUM: Buy assets trending strongly upward with volume confirmation
2. MEAN REVERSION: Buy oversold assets (RSI < 30) near support levels
3. MACRO ALIGNMENT: Only trade with the macro trend
4. RISK FIRST: Never risk more than 1-2% of portfolio per trade
5. PATTERN RECOGNITION: Find repeating statistical patterns

GOAL: Grow portfolio 20-30% annually through consistent small wins.
Win 55% of trades with 2:1 reward-to-risk ratio minimum.
"""

def get_account():
    account = alpaca.get_account()
    return {
        "balance": float(account.portfolio_value),
        "cash": float(account.cash),
    }

def scan_and_trade():
    print(f"\nSCAN: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    account = get_account()
    print(f"Portfolio: ${account['balance']:,.2f}")

    message = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""
            Portfolio: ${account['balance']}
            Cash available: ${account['cash']}

            Scan the market RIGHT NOW. Find:
            1. Top 3 momentum stocks breaking out with volume today
            2. Top 2 oversold stocks RSI < 30 near support
            3. Any major macro events affecting markets today

            Return ONLY a JSON array:
            [{{
                "action": "buy",
                "ticker": "AAPL",
                "qty": 1,
                "order_type": "market",
                "limit_price": null,
                "reasoning": "why this trade",
                "stop_loss": 145.00,
                "take_profit": 160.00,
                "confidence": 75
            }}]

            Only include trades with confidence >= 70.
            Max position: 20% of portfolio = ${account['balance'] * 0.20:.2f}
            Return JSON array only, nothing else.
            """
        }]
    )

    response_text = ""
    for block in message.content:
        if block.type == "text":
            response_text += block.text

    try:
        start = response_text.find('[')
        end = response_text.rfind(']') + 1
        if start >= 0 and end > start:
            trades = json.loads(response_text[start:end])
            execute_trades(trades)
    except Exception as e:
        print(f"Error: {e}")

def execute_trades(trades):
    for trade in trades:
        try:
            ticker  = trade['ticker']
            action  = trade['action']
            qty     = trade['qty']
            conf    = trade.get('confidence', 0)

            print(f"→ {action.upper()} {qty} {ticker} | {conf}% confidence")
            print(f"  {trade.get('reasoning','')[:80]}")

            if trade['order_type'] == 'limit' and trade.get('limit_price'):
                alpaca.submit_order(
                    symbol=ticker, qty=qty, side=action,
                    type='limit', time_in_force='day',
                    limit_price=trade['limit_price']
                )
            else:
                alpaca.submit_order(
                    symbol=ticker, qty=qty, side=action,
                    type='market', time_in_force='day'
                )

            log_trade(trade)
            print(f"  ✓ Order submitted")

        except Exception as e:
            print(f"  ✗ Failed: {e}")

def log_trade(trade):
    with open('trade_log.json', 'a') as f:
        entry = {"timestamp": datetime.now().isoformat(), **trade}
        f.write(json.dumps(entry) + '\n')

def daily_learning():
    print("\n📚 Daily learning cycle...")
    try:
        with open('trade_log.json', 'r') as f:
            recent = f.readlines()[-20:]
    except:
        recent = []

    if recent:
        message = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"""
                Review these trades: {' '.join(recent)}
                Search for: latest market conditions, sector rotations,
                upcoming earnings catalysts.
                What should we adjust in our strategy?
                Return JSON: {{
                    "winRate": 0.0,
                    "bestStrategy": "",
                    "marketRegime": "",
                    "adjustments": [],
                    "watchlist": []
                }}
                """
            }]
        )
        for block in message.content:
            if block.type == "text":
                print(block.text[:300])

# ── SCHEDULE ─────────────────────────────────────────
schedule.every(15).minutes.do(scan_and_trade)
schedule.every().day.at("18:00").do(daily_learning)

print("🤖 AI TRADER RUNNING")
print("Strategy: Momentum + Mean Reversion")
print("Risk: Max 2% per trade")
print("Target: 20-30% annually\n")

scan_and_trade()

while True:
    schedule.run_pending()
    time.sleep(60)
