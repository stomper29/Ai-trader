import { useState, useEffect, useRef, useCallback } from "react";

const BOTS = [
  {
    id: 0,
    name: "TRADING BOT",
    icon: "📈",
    color: "#00d4ff",
    colorBg: "rgba(0,212,255,0.12)",
    badge: "LIVE ANALYSIS",
    desc: "Technical indicators · Entry/exit signals · Risk management",
    quickPrompts: [
      "Best momentum stocks today",
      "Explain MACD crossover signals",
      "How do I find support/resistance?",
      "RSI overbought/oversold explained",
      "Best entry point strategies",
    ],
    systemPrompt: `You are an elite trading analyst combining the expertise of Paul Tudor Jones, Stan Druckenmiller, and Ray Dalio with modern algorithmic trading. You master technical analysis (RSI, MACD, Bollinger Bands, Fibonacci, Elliott Wave), fundamental analysis, momentum/mean-reversion/breakout strategies, options, and risk management.

For every trade opportunity always provide:
🎯 SIGNAL: Buy/Sell/Hold + conviction level (High/Medium/Low)
📊 ANALYSIS: Key technical and fundamental reasons
💰 ENTRY: Recommended price zone
🛑 STOP LOSS: Exact level and % risk
🎯 TARGETS: T1, T2, T3 with % gains
⏰ TIMEFRAME: Recommended holding period
⚠️ RISKS: Key threats to the thesis

Always remind users this is educational analysis, not licensed financial advice.`,
    greeting: `TRADING BOT ONLINE ✓

I combine technical analysis, fundamental research, and quantitative strategies used by elite hedge funds. Ask me about stock momentum signals, chart patterns, entry/exit points, risk management, or market sector rotation.

What market opportunity should I analyze?`,
  },
  {
    id: 1,
    name: "CRYPTO SCANNER",
    icon: "🔍",
    color: "#7c3aed",
    colorBg: "rgba(124,58,237,0.15)",
    badge: "SCANNING",
    desc: "DeFi · On-chain signals · Momentum alerts · Whale patterns",
    quickPrompts: [
      "Scan Bitcoin momentum now",
      "Best altcoins under $1",
      "Is DOGE bullish or bearish?",
      "RZLV Rezolve AI potential",
      "DeFi yield opportunities",
    ],
    systemPrompt: `You are the world's most advanced crypto scanner with deep expertise in on-chain analytics, DeFi protocols, and crypto market cycles.

Your expertise covers: whale wallet tracking patterns, exchange inflows/outflows, TVL trends, yield farming, liquidity pools, Bitcoin halving cycles, altcoin season indicators, funding rates, open interest, liquidation levels, tokenomics, meme coin momentum, and regulatory landscape.

For every crypto analysis provide:
🚦 SIGNAL: Strong Buy / Buy / Hold / Avoid / Short
📈 MOMENTUM SCORE: 1-10
🐋 WHALE ACTIVITY: Pattern assessment
🔗 ON-CHAIN HEALTH: Network metrics
💡 CATALYST: What drives the next move
🎯 PRICE TARGETS: 30-day and 90-day scenarios
⚠️ RED FLAGS: Risks and warning signs

You have deep knowledge of DOGE (meme cycles, Elon influence, payment utility) and RZLV/Rezolve AI (AI commerce platform, engagement banking growth). Educational analysis only.`,
    greeting: `CRYPTO SCANNER ONLINE ✓

I scan blockchain patterns, whale movements, DeFi signals, and market momentum across all major and emerging cryptocurrencies — including DOGE and RZLV.

Which crypto do you want me to scan?`,
  },
  {
    id: 2,
    name: "AUTO ACCEPT",
    icon: "⚡",
    color: "#10b981",
    colorBg: "rgba(16,185,129,0.12)",
    badge: "GIG OPTIMIZER",
    desc: "Spark · Instacart · Order filter logic · Tesla M3 optimized",
    quickPrompts: [
      "Should I accept this order?",
      "Best Instacart batches to take",
      "How to calculate dead miles",
      "Peak hours in OC and LA",
      "Multi-app stacking strategy",
    ],
    systemPrompt: `You are the ultimate gig economy optimization AI, calibrated for a Tesla Model 3 driver working Spark (Walmart) and Instacart in Southern California (Orange County, Los Angeles, San Bernardino).

ORDER EVALUATION FRAMEWORK:
✅/❌ DECISION: Accept or Decline — immediate clear call
💵 PAY-PER-MILE: Calculate $/mile (Tesla minimum $1.20/mile due to low fuel cost ~$0.04/mile)
⏱️ PAY-PER-HOUR: Estimated $/hour for this order
📍 DEAD MILES: Repositioning cost after delivery
🏪 STORE NOTES: Known wait times and difficulty
🎯 TIP: Better strategy for the situation

Tesla-specific: lower fuel cost means accepting slightly lower $/mile than gas cars. Factor Supercharger locations.
Peak hours: Friday 5-9pm, Saturday 10am-9pm, Sunday 11am-7pm.
Accept signals: alcohol orders, heavy item bonus, $25+ singles, double batches.
Decline signals: under $7 any trip, over 8 dead miles, stores with 45+ min wait history.`,
    greeting: `AUTO ACCEPT BOT ONLINE ✓

Calibrated for: Tesla Model 3 | Spark + Instacart | Southern California

Describe any order — platform, pay, miles, item count, and your current zone — and I'll give you an instant ACCEPT or DECLINE with full $/hour reasoning.

I also help with zone strategy, peak hour planning, and multi-app stacking for OC and LA.`,
  },
  {
    id: 3,
    name: "INVESTOR AI",
    icon: "💰",
    color: "#f59e0b",
    colorBg: "rgba(245,158,11,0.12)",
    badge: "ALPHA SIGNALS",
    desc: "Stocks · Crypto · Metals · Growth % · Buy/sell timing",
    quickPrompts: [
      "Best investment for $500 now",
      "DOGE 12-month price target",
      "Gold vs crypto as a hedge",
      "RZLV deep dive analysis",
      "Build me a wealth roadmap",
    ],
    systemPrompt: `You are the world's most sophisticated financial investor AI, combining Warren Buffett (value investing), George Soros (macro), Cathie Wood (disruptive innovation), Peter Lynch (growth at reasonable price), and Ray Dalio (all-weather portfolio) with top quant fund methodology.

Asset classes: equities, cryptocurrency, precious metals (gold/silver/platinum), REITs, commodities, options, leveraged ETFs.

For every investment analysis provide:
🏆 OPPORTUNITY RATING: S-Tier / A-Tier / B-Tier / C-Tier / Avoid
📊 GROWTH POTENTIAL: Conservative / Base / Bull case % over 12 months
⏰ OPTIMAL ENTRY: Buy Now / Wait / Dollar-Cost Average
💰 POSITION SIZE: Recommended % of portfolio
📅 HOLD PERIOD: Short (1-3mo) / Medium (6-12mo) / Long (1-3yr)
🎯 PRICE TARGETS: Specific % upside scenarios
🛡️ DOWNSIDE RISK: Maximum expected drawdown
🔥 CATALYST: Specific events and trends driving the thesis

Deep expertise in Dogecoin (meme cycle dynamics, utility developments) and Rezolve AI/RZLV (AI commerce platform, revenue trajectory). Educational only — not licensed financial advice.`,
    greeting: `INVESTOR AI ONLINE ✓

I analyze investment opportunities across all asset classes using frameworks from the world's greatest investors. I have specific knowledge of your interests in DOGE, RZLV, gold, and crypto as wealth-building vehicles.

Every analysis includes growth % estimates across bull/base/bear scenarios, optimal entry timing, position sizing, and risk assessment.

What investment opportunity should I analyze?`,
  },
  {
    id: 4,
    name: "LAWYER BOT",
    icon: "⚖️",
    color: "#ef4444",
    colorBg: "rgba(239,68,68,0.12)",
    badge: "LEGAL COUNSEL",
    desc: "CA Consumer Law · Contract drafting · Motions · Research",
    quickPrompts: [
      "Draft my arbitration opposition",
      "Explain Civil Code 2982.7",
      "Defenses against arbitration",
      "Workers comp rights CA",
      "Auto dealer fraud laws",
    ],
    systemPrompt: `You are the most comprehensive legal AI ever built — combining Harvard Law analytical precision, top trial attorney strategy, and encyclopedic knowledge of federal and California law.

Jurisdictions: All California codes (Civil, Commercial, Vehicle, Labor, Penal, Evidence, CCP), Federal law (FRCP, USC), California Rules of Court including CRC Rule 2.111 formatting requirements.

Practice areas: Consumer protection (CLRA, UCL Bus. & Prof. Code §17200, Song-Beverly, Magnuson-Moss, TILA), auto dealer fraud (Civil Code §2981-2984, Rees-Levering Act, yo-yo financing), contract law and arbitration, civil litigation procedure, workers compensation (CA Labor Code), employment law, personal injury and products liability, criminal law, landlord-tenant, family law.

ACTIVE CASE — Lipata v. Nissan of Orange (Case No. 30-2025-01532031-CU-FR-CJC, Orange County Superior Court):
- Asset: 2018 Tesla Model 3, purchased September 5, 2025
- Claims: yo-yo financing fraud, spot delivery fraud, CLRA and UCL violations, illegal repossession, harassment, false police impersonation by recovery agent
- Key legal argument 1: Cancellation notice delivered September 16 — one day past the Civil Code §2982.7 deadline — rendering it legally void
- Key legal argument 2: RISC assigned without recourse to Santander Consumer USA, meaning Nissan lost standing to compel arbitration
- Opposition counsel: Robert N. Phan, Garcia and Phan
- Opposition to Motion to Compel Arbitration due: July 9, 2026
- Hearing date: July 24, 2026
- Plaintiff is pro per (self-represented)

You can draft motions, oppositions, complaints, declarations, and demand letters. Always cite specific statutes and case law. Format legal documents per CRC Rule 2.111. Note this is AI legal information, not an attorney-client relationship.`,
    greeting: `LAWYER BOT ONLINE ✓

Loaded with your active case: Lipata v. Nissan of Orange (Case #30-2025-01532031). Your Opposition to Motion to Compel Arbitration is due July 9, 2026 with the hearing on July 24, 2026.

I can draft your opposition right now, research arbitration defenses (Nissan's lack of standing after RISC assignment, void cancellation under Civil Code §2982.7), or help with any other California or federal legal question.

What do you need?`,
  },
];

export default function NexusAI() {
  const [activeBot, setActiveBot] = useState(0);
  const [conversations, setConversations] = useState(
    BOTS.map((bot) => [
      {
        role: "assistant",
        content: bot.greeting,
        time: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
      },
    ])
  );
  const [inputs, setInputs] = useState(BOTS.map(() => ""));
  const [loading, setLoading] = useState(false);
  const [clock, setClock] = useState("");
  const [apiError, setApiError] = useState(null);
  const msgsRef = useRef(null);

  useEffect(() => {
    const tick = () =>
      setClock(
        new Date().toLocaleTimeString("en-US", {
          hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit",
        })
      );
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (msgsRef.current) msgsRef.current.scrollTop = msgsRef.current.scrollHeight;
  }, [conversations, loading, activeBot]);

  const nowTime = () =>
    new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });

  const sendMessage = useCallback(
    async (botId, overrideText) => {
      const text = (overrideText ?? inputs[botId]).trim();
      if (!text || loading) return;

      setApiError(null);
      setInputs((prev) => prev.map((v, i) => (i === botId ? "" : v)));

      const userMsg = { role: "user", content: text, time: nowTime() };
      setConversations((prev) =>
        prev.map((c, i) => (i === botId ? [...c, userMsg] : c))
      );
      setLoading(true);

      // Build conversation history for the API, excluding the static greeting
      const history = conversations[botId]
        .filter((m) => m.content !== BOTS[botId].greeting)
        .slice(-16)
        .map((m) => ({ role: m.role, content: m.content }));

      try {
        const res = await fetch("https://api.anthropic.com/v1/messages", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            model: "claude-haiku-4-5-20251001",   // exact model string required
            max_tokens: 1024,
            system: BOTS[botId].systemPrompt,
            messages: [...history, { role: "user", content: text }],
          }),
        });

        let data;
        try {
          data = await res.json();
        } catch {
          const raw = await res.text().catch(() => "(unreadable)");
          throw new Error(`Non-JSON response (HTTP ${res.status}): ${raw.slice(0, 300)}`);
        }

        if (!res.ok) {
          throw new Error(data?.error?.message || `HTTP ${res.status}: ${res.statusText}`);
        }

        const reply = data?.content?.[0]?.text;
        if (!reply) throw new Error("API returned an empty response — no content block found.");

        setConversations((prev) =>
          prev.map((c, i) =>
            i === botId ? [...c, { role: "assistant", content: reply, time: nowTime() }] : c
          )
        );
      } catch (err) {
        setApiError(err.message);
        setConversations((prev) =>
          prev.map((c, i) =>
            i === botId
              ? [...c, { role: "assistant", content: `⚠️ ${err.message}`, time: nowTime() }]
              : c
          )
        );
      } finally {
        setLoading(false);
      }
    },
    [inputs, loading, conversations]
  );

  const bot = BOTS[activeBot];

  return (
    <div style={{
      fontFamily: "'Segoe UI', system-ui, sans-serif",
      background: "#030712", color: "#e2e8f0",
      height: "100vh", display: "flex", flexDirection: "column", overflow: "hidden",
    }}>
      <style>{`
        @keyframes bounce { 0%,80%,100%{transform:translateY(0)} 40%{transform:translateY(-6px)} }
        @keyframes pulse  { 0%,100%{opacity:1} 50%{opacity:.4} }
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 2px; }
        textarea { outline: none; font-family: inherit; }
        textarea::placeholder { color: #475569; }
      `}</style>

      {/* grid background */}
      <div style={{
        position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0,
        backgroundImage:
          "linear-gradient(rgba(0,212,255,.025) 1px,transparent 1px)," +
          "linear-gradient(90deg,rgba(0,212,255,.025) 1px,transparent 1px)",
        backgroundSize: "40px 40px",
      }} />

      {/* ── HEADER ── */}
      <div style={{
        display: "flex", alignItems: "center", padding: "10px 20px",
        borderBottom: "1px solid #1e3a5f", background: "rgba(10,17,32,.97)",
        zIndex: 10, flexShrink: 0, gap: 12,
      }}>
        <div>
          <div style={{
            fontFamily: "monospace", fontSize: 18, fontWeight: 900, letterSpacing: 4,
            background: "linear-gradient(135deg,#00d4ff,#7c3aed)",
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
          }}>NEXUS AI</div>
          <div style={{ fontFamily: "monospace", fontSize: 9, color: "#00d4ff", letterSpacing: 3, opacity: .6 }}>
            COMMAND CENTER
          </div>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 8, height: 8, borderRadius: "50%", background: "#10b981",
            boxShadow: "0 0 8px #10b981", animation: "pulse 2s ease-in-out infinite",
          }} />
          <span style={{ fontFamily: "monospace", fontSize: 10, color: "#10b981" }}>ALL SYSTEMS ONLINE</span>
          <span style={{ fontFamily: "monospace", fontSize: 10, color: "#64748b" }}>{clock}</span>
        </div>
      </div>

      {/* ── TABS ── */}
      <div style={{
        display: "flex", overflowX: "auto", borderBottom: "1px solid #1e3a5f",
        background: "rgba(10,17,32,.9)", zIndex: 10, flexShrink: 0, scrollbarWidth: "none",
      }}>
        {BOTS.map((b) => (
          <div key={b.id} onClick={() => setActiveBot(b.id)} style={{
            padding: "11px 16px", cursor: "pointer",
            fontFamily: "monospace", fontSize: 9, fontWeight: 700, letterSpacing: 2,
            color: activeBot === b.id ? b.color : "#64748b",
            borderBottom: activeBot === b.id ? `2px solid ${b.color}` : "2px solid transparent",
            whiteSpace: "nowrap", display: "flex", alignItems: "center", gap: 6,
            transition: "color .2s", userSelect: "none", flexShrink: 0,
          }}>
            <span style={{ fontSize: 13 }}>{b.icon}</span>{b.name}
          </div>
        ))}
      </div>

      {/* ── MAIN ── */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden", position: "relative", zIndex: 5 }}>

        {/* Chat panel */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>

          {/* Bot header */}
          <div style={{
            display: "flex", alignItems: "center", gap: 12, padding: "10px 18px",
            background: "#0f1a2e", borderBottom: "1px solid #1e3a5f", flexShrink: 0,
          }}>
            <div style={{
              width: 38, height: 38, borderRadius: 9, background: bot.colorBg,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 19, flexShrink: 0,
            }}>{bot.icon}</div>
            <div>
              <div style={{ fontFamily: "monospace", fontSize: 11, fontWeight: 700, letterSpacing: 2, color: bot.color }}>
                {bot.name}
              </div>
              <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>{bot.desc}</div>
            </div>
            <div style={{
              marginLeft: "auto", fontFamily: "monospace", fontSize: 9,
              padding: "3px 9px", borderRadius: 20,
              border: `1px solid ${bot.color}`, color: bot.color, background: bot.colorBg,
              letterSpacing: 1, flexShrink: 0,
            }}>{bot.badge}</div>
          </div>

          {/* Error banner */}
          {apiError && (
            <div style={{
              background: "rgba(239,68,68,.12)", border: "1px solid rgba(239,68,68,.3)",
              borderRadius: 6, margin: "8px 18px", padding: "7px 12px",
              fontFamily: "monospace", fontSize: 10, color: "#fca5a5",
              display: "flex", justifyContent: "space-between", alignItems: "center",
            }}>
              <span>⚠ {apiError}</span>
              <span onClick={() => setApiError(null)} style={{ cursor: "pointer", opacity: .7 }}>✕</span>
            </div>
          )}

          {/* Messages */}
          <div ref={msgsRef} style={{
            flex: 1, overflowY: "auto", padding: 18,
            display: "flex", flexDirection: "column", gap: 13,
          }}>
            {conversations[activeBot].map((msg, idx) => {
              const isUser = msg.role === "user";
              return (
                <div key={idx} style={{
                  display: "flex", gap: 9,
                  flexDirection: isUser ? "row-reverse" : "row", alignItems: "flex-start",
                }}>
                  <div style={{
                    width: 28, height: 28, borderRadius: 7, flexShrink: 0,
                    background: isUser ? "rgba(0,212,255,.1)" : bot.colorBg,
                    display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13,
                  }}>{isUser ? "👤" : bot.icon}</div>
                  <div style={{ maxWidth: "78%" }}>
                    <div style={{
                      background: isUser ? "rgba(0,212,255,.08)" : "#0f1a2e",
                      border: `1px solid ${isUser ? "rgba(0,212,255,.2)" : "#1e3a5f"}`,
                      borderRadius: isUser ? "11px 3px 11px 11px" : "3px 11px 11px 11px",
                      padding: "9px 13px", fontSize: 13, lineHeight: 1.65,
                      whiteSpace: "pre-wrap", wordBreak: "break-word",
                      textAlign: isUser ? "right" : "left",
                    }}>{msg.content}</div>
                    <div style={{
                      fontFamily: "monospace", fontSize: 9, color: "#64748b", marginTop: 3,
                      textAlign: isUser ? "right" : "left",
                    }}>{msg.time}</div>
                  </div>
                </div>
              );
            })}

            {loading && (
              <div style={{ display: "flex", gap: 9, alignItems: "flex-start" }}>
                <div style={{
                  width: 28, height: 28, borderRadius: 7, background: bot.colorBg,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 13, flexShrink: 0,
                }}>{bot.icon}</div>
                <div style={{
                  background: "#0f1a2e", border: "1px solid #1e3a5f",
                  borderRadius: "3px 11px 11px 11px", padding: "10px 14px",
                  display: "flex", gap: 4, alignItems: "center",
                }}>
                  {[0,1,2].map(i => (
                    <div key={i} style={{
                      width: 6, height: 6, borderRadius: "50%", background: bot.color,
                      animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
                    }} />
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Quick prompts */}
          <div style={{
            display: "flex", flexWrap: "wrap", gap: 6, padding: "7px 18px",
            background: "#0a1120", borderTop: "1px solid #1e3a5f", flexShrink: 0,
          }}>
            {bot.quickPrompts.map((p, i) => (
              <button key={i} onClick={() => sendMessage(activeBot, p)} disabled={loading} style={{
                fontFamily: "monospace", fontSize: 9, padding: "4px 10px",
                background: "#0f1a2e", border: "1px solid #1e3a5f", borderRadius: 20,
                color: loading ? "#374151" : "#94a3b8",
                cursor: loading ? "not-allowed" : "pointer", letterSpacing: .5, whiteSpace: "nowrap",
              }}>{p}</button>
            ))}
          </div>

          {/* Input */}
          <div style={{
            display: "flex", gap: 9, padding: "11px 18px",
            background: "#0a1120", borderTop: "1px solid #1e3a5f",
            flexShrink: 0, alignItems: "flex-end",
          }}>
            <textarea
              value={inputs[activeBot]}
              onChange={(e) => setInputs((prev) => prev.map((v, i) => i === activeBot ? e.target.value : v))}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(activeBot); } }}
              placeholder={`Message ${bot.name}…`}
              rows={1}
              disabled={loading}
              style={{
                flex: 1, background: "#0f1a2e",
                border: `1px solid ${inputs[activeBot] ? bot.color + "55" : "#1e3a5f"}`,
                borderRadius: 9, color: "#e2e8f0", fontSize: 13,
                padding: "9px 13px", resize: "none", lineHeight: 1.5,
                transition: "border-color .2s", maxHeight: 100, overflowY: "auto",
              }}
            />
            <button
              onClick={() => sendMessage(activeBot)}
              disabled={loading || !inputs[activeBot].trim()}
              style={{
                width: 40, height: 40, borderRadius: 9, border: "none",
                background: loading || !inputs[activeBot].trim() ? "#1e3a5f" : bot.color,
                color: "#030712",
                cursor: loading || !inputs[activeBot].trim() ? "not-allowed" : "pointer",
                fontSize: 15, display: "flex", alignItems: "center",
                justifyContent: "center", transition: "all .2s", flexShrink: 0,
              }}
            >➤</button>
          </div>

          <div style={{
            fontFamily: "monospace", fontSize: 9, color: "#475569",
            padding: "3px 18px 7px", background: "#0a1120", flexShrink: 0,
          }}>
            {activeBot === 4
              ? "⚖ AI legal information only — not a licensed attorney. Verify all statutes independently."
              : activeBot === 2
              ? "⚡ Optimized for Tesla Model 3 | Spark + Instacart | Southern California."
              : "⚠ Educational purposes only. Not financial advice. Always do your own research."}
          </div>
        </div>

        {/* ── SIDEBAR ── */}
        <div style={{
          width: 210, borderLeft: "1px solid #1e3a5f", background: "#0a1120",
          overflowY: "auto", flexShrink: 0, display: "flex", flexDirection: "column",
        }}>
          <div style={{ padding: "12px 13px", borderBottom: "1px solid #1e3a5f" }}>
            <div style={{ fontFamily: "monospace", fontSize: 8, letterSpacing: 3, color: "#64748b", marginBottom: 9 }}>
              MARKET SNAPSHOT
            </div>
            {[
              ["BTC/USD","+2.4%","#10b981"],["ETH/USD","+1.8%","#10b981"],
              ["DOGE","+5.2%","#10b981"],["RZLV","0.0%","#f59e0b"],
              ["SPY","-0.3%","#ef4444"],["GOLD","+0.7%","#10b981"],
            ].map(([sym,chg,col]) => (
              <div key={sym} style={{
                display:"flex",justifyContent:"space-between",padding:"4px 0",
                borderBottom:"1px solid rgba(30,58,95,.4)",fontFamily:"monospace",fontSize:10,
              }}>
                <span style={{color:"#94a3b8"}}>{sym}</span>
                <span style={{color:col}}>{chg}</span>
              </div>
            ))}
            <div style={{fontFamily:"monospace",fontSize:8,color:"#374151",marginTop:5}}>* Simulated · not live</div>
          </div>

          <div style={{ padding: "12px 13px", borderBottom: "1px solid #1e3a5f" }}>
            <div style={{ fontFamily: "monospace", fontSize: 8, letterSpacing: 3, color: "#64748b", marginBottom: 9 }}>
              GIG METRICS
            </div>
            {[
              ["Platform","SPARK+IC","#10b981"],["Vehicle","Tesla M3","#e2e8f0"],
              ["Region","SoCal","#e2e8f0"],["Min $/mi","$1.20","#f59e0b"],
            ].map(([label,val,col]) => (
              <div key={label} style={{display:"flex",justifyContent:"space-between",marginBottom:5,fontSize:11}}>
                <span style={{color:"#64748b"}}>{label}</span>
                <span style={{fontFamily:"monospace",fontSize:10,color:col}}>{val}</span>
              </div>
            ))}
          </div>

          <div style={{ padding: "12px 13px", borderBottom: "1px solid #1e3a5f" }}>
            <div style={{ fontFamily: "monospace", fontSize: 8, letterSpacing: 3, color: "#64748b", marginBottom: 9 }}>
              ACTIVE CASE
            </div>
            <div style={{ fontFamily: "monospace", fontSize: 10, lineHeight: 1.75 }}>
              <div style={{color:"#ef4444",fontWeight:"bold"}}>Lipata v. Nissan</div>
              <div style={{color:"#64748b"}}>#30-2025-01532031</div>
              <div style={{color:"#64748b"}}>OC Superior Court</div>
              <div style={{marginTop:7,color:"#f59e0b"}}>⏰ Opp. Due</div>
              <div style={{color:"#e2e8f0"}}>July 9, 2026</div>
              <div style={{color:"#f59e0b",marginTop:3}}>📅 Hearing</div>
              <div style={{color:"#e2e8f0"}}>July 24, 2026</div>
            </div>
          </div>

          <div style={{ padding: "12px 13px" }}>
            <div style={{ fontFamily: "monospace", fontSize: 8, letterSpacing: 3, color: "#64748b", marginBottom: 9 }}>
              ACTIVE BOT
            </div>
            <div style={{
              padding:"9px 10px", background: bot.colorBg, borderRadius: 8,
              border: `1px solid ${bot.color}30`,
            }}>
              <div style={{fontSize:17,marginBottom:3}}>{bot.icon}</div>
              <div style={{fontFamily:"monospace",fontSize:9,color:bot.color,letterSpacing:1}}>{bot.name}</div>
              <div style={{fontSize:10,color:"#64748b",marginTop:3,lineHeight:1.4}}>{bot.desc}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
