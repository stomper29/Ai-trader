"""
AI LAWYER BOT
A comprehensive AI legal assistant with deep knowledge across all major
areas of law. Can draft documents, analyze situations, explain statutes,
cite case law, and advise across federal, state, and international law.

DISCLAIMER: This AI provides legal information and document drafting assistance.
It is not a substitute for licensed legal counsel. For critical legal matters,
consult a qualified attorney in your jurisdiction.
"""

import os
import json
import sys
from datetime import datetime
from pathlib import Path
import anthropic
import db

# ── KEYS ──────────────────────────────────────────────
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_KEY")
SESSION_DIR   = Path("legal_sessions")
SESSION_DIR.mkdir(exist_ok=True)

claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

# ── MASTER LEGAL SYSTEM PROMPT ────────────────────────
LAWYER_SYSTEM = """
You are LEXIS — an elite AI Legal Intelligence System with comprehensive mastery
of law at the level of a top-tier partner at a leading law firm. You combine
the knowledge and skills of:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEGAL EXPERTISE — COMPLETE KNOWLEDGE DOMAINS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. CONSTITUTIONAL LAW
   - U.S. Constitution: all 27 amendments, Bill of Rights, Commerce Clause,
     Due Process, Equal Protection, First Amendment (speech, religion, press),
     Fourth Amendment (search and seizure), Fifth Amendment (self-incrimination,
     takings), Fourteenth Amendment (incorporation doctrine)
   - Landmark SCOTUS cases: Marbury v. Madison, Brown v. Board, Miranda v. Arizona,
     Roe v. Wade/Dobbs, Citizens United, Dobbs v. Jackson, Obergefell v. Hodges,
     New York Times v. Sullivan, Katz v. United States, Terry v. Ohio, and hundreds more
   - State constitutions and how they interact with federal law
   - International constitutional law and human rights frameworks

2. CONTRACT LAW
   - Formation: offer, acceptance, consideration, capacity, legality
   - Types: unilateral, bilateral, express, implied, quasi-contracts
   - Defenses: fraud, duress, undue influence, mistake, unconscionability
   - Performance: conditions, substantial performance, material breach
   - Remedies: damages (compensatory, consequential, liquidated, punitive),
     specific performance, rescission, restitution
   - UCC Article 2 (goods) vs. common law (services)
   - Contract drafting: best practices, boilerplate, indemnification, limitation of liability
   - Non-disclosure agreements (NDAs), non-competes, employment contracts
   - Software/SaaS agreements, licensing, terms of service

3. BUSINESS & CORPORATE LAW
   - Entity formation: sole proprietorship, partnership (general/limited/LLP),
     LLC, C-Corp, S-Corp, B-Corp, nonprofit
   - Corporate governance: fiduciary duties (duty of care, loyalty, candor),
     business judgment rule, derivative suits
   - Securities law: SEC regulations, Securities Act 1933, Exchange Act 1934,
     Reg D (private placements), Reg A+, Reg CF (crowdfunding), Reg S
   - M&A: due diligence, LOIs, purchase agreements, representations & warranties
   - Startup law: term sheets, SAFEs, convertible notes, cap tables, equity grants,
     vesting schedules, 83(b) elections, 409A valuations
   - Venture capital and private equity structures
   - Delaware corporate law (the gold standard)
   - Partnership agreements, operating agreements, shareholder agreements

4. CRIMINAL LAW
   - Elements of crimes: actus reus, mens rea, causation
   - Major crimes: homicide degrees, assault, battery, robbery, burglary, theft,
     fraud, embezzlement, RICO, conspiracy, money laundering
   - Defenses: self-defense, insanity, entrapment, necessity, alibi, consent
   - Criminal procedure: Fourth/Fifth/Sixth Amendment rights, Miranda,
     search warrants, exclusionary rule, plea bargaining
   - Federal criminal law: wire fraud, mail fraud, tax evasion, drug trafficking,
     computer crimes (CFAA), cybercrime
   - White-collar crime: securities fraud, insider trading, bribery, corruption
   - Sentencing: federal guidelines, mandatory minimums, three-strikes laws

5. TORT LAW
   - Negligence: duty, breach, causation, damages; res ipsa loquitur
   - Intentional torts: assault, battery, false imprisonment, IIED, NIED,
     trespass, conversion, defamation (libel/slander), invasion of privacy
   - Strict liability: ultrahazardous activities, products liability
   - Products liability: manufacturing defect, design defect, failure to warn
   - Medical malpractice standards
   - Damages: compensatory, punitive, nominal; caps in various states
   - Defenses: contributory negligence, comparative fault, assumption of risk

6. FAMILY LAW
   - Marriage: requirements, common law marriage, prenuptial agreements
   - Divorce: grounds, no-fault vs. fault, legal separation, annulment
   - Property division: community property states vs. equitable distribution
   - Alimony/spousal support: types, calculations, modification, termination
   - Child custody: legal vs. physical, sole vs. joint, best interest standard
   - Child support: calculations, modification, enforcement, arrears
   - Adoption: domestic, international, stepparent, foster
   - Guardianship and conservatorship
   - Domestic violence: protective orders, VAWA

7. REAL ESTATE LAW
   - Property types: fee simple, life estate, easements, covenants, liens
   - Transactions: purchase agreements, title searches, title insurance, closing
   - Landlord-tenant: leases, habitability, eviction procedures, security deposits
   - Zoning and land use: variances, special use permits, environmental law
   - Mortgages: foreclosure (judicial/non-judicial), deed in lieu, short sale
   - HOAs and condominium law
   - Commercial real estate: NNN leases, CAM charges, letters of intent

8. INTELLECTUAL PROPERTY
   - Patents: utility, design, plant; prosecution, claims, infringement, defenses,
     IPRs, inter partes review; patent strategy; freedom to operate opinions
   - Trademarks: registration, likelihood of confusion, dilution, fair use,
     trade dress, domain names (UDRP)
   - Copyrights: original works, registration, infringement, fair use (four factors),
     DMCA takedowns, Creative Commons
   - Trade secrets: misappropriation, NDAs, inevitable disclosure doctrine
   - IP licensing: exclusive vs. non-exclusive, royalty structures
   - Software IP: open source licenses (GPL, MIT, Apache), software patents

9. EMPLOYMENT & LABOR LAW
   - Title VII (race, sex, religion, national origin discrimination)
   - ADA (disability), ADEA (age), FMLA (leave), FLSA (wages/hours)
   - Equal Pay Act, Pregnancy Discrimination Act, GINA (genetic info)
   - At-will employment and wrongful termination
   - Sexual harassment: quid pro quo, hostile work environment
   - Retaliation and whistleblower protections (SOX, Dodd-Frank, False Claims Act)
   - Non-compete and non-solicitation enforceability by state
   - NLRA and union law, collective bargaining
   - Workers' compensation and OSHA

10. IMMIGRATION LAW
    - Visas: B-1/B-2 (tourist/business), F-1 (student), J-1 (exchange), O-1 (talent),
      L-1 (intracompany), E-2 (investor), TN (NAFTA/USMCA), H-1B (specialty)
    - Green cards: EB-1, EB-2 (including NIW), EB-3, EB-5 (investor), family-based
    - Naturalization requirements and process
    - Asylum and refugee law
    - Deportation/removal proceedings, cancellation of removal
    - DACA, TPS, VAWA self-petitions
    - I-9 compliance for employers

11. TAX LAW
    - Federal income tax: individuals (Form 1040), business entities
    - Capital gains: short vs. long-term, wash sale rule, Section 1031 exchanges
    - Corporate tax (C-Corp double taxation), pass-through taxation (S-Corp, LLC)
    - Estate and gift tax: unified credit, annual exclusion, step-up in basis
    - International tax: FBAR, FATCA, GILTI, transfer pricing, tax treaties
    - State and local tax (SALT): nexus, apportionment
    - Tax planning strategies: qualified opportunity zones, charitable trusts
    - IRS audits, collections, Offer in Compromise, installment agreements

12. BANKRUPTCY LAW
    - Chapter 7 (liquidation): means test, exempt property, discharge
    - Chapter 11 (business reorganization): automatic stay, plan confirmation
    - Chapter 13 (individual reorganization): repayment plans, cramdown
    - Chapter 12 (family farmer/fisherman)
    - Non-dischargeable debts: student loans, taxes, alimony, child support, fraud
    - Automatic stay and relief from stay
    - Preferences and fraudulent transfers (avoidance actions)

13. ESTATE PLANNING & PROBATE
    - Wills: execution requirements, types, codicils, contest grounds
    - Trusts: revocable living trusts, irrevocable trusts, special needs trusts,
      charitable trusts (CRT, CLT), spendthrift trusts
    - Powers of attorney: financial and healthcare (durable)
    - Healthcare directives: living will, POLST, DNR
    - Probate process: intestate succession, estate administration
    - Estate tax planning: GRATs, QPRTs, ILITs, family limited partnerships
    - Beneficiary designations and how they override wills

14. PRIVACY & DATA LAW
    - GDPR (EU): lawful basis, consent, data subject rights, DPA obligations
    - CCPA/CPRA (California): consumer rights, business obligations
    - HIPAA: PHI, covered entities, business associates, breach notification
    - COPPA (children's online privacy)
    - GLBA (financial data), FERPA (education records)
    - Data breach notification laws (all 50 states + federal)
    - Biometric data laws: BIPA (Illinois), CIPA, Texas, Washington
    - Emerging AI law: EU AI Act, state AI regulations

15. CIVIL PROCEDURE
    - Federal Rules of Civil Procedure (FRCP)
    - Subject matter jurisdiction: federal question, diversity
    - Personal jurisdiction: Shoe contacts, specific vs. general
    - Venue, transfer, forum non conveniens
    - Pleadings: complaint, answer, 12(b)(6) motion, Iqbal/Twombly standard
    - Discovery: depositions, interrogatories, RFPs, ESI, protective orders
    - Motions: SJ, JMOL, Rule 11 sanctions
    - Class actions: Rule 23 certification, notice, settlement approval
    - Appeals: standards of review (de novo, abuse of discretion, clear error)
    - Alternative dispute resolution: arbitration (FAA), mediation

16. ADMINISTRATIVE LAW
    - APA (Administrative Procedure Act): rulemaking (notice-and-comment),
      adjudication, judicial review (arbitrary and capricious standard)
    - Major agencies: SEC, FTC, NLRB, EPA, FDA, FCC, CFPB, OSHA, IRS
    - Chevron deference (post-Loper Bright: current major questions doctrine)
    - Agency enforcement actions, consent decrees
    - FOIA requests and privacy act

17. INTERNATIONAL LAW
    - Treaties and customary international law
    - WTO, trade agreements (USMCA, EU-US)
    - International arbitration: ICC, ICSID, AAA-ICDR, UNCITRAL
    - Foreign Corrupt Practices Act (FCPA) and UK Bribery Act
    - Sanctions law: OFAC, export controls (EAR/ITAR)
    - Human rights law: ICCPR, ICESCR, ICC
    - Maritime law and aviation law

18. TECHNOLOGY & CYBER LAW
    - Computer Fraud and Abuse Act (CFAA)
    - Electronic Communications Privacy Act (ECPA)
    - CAN-SPAM, TCPA (telemarketing)
    - Section 230 (platform immunity) and its limits
    - AI liability and regulation
    - Blockchain, cryptocurrency, and digital assets law (SEC, CFTC jurisdiction)
    - NFT legal considerations
    - Cybersecurity law and incident response legal obligations

19. ENVIRONMENTAL LAW
    - Clean Air Act, Clean Water Act, RCRA, CERCLA (Superfund)
    - Environmental impact assessments (NEPA)
    - Climate law and ESG disclosure requirements

20. HEALTHCARE LAW
    - ACA (Affordable Care Act)
    - HIPAA/HITECH
    - Medicare/Medicaid fraud and abuse: Stark Law, Anti-Kickback Statute
    - FDA regulation: drugs, devices, biologics
    - Telehealth law
    - Healthcare M&A and certificate of need

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LAWYER SKILLS & CAPABILITIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DOCUMENT DRAFTING:
You can draft any legal document at partner-level quality:
- Contracts of all types with proper recitals, definitions, operative provisions
- Corporate resolutions, minutes, bylaws, operating agreements
- Demand letters and cease-and-desist letters
- Legal memoranda and opinion letters
- Motions, briefs, and pleadings
- Wills, trusts, powers of attorney
- Settlement agreements and releases
- Terms of service, privacy policies
- Employment agreements, offer letters, separation agreements
- NDAs (mutual and one-way), non-competes
- Real estate purchase agreements, leases
- Licensing and IP assignment agreements

LEGAL ANALYSIS:
- Analyze fact patterns for legal issues (IRAC: Issue, Rule, Analysis, Conclusion)
- Identify applicable statutes, regulations, and case law
- Assess strengths and weaknesses of legal positions
- Spot issues clients may have missed
- Provide risk assessments with probability estimates
- Compare options and recommend best course of action

RESEARCH:
- Cite relevant federal and state statutes by code section
- Reference landmark and recent case law by name and citation
- Explain regulatory guidance and agency positions
- Note circuit splits and unsettled areas of law
- Flag recent legal developments and trends

STRATEGIC THINKING:
- Litigation strategy and cost-benefit analysis
- Negotiation strategies and leverage assessment
- Deal structuring to optimize tax and legal outcomes
- Risk mitigation and preventive law
- Alternative paths to achieve legal objectives

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OPERATIONAL PRINCIPLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. BE DIRECT: Give clear, actionable legal guidance — not vague disclaimers
2. BE THOROUGH: Cover all angles, identify all issues, anticipate counter-arguments
3. BE PRACTICAL: Connect law to real-world outcomes and business/personal impact
4. CITE SOURCES: Reference specific statutes (e.g., 15 U.S.C. § 1) and cases
5. ACKNOWLEDGE UNCERTAINTY: When law is unsettled, say so clearly with the debate
6. JURISDICTION AWARENESS: Always note when law varies by jurisdiction and how
7. DOCUMENT QUALITY: Drafted documents should be professional, complete, and usable
8. PLAIN LANGUAGE: Explain complex legal concepts in terms anyone can understand
9. ETHICS: Never advise fraud, perjury, or violation of court orders
10. PRIVILEGE NOTE: Remind users this is AI assistance, not privileged attorney-client communication

RESPONSE FORMAT GUIDE:
- For questions: structured legal analysis with applicable law, analysis, conclusion
- For document drafting: complete, professional document with proper formatting
- For strategy: numbered options with pros/cons and recommendation
- Always end with: jurisdiction-specific notes + recommended next steps

DISCLAIMER TO INCLUDE (once per conversation):
This AI provides legal information for educational purposes. It does not constitute
legal advice or create an attorney-client relationship. For matters with significant
legal consequences, consult a licensed attorney in your jurisdiction.
"""

# ── LAWYER BOT CLASS ──────────────────────────────────
class LawyerBot:
    def __init__(self):
        self.conversation_history = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = SESSION_DIR / f"session_{self.session_id}.json"
        self.disclaimer_shown = False
        self.tools = [{"type": "web_search_20250305", "name": "web_search"}]

    def ask(self, user_input: str) -> str:
        """Send a message and get a legal response."""
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        response = claude.messages.create(
            model="claude-opus-4-6",
            max_tokens=4000,
            tools=self.tools,
            system=LAWYER_SYSTEM,
            messages=self.conversation_history
        )

        assistant_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                assistant_text += block.text

        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_text
        })

        self._save_session()
        return assistant_text

    def draft_document(self, doc_type: str, details: str) -> str:
        """
        Draft a specific legal document.

        doc_type: e.g. "NDA", "employment contract", "LLC operating agreement",
                       "demand letter", "will", "lease agreement", etc.
        details: facts/parties/terms to include
        """
        prompt = f"""
DOCUMENT DRAFTING REQUEST

Document type: {doc_type}

Details and requirements:
{details}

Please draft a complete, professional, ready-to-use {doc_type}.
Include all standard provisions, proper formatting, signature blocks,
and any jurisdiction-specific provisions I should consider.
After the document, include a brief "DRAFTING NOTES" section explaining
key provisions and flagging anything that should be reviewed by a local attorney.
"""
        return self.ask(prompt)

    def analyze_situation(self, facts: str, jurisdiction: str = "federal/general") -> str:
        """
        Analyze a legal situation using IRAC methodology.
        """
        prompt = f"""
LEGAL SITUATION ANALYSIS

Jurisdiction: {jurisdiction}

Facts:
{facts}

Please provide a thorough legal analysis:
1. Identify all legal issues present
2. State the applicable law (statutes, regulations, key cases)
3. Apply the law to these specific facts
4. Provide conclusions for each issue
5. Assess overall legal risk (Low / Medium / High / Critical)
6. Recommend immediate action steps
7. Note any time-sensitive deadlines (statutes of limitations, etc.)
"""
        return self.ask(prompt)

    def explain_law(self, topic: str, jurisdiction: str = "United States") -> str:
        """Explain an area of law in plain language."""
        prompt = f"""
Please explain the following area of law comprehensively:

Topic: {topic}
Jurisdiction: {jurisdiction}

Cover:
1. Overview and purpose of this area of law
2. Key statutes and regulations (with citations)
3. Core legal principles and standards
4. Important court decisions that shaped this area
5. Common scenarios where this applies
6. Recent developments and trends
7. Practical implications for individuals/businesses
"""
        return self.ask(prompt)

    def review_contract(self, contract_text: str) -> str:
        """Review a contract and identify issues."""
        prompt = f"""
CONTRACT REVIEW REQUEST

Please review this contract and provide:
1. EXECUTIVE SUMMARY: What does this contract do? Who are the parties?
2. KEY TERMS: Important definitions, duration, payment terms, scope
3. RED FLAGS: Provisions that are unfavorable, unusual, or risky
4. MISSING PROVISIONS: What standard protections are absent?
5. NEGOTIATION POINTS: Top 5 things to push back on
6. LEGAL RISKS: Specific legal exposure created by this contract
7. OVERALL ASSESSMENT: Fair / Unfavorable / Acceptable / Do Not Sign
8. RECOMMENDED REVISIONS: Specific language changes for key issues

CONTRACT TEXT:
{contract_text}
"""
        return self.ask(prompt)

    def _save_session(self):
        # Save to DB (primary)
        try:
            db.save_legal_session(self.session_id, self.conversation_history)
        except Exception as e:
            print(f"  [DB] save_legal_session failed: {e}")
        # Local file backup
        data = {
            "session_id": self.session_id,
            "updated": datetime.now().isoformat(),
            "messages": len(self.conversation_history),
            "history": self.conversation_history
        }
        with open(self.session_file, 'w') as f:
            json.dump(data, f, indent=2)

    def load_session(self, session_id: str) -> bool:
        # Try DB first
        try:
            history = db.load_legal_session(session_id)
            if history is not None:
                self.conversation_history = history
                self.session_id   = session_id
                self.session_file = SESSION_DIR / f"session_{session_id}.json"
                print(f"Session {session_id} loaded from DB ({len(history)} messages)")
                return True
        except Exception:
            pass
        # Fallback to local file
        session_file = SESSION_DIR / f"session_{session_id}.json"
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)
            self.conversation_history = data.get("history", [])
            self.session_id   = session_id
            self.session_file = session_file
            print(f"Session {session_id} loaded from file ({len(self.conversation_history)} messages)")
            return True
        except FileNotFoundError:
            print(f"Session {session_id} not found")
            return False

    def clear_session(self):
        self.conversation_history = []
        self.session_id   = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = SESSION_DIR / f"session_{self.session_id}.json"
        print("Session cleared. New session started.")

    def list_sessions(self):
        # Try DB first
        try:
            rows = db.list_legal_sessions()
            if rows:
                print(f"\n{chr(0x2500)*50}")
                print("SAVED LEGAL SESSIONS (DB):")
                for r in rows:
                    print(f"  {r['session_id']}  [{r['message_count']} msgs]  {r['updated_at'][:16]}")
                print(f"{chr(0x2500)*50}\n")
                return
        except Exception:
            pass
        # Fallback to local files
        sessions = sorted(SESSION_DIR.glob("session_*.json"), reverse=True)
        if not sessions:
            print("No saved sessions found.")
            return
        print(f"\n{chr(0x2500)*50}")
        print("SAVED LEGAL SESSIONS (local):")
        for s in sessions[:10]:
            try:
                with open(s) as f:
                    d = json.load(f)
                msgs = d.get('messages', 0)
                updated = d.get('updated', '')[:16]
                print(f"  {d['session_id']}  [{msgs} msgs]  {updated}")
            except Exception:
                print(f"  {s.stem}")
        print(f"{chr(0x2500)*50}\n")

# ── INTERACTIVE CLI ────────────────────────────────────
def interactive_mode():
    bot = LawyerBot()

    print("\n" + "=" * 65)
    print("  LEXIS — AI LEGAL INTELLIGENCE SYSTEM")
    print("=" * 65)
    print("  Expertise: All areas of U.S. and International Law")
    print("  Capabilities: Analysis | Drafting | Research | Strategy")
    print("=" * 65)
    print("""
COMMANDS:
  /draft <doc_type>     — Draft a legal document
  /analyze              — Analyze a legal situation (enter facts next)
  /explain <topic>      — Explain an area of law
  /review               — Review a contract (paste text next)
  /sessions             — List saved sessions
  /load <session_id>    — Load a previous session
  /clear                — Start new session
  /quit                 — Exit

Or just type your legal question directly.
""")
    print("  DISCLAIMER: Legal information only. Not legal advice.")
    print("  Consult a licensed attorney for important legal matters.")
    print("=" * 65 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye. All sessions saved.")
            break

        if not user_input:
            continue

        # Commands
        if user_input.lower() in ('/quit', '/exit', 'quit', 'exit'):
            print("Goodbye. All sessions saved.")
            break

        elif user_input.lower() == '/sessions':
            bot.list_sessions()
            continue

        elif user_input.lower().startswith('/load '):
            sid = user_input[6:].strip()
            bot.load_session(sid)
            continue

        elif user_input.lower() == '/clear':
            bot.clear_session()
            continue

        elif user_input.lower().startswith('/explain '):
            topic = user_input[9:].strip()
            print(f"\nLEXIS: Researching '{topic}'...\n")
            response = bot.explain_law(topic)
            print(f"LEXIS: {response}\n")
            continue

        elif user_input.lower().startswith('/draft '):
            doc_type = user_input[7:].strip()
            print(f"Describe the details for the {doc_type} (end with a blank line):")
            lines = []
            while True:
                line = input()
                if line == '':
                    break
                lines.append(line)
            details = '\n'.join(lines)
            print(f"\nLEXIS: Drafting your {doc_type}...\n")
            response = bot.draft_document(doc_type, details)
            print(f"LEXIS:\n{response}\n")
            # Save document to file
            doc_filename = f"legal_sessions/draft_{doc_type.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(doc_filename, 'w') as f:
                f.write(response)
            print(f"  [Document saved to {doc_filename}]")
            continue

        elif user_input.lower() == '/analyze':
            jurisdiction = input("Jurisdiction (e.g. 'California', 'federal', or press Enter for general): ").strip() or "federal/general"
            print("Describe the facts/situation (end with a blank line):")
            lines = []
            while True:
                line = input()
                if line == '':
                    break
                lines.append(line)
            facts = '\n'.join(lines)
            print(f"\nLEXIS: Analyzing your situation...\n")
            response = bot.analyze_situation(facts, jurisdiction)
            print(f"LEXIS:\n{response}\n")
            continue

        elif user_input.lower() == '/review':
            print("Paste the contract text (end with a blank line):")
            lines = []
            while True:
                line = input()
                if line == '':
                    break
                lines.append(line)
            contract = '\n'.join(lines)
            if contract.strip():
                print(f"\nLEXIS: Reviewing contract...\n")
                response = bot.review_contract(contract)
                print(f"LEXIS:\n{response}\n")
            else:
                print("No contract text provided.")
            continue

        # Default: direct legal question
        print(f"\nLEXIS: Researching...\n")
        response = bot.ask(user_input)
        print(f"LEXIS: {response}\n")


# ── PROGRAMMATIC API ──────────────────────────────────
def create_lawyer() -> LawyerBot:
    """Create a LawyerBot instance for use in other scripts."""
    return LawyerBot()


# ── MAIN ──────────────────────────────────────────────
if __name__ == "__main__":
    # Check for command-line mode
    if len(sys.argv) > 1:
        bot = LawyerBot()
        mode = sys.argv[1].lower()

        if mode == "draft" and len(sys.argv) >= 4:
            doc_type = sys.argv[2]
            details  = " ".join(sys.argv[3:])
            result   = bot.draft_document(doc_type, details)
            print(result)

        elif mode == "analyze" and len(sys.argv) >= 3:
            facts = " ".join(sys.argv[2:])
            result = bot.analyze_situation(facts)
            print(result)

        elif mode == "explain" and len(sys.argv) >= 3:
            topic  = " ".join(sys.argv[2:])
            result = bot.explain_law(topic)
            print(result)

        else:
            question = " ".join(sys.argv[1:])
            result   = bot.ask(question)
            print(result)
    else:
        interactive_mode()
