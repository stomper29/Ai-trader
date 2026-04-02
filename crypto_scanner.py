"""
AI CRYPTO SCANNER
Scans BTC, ETH, and top altcoins for high-probability trading setups.
Uses Claude AI with web search for real-time on-chain and price analysis.
Integrates with Alpaca Crypto trading (or outputs signals for manual/auto execution).
"""

import os
import json
import time
import schedule
from datetime import datetime
import anthropic
import db

# ── KEYS ──────────────────────────────────────────────
ANTHROPIC_KEY  = os.environ.get("ANTHROPIC_KEY")
ALPACA_KEY     = os.environ.get("ALPACA_KEY")
ALPACA_SECRET  = os.environ.get("ALPACA_SECRET")
ALPACA_BASE    = os.environ.get("ALPACA_BASE", "https://paper-api.alpaca.markets")

SIGNAL_FILE    = "crypto_signals.json"
MIN_CONFIDENCE = 68

claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

# Optional Alpaca crypto trading
try:
    import alpaca_trade_api as tradeapi
    alpaca = tradeapi.REST(ALPACA_KEY, ALPACA_SECRET, ALPACA_BASE)
    ALPACA_AVAILABLE = True
except Exception:
    alpaca = None
    ALPACA_AVAILABLE = False

# ── SYSTEM PROMPT ─────────────────────────────────────
CRYPTO_SYSTEM = """
You are an elite crypto market analyst and trader combining expertise from:
- Willy Woo (on-chain analytics: NVT, SOPR, MVRV, exchange flows)
- PlanB (stock-to-flow model, cycle analysis)
- Arthur Hayes (macro-crypto correlation, liquidity cycles)
- Raoul Pal (institutional crypto adoption, macro framework)
- Michael Saylor (Bitcoin fundamentals, long-term accumulation)
- Top DeFi analysts (DEX volume, TVL trends, protocol revenue)

CRYPTO ANALYSIS FRAMEWORK:
1. ON-CHAIN METRICS:
   - Exchange inflows/outflows (high outflows = accumulation = bullish)
   - MVRV ratio (>3.5 = overvalued, <1 = undervalued)
   - NVT ratio (high = overvalued relative to transaction volume)
   - Whale wallet movements (>1000 BTC wallets)
   - Miner behavior (capitulation or accumulation)

2. TECHNICAL ANALYSIS:
   - Bitcoin dominance trend (rising = altcoin weakness, falling = alt season)
   - Funding rates on perpetual futures (>0.1% = overheated longs)
   - Open interest changes (surging OI + price up = strong trend)
   - Fear & Greed Index (< 20 = extreme fear = buy zone, > 80 = extreme greed = be cautious)
   - Key support/resistance levels on weekly/daily charts
   - Volume profile (high-volume nodes = strong support/resistance)

3. MACRO FACTORS:
   - DXY correlation (strong dollar = crypto headwind)
   - Fed policy impact on risk assets
   - Institutional flows (ETF inflows/outflows for BTC/ETH)
   - Regulatory news globally
   - Correlation with Nasdaq/S&P 500

4. ALTCOIN SIGNALS:
   - BTC dominance breakdowns = altcoin season triggers
   - Layer-1 competitor metrics (TVL, daily active users, revenue)
   - DeFi protocol launches and upgrades
   - NFT market sentiment as risk appetite indicator
   - New exchange listings (short-term pump potential)

5. RISK MANAGEMENT FOR CRYPTO:
   - Higher volatility = smaller position sizes (max 5-10% portfolio in single coin)
   - Use wider stops due to crypto volatility (5-15%)
   - Scale in/out rather than single entry/exit
   - Never invest more than you can afford to lose in alts
   - Bitcoin first — it's the base layer and safest crypto asset

CRYPTO UNIVERSE TO MONITOR:
- Large caps: BTC, ETH, BNB, SOL, XRP, ADA, AVAX, DOT
- DeFi: UNI, AAVE, COMP, CRV, MKR, SNX
- Layer 2: MATIC, ARB, OP, IMX
- Infrastructure: LINK, GRT, FIL, RENDER
- Emerging: Monitor top 50 by market cap for breakouts

SIGNAL QUALITY TIERS:
- Tier 1 (85-100%): Multiple confluent signals, strong on-chain + technical alignment
- Tier 2 (70-84%): Good technical setup with on-chain support
- Tier 3 (60-69%): Speculative, smaller position size recommended

OUTPUT RULES:
- Confidence >= 68 for any signal to be worth acting on
- Always specify entry zone, not just single price
- Always specify invalidation level (where the thesis is wrong)
- Mention the primary catalyst driving the signal
"""

# ── SCAN FUNCTION ─────────────────────────────────────
def run_crypto_scan(scan_type="full"):
    now = datetime.now()
    print(f"\n{'='*60}")
    print(f"CRYPTO SCAN [{scan_type.upper()}]  {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    if scan_type == "full":
        prompt = _full_scan_prompt()
    elif scan_type == "quick":
        prompt = _quick_scan_prompt()
    elif scan_type == "altseason":
        prompt = _altseason_prompt()
    else:
        prompt = _full_scan_prompt()

    message = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        system=CRYPTO_SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = ""
    for block in message.content:
        if hasattr(block, "text"):
            response_text += block.text

    signals = _parse_signals(response_text)
    if signals:
        _display_signals(signals)
        _save_signals(signals, scan_type)
        if ALPACA_AVAILABLE:
            _execute_crypto_signals(signals)
    else:
        print("No valid signals parsed from response.")
        print(f"Raw (first 400 chars): {response_text[:400]}")

    return signals

# ── PROMPTS ───────────────────────────────────────────
def _full_scan_prompt():
    return f"""
FULL CRYPTO MARKET SCAN — {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}

Search the web for the most current crypto market data and perform a complete analysis.

STEP 1 — MARKET REGIME:
Search for: current Bitcoin price, Bitcoin dominance %, Fear & Greed Index,
total crypto market cap, BTC ETF inflows today.

STEP 2 — ON-CHAIN HEALTH:
Search for: Bitcoin exchange net flows today, MVRV ratio current,
ETH staking APY, largest whale transactions last 24h.

STEP 3 — TOP OPPORTUNITIES:
Identify the 5 best crypto trading opportunities RIGHT NOW based on:
- Technical breakouts with volume confirmation
- Oversold conditions with reversal signals
- Major catalyst (upgrade, partnership, exchange listing)
- On-chain accumulation signal

STEP 4 — MACRO CONTEXT:
Search for: DXY today, 10-year treasury yield, S&P 500 today,
any Fed statements or regulatory crypto news.

Return ONLY a JSON object with this exact structure:
{{
  "market_regime": {{
    "btc_dominance": <float>,
    "fear_greed": <integer 0-100>,
    "phase": "accumulation|markup|distribution|markdown",
    "trend": "bull|bear|sideways",
    "summary": "<2 sentences>"
  }},
  "signals": [
    {{
      "coin": "BTC",
      "pair": "BTC/USD",
      "action": "buy|sell|watch",
      "timeframe": "scalp(1-4h)|swing(1-7d)|position(1-4wk)",
      "entry_zone": {{"low": <float>, "high": <float>}},
      "stop_loss": <float>,
      "take_profit_1": <float>,
      "take_profit_2": <float>,
      "take_profit_3": <float>,
      "position_size_pct": <float 1-10>,
      "catalyst": "<primary reason>",
      "on_chain_signal": "<relevant metric>",
      "invalidation": "<what would make this wrong>",
      "confidence": <integer 0-100>,
      "tier": 1|2|3,
      "reasoning": "<detailed analysis max 200 chars>"
    }}
  ],
  "watchlist": ["COIN1", "COIN2", "COIN3"],
  "avoid": ["COIN1"],
  "macro_notes": "<macro context>",
  "altseason_probability": <float 0-1>,
  "btc_price": <float>,
  "eth_price": <float>
}}
"""

def _quick_scan_prompt():
    return f"""
QUICK CRYPTO SCAN — {datetime.now().strftime('%H:%M UTC')}

Search for: current BTC price, ETH price, any major crypto moves in last 1 hour,
any liquidation events, funding rate extremes.

Return top 3 immediate opportunities ONLY as JSON array:
[{{
  "coin": "BTC",
  "pair": "BTC/USD",
  "action": "buy|sell|watch",
  "timeframe": "scalp(1-4h)",
  "entry_zone": {{"low": <float>, "high": <float>}},
  "stop_loss": <float>,
  "take_profit_1": <float>,
  "take_profit_2": <float>,
  "take_profit_3": <float>,
  "position_size_pct": <float 1-5>,
  "catalyst": "<reason>",
  "on_chain_signal": "n/a",
  "invalidation": "<what breaks thesis>",
  "confidence": <integer>,
  "tier": 1|2|3,
  "reasoning": "<max 100 chars>"
}}]
"""

def _altseason_prompt():
    return f"""
ALTCOIN SEASON ANALYSIS — {datetime.now().strftime('%Y-%m-%d')}

Search for: Bitcoin dominance trend, Ethereum vs Bitcoin ratio (ETH/BTC),
total2 market cap (excluding BTC), altcoin season index,
top performing altcoins this week.

Identify the TOP 5 altcoins most likely to outperform over next 2-4 weeks.
Focus on coins with: rising fundamentals, accumulation on-chain, upcoming catalysts.

Return JSON array of signals (same format as full scan signals array).
"""

# ── PARSING ───────────────────────────────────────────
def _parse_signals(text):
    signals = []

    # Try full scan format first (nested under "signals" key)
    obj_start = text.find('{')
    obj_end   = text.rfind('}') + 1
    if obj_start >= 0 and obj_end > obj_start:
        try:
            data = json.loads(text[obj_start:obj_end])
            if "signals" in data:
                signals = data["signals"]
                # Store full market context
                _save_market_context(data)
            elif isinstance(data, list):
                signals = data
        except json.JSONDecodeError:
            pass

    # Fallback: try array format
    if not signals:
        arr_start = text.find('[')
        arr_end   = text.rfind(']') + 1
        if arr_start >= 0 and arr_end > arr_start:
            try:
                signals = json.loads(text[arr_start:arr_end])
            except json.JSONDecodeError:
                pass

    return [s for s in signals if s.get('confidence', 0) >= MIN_CONFIDENCE]

def _save_market_context(data):
    try:
        db.save_market_context(data)
    except Exception as e:
        print(f"  [DB] save_market_context failed: {e}")

def _display_signals(signals):
    print(f"\n  {len(signals)} SIGNAL(S) FOUND:")
    print(f"  {'─'*56}")
    for s in signals:
        action_str = s.get('action','?').upper()
        coin       = s.get('coin', s.get('pair','?'))
        tf         = s.get('timeframe','?')
        conf       = s.get('confidence',0)
        tier       = s.get('tier','?')
        ez         = s.get('entry_zone', {})
        sl         = s.get('stop_loss',0)
        tp1        = s.get('take_profit_1',0)
        catalyst   = s.get('catalyst','')[:60]
        reasoning  = s.get('reasoning','')[:80]

        print(f"\n  [{action_str}] {coin}  T{tier}  {conf}%  [{tf}]")
        if isinstance(ez, dict):
            print(f"  Entry : ${ez.get('low',0):,.2f} – ${ez.get('high',0):,.2f}")
        print(f"  SL    : ${sl:,.2f}   TP1: ${tp1:,.2f}")
        if s.get('take_profit_2'):
            print(f"  TP2   : ${s['take_profit_2']:,.2f}  TP3: ${s.get('take_profit_3',0):,.2f}")
        print(f"  Size  : {s.get('position_size_pct',1):.1f}% of portfolio")
        print(f"  Basis : {catalyst}")
        if reasoning:
            print(f"  Note  : {reasoning}")

    print(f"\n  {'─'*56}")

def _save_signals(signals, scan_type):
    # Save each signal to DB
    saved = 0
    for sig in signals:
        try:
            db.log_crypto_signal(sig, scan_type)
            saved += 1
        except Exception as e:
            print(f"  [DB] log_crypto_signal failed: {e}")
    # Also write to local file as backup
    entry = {
        "timestamp": datetime.now().isoformat(),
        "scan_type": scan_type,
        "count": len(signals),
        "signals": signals
    }
    with open(SIGNAL_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')
    print(f"\n  {saved}/{len(signals)} signals saved to DB + {SIGNAL_FILE}")

# ── EXECUTION (ALPACA CRYPTO) ─────────────────────────
def _execute_crypto_signals(signals):
    """Execute crypto signals via Alpaca (supports BTC/USD, ETH/USD, etc.)"""
    if not alpaca:
        return

    ALPACA_CRYPTO_PAIRS = {
        "BTC": "BTCUSD", "ETH": "ETHUSD", "LTC": "LTCUSD",
        "BCH": "BCHUSD", "LINK": "LINKUSD", "UNI": "UNIUSD",
        "AAVE": "AAVEUSD", "SOL": "SOLUSD", "AVAX": "AVAXUSD",
    }

    try:
        acc = alpaca.get_account()
        portfolio_val = float(acc.portfolio_value)
        cash = float(acc.cash)
    except Exception as e:
        print(f"  Could not get account: {e}")
        return

    for sig in signals:
        if sig.get('action') not in ('buy', 'sell'):
            continue

        coin = sig.get('coin', '').upper()
        alpaca_pair = ALPACA_CRYPTO_PAIRS.get(coin)
        if not alpaca_pair:
            print(f"  {coin} not available on Alpaca crypto — skipping")
            continue

        size_pct    = sig.get('position_size_pct', 2) / 100
        position_usd = portfolio_val * size_pct
        entry_mid    = 0
        ez = sig.get('entry_zone', {})
        if isinstance(ez, dict) and ez.get('low') and ez.get('high'):
            entry_mid = (ez['low'] + ez['high']) / 2

        if position_usd > cash and sig['action'] == 'buy':
            print(f"  {coin}: insufficient cash (need ${position_usd:.0f}, have ${cash:.0f})")
            continue

        notional = round(position_usd, 2)

        print(f"\n  CRYPTO EXECUTE: {sig['action'].upper()} ${notional:.2f} of {alpaca_pair}")
        try:
            alpaca.submit_order(
                symbol=alpaca_pair,
                notional=notional,
                side=sig['action'],
                type='market',
                time_in_force='gtc'
            )
            _log_crypto_trade(sig, notional, alpaca_pair)
            print(f"  OK — order submitted")
        except Exception as e:
            print(f"  FAIL — {e}")

def _log_crypto_trade(signal, notional_usd, alpaca_pair):
    try:
        trade = {**signal, "ticker": alpaca_pair, "qty": notional_usd,
                 "order_type": "market", "strategy": "crypto_execution"}
        db.log_trade(trade)
    except Exception as e:
        print(f"  [DB] _log_crypto_trade failed: {e}")

# ── ALTSEASON MONITOR ─────────────────────────────────
def altseason_check():
    """Dedicated altseason analysis — run once daily."""
    print(f"\n{'='*60}")
    print("ALTCOIN SEASON MONITOR")
    print(f"{'='*60}")
    run_crypto_scan("altseason")

# ── MAIN ──────────────────────────────────────────────
if __name__ == "__main__":
    db.init_db()
    print("=" * 60)
    print("  AI CRYPTO SCANNER  —  ACTIVE")
    print("=" * 60)
    print(f"  Coverage  : BTC, ETH + Top 50 Altcoins")
    print(f"  Signals   : On-chain + Technical + Macro")
    print(f"  Min Conf  : {MIN_CONFIDENCE}%")
    print(f"  Execution : {'Alpaca Crypto' if ALPACA_AVAILABLE else 'Signal-only mode'}")
    print("=" * 60)

    # Immediate full scan on start
    run_crypto_scan("full")

    # Schedule
    schedule.every(30).minutes.do(run_crypto_scan, scan_type="quick")
    schedule.every(4).hours.do(run_crypto_scan, scan_type="full")
    schedule.every().day.at("07:00").do(altseason_check)
    schedule.every().day.at("20:00").do(run_crypto_scan, scan_type="full")

    print("\nScheduler running — Ctrl+C to stop")
    while True:
        schedule.run_pending()
        time.sleep(60)
