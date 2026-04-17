<h1 align="center">Hi, I'm Efecan 👋</h1>

<p align="center">
  <strong>Computer Science senior at California Lutheran University</strong> · <em>3.9 GPA</em> · graduating May 2026<br/>
  Building full-stack production systems with ML at their core.
</p>

<p align="center">
  <a href="https://www.linkedin.com/in/efe-biskin-923397400"><img src="https://img.shields.io/badge/-LinkedIn-0A66C2?style=flat&logo=linkedin&logoColor=white" alt="LinkedIn" /></a>
  <a href="mailto:efebskn@gmail.com"><img src="https://img.shields.io/badge/-Email-D14836?style=flat&logo=gmail&logoColor=white" alt="Email" /></a>
  <img src="https://komarev.com/ghpvc/?username=efebiskin&label=Profile%20views&color=0e75b6&style=flat" alt="profile views" />
</p>

<p align="center">
  <a href="https://git.io/typing-svg">
    <img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=600&size=22&duration=3000&pause=900&color=8B5CF6&center=true&vCenter=true&width=720&lines=AI%2FML+Engineer+%2B+Software+Engineer;Rigorous+validation.+Honest+failure+analysis.;Shipping+real+systems%2C+not+demos." alt="typing"/>
  </a>
</p>

---

<p align="center">
  <a href="https://github.com/efebiskin">
    <img height="165" src="https://github-readme-stats.vercel.app/api?username=efebiskin&show_icons=true&theme=tokyonight&hide_border=true&count_private=true&include_all_commits=true" alt="GitHub stats" />
  </a>
  <a href="https://github.com/efebiskin">
    <img height="165" src="https://github-readme-stats.vercel.app/api/top-langs/?username=efebiskin&layout=compact&theme=tokyonight&hide_border=true&langs_count=10&exclude_repo=efebiskin&size_weight=0.5&count_weight=0.5&v=2" alt="Top languages" />
  </a>
</p>

<p align="center">
  <img src="https://github-readme-streak-stats.herokuapp.com/?user=efebiskin&theme=tokyonight&hide_border=true" alt="GitHub streak" />
</p>

<p align="center">
  <img src="https://github-readme-activity-graph.vercel.app/graph?username=efebiskin&theme=tokyo-night&hide_border=true&area=true" alt="contribution graph" />
</p>

<p align="center">
  <img src="https://github-profile-trophy.vercel.app/?username=efebiskin&theme=tokyonight&no-frame=true&no-bg=true&margin-w=6&column=7" alt="GitHub trophies" />
</p>

---

## ⭐ Featured open-source work

<table>
  <tr>
    <td width="50%" valign="top">
      <a href="https://github.com/efebiskin/mini-react">
        <img src="https://github-readme-stats.vercel.app/api/pin/?username=efebiskin&repo=mini-react&theme=tokyonight&hide_border=true" />
      </a>
      <p><strong>A from-scratch ~220-line clone of React's core</strong> — virtual DOM, function components, hooks, reconciling diff. Zero dependencies, zero build step. 10/10 tests passing. Read top-to-bottom and you understand how React works.</p>
    </td>
    <td width="50%" valign="top">
      <a href="https://github.com/efebiskin/sec-form4-parser">
        <img src="https://github-readme-stats.vercel.app/api/pin/?username=efebiskin&repo=sec-form4-parser&theme=tokyonight&hide_border=true" />
      </a>
      <p><strong>Clean typed Python parser for SEC Form 4 insider-trading XML filings.</strong> Dataclass-based, rate-limited EDGAR fetcher, CLI, 13/13 tests. Zero runtime dependencies.</p>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <a href="https://github.com/efebiskin/python-dsa">
        <img src="https://github-readme-stats.vercel.app/api/pin/?username=efebiskin&repo=python-dsa&theme=tokyonight&hide_border=true" />
      </a>
      <p><strong>20 classic algorithm problems in Python</strong>, organized by pattern. Every solution ships the best known approach with time/space complexity noted. 80 pytest assertions. Self-contained curriculum.</p>
    </td>
    <td width="50%" valign="top">
      <a href="https://github.com/efebiskin/cliprythm">
        <img src="https://github-readme-stats.vercel.app/api/pin/?username=efebiskin&repo=cliprythm&theme=tokyonight&hide_border=true" />
      </a>
      <p><strong>ClipRhythm</strong> — automated short-form video pipeline. AI-generated scripts and voiceover, auto-publishes to TikTok. Proof-of-concept for a content-automation SaaS I'm registering as a business.</p>
    </td>
  </tr>
</table>

---

## 🧠 Flagship projects *(private source — happy to walk through on request)*

### Autonomous ML Trading Platform
Ensemble-model trading system *(XGBoost + LightGBM + Random Forest, stacked, isotonic-calibrated)* with walk-forward cross-validation and time-series embargo to prevent look-ahead bias. After rigorous out-of-sample testing revealed the ensemble overfit, I pivoted to **two academic-backed alpha strategies**. Live backtest results:

| Strategy | Win Rate | Alpha vs S&P 500 | Sharpe | Sample |
|---|---|---|---|---|
| Insider-buy + momentum filter *(Lakonishok-Lee 2001)* | **64.6%** | +3.31% | 1.21 | 164 trades, 3 years |
| Post-earnings drift *(Bernard-Thomas 1989)* | **65.5%** | +4.46% | 0.91 | 142 events, 3 years |

Production infra: Popen-based watchdog with exponential-backoff restart, Telegram `/panic` kill switch, daily performance digest, live-trading gate blocking real-money execution until thresholds met, 17-test pytest invariant suite, Flask dashboard integrating 9 data sources (SEC EDGAR, yfinance, FRED, Congressional disclosures, ARK, Google News, Reddit, Alpaca, in-house news-radar).

### LFVI — Land Future Value Index
AI-powered real-estate investment intelligence. End-to-end ML pipeline ingesting **7+ U.S. government data APIs** (Census ACS, IRS, BLS, FRED, FEMA, Zillow), engineering **50+ features per county**, training **5 ensemble models** to score all 3,100+ U.S. counties. Extends down to individual parcels via APN polygon lookups with a Deal Analyzer that estimates max rational purchase price. Delivered as an interactive Dash choropleth dashboard with tract-level drilldown.

### Olympiq — Personalized Fitness Web App *(CSC499 Senior Capstone)*
Zero-install single-file web application (~214 KB HTML) with a **hand-rolled 208-line React-like runtime** (virtual DOM, hook system, event delegation) compiled from JSX via esbuild. **No framework dependencies.** Supabase auth + Postgres backend. Offline-capable.

### HERA — Personal AI Assistant
Jarvis-style orchestration: Claude API (reasoning), Telegram Bot API (mobile), Obsidian vault (persistent memory across sessions), ElevenLabs (voice), Windows desktop avatar overlay. 42 registered tools across memory, PC control, vision, and agentic-coding.

### BEF Games *(shipped on Steam)*
Contributor to *The Boss Gangsters: Nightlife*. Ship features, patches, and trilingual localization (EN/TR/ES). Brokered the studio's publishing partnership with **Tripwire Interactive** (*Killing Floor*, *Rising Storm*).

---

## 🛠️ Tech

<p>
  <img src="https://img.shields.io/badge/-Python-3776AB?style=flat&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/-JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black" />
  <img src="https://img.shields.io/badge/-TypeScript-3178C6?style=flat&logo=typescript&logoColor=white" />
  <img src="https://img.shields.io/badge/-Java-007396?style=flat&logo=openjdk&logoColor=white" />
  <img src="https://img.shields.io/badge/-C%2B%2B-00599C?style=flat&logo=c%2B%2B&logoColor=white" />
  <img src="https://img.shields.io/badge/-SQL-4479A1?style=flat&logo=postgresql&logoColor=white" />
</p>

<p>
  <img src="https://img.shields.io/badge/-PyTorch-EE4C2C?style=flat&logo=pytorch&logoColor=white" />
  <img src="https://img.shields.io/badge/-scikit--learn-F7931E?style=flat&logo=scikit-learn&logoColor=white" />
  <img src="https://img.shields.io/badge/-XGBoost-EB5E28?style=flat" />
  <img src="https://img.shields.io/badge/-LightGBM-0288D1?style=flat" />
  <img src="https://img.shields.io/badge/-pandas-150458?style=flat&logo=pandas&logoColor=white" />
  <img src="https://img.shields.io/badge/-NumPy-013243?style=flat&logo=numpy&logoColor=white" />
  <img src="https://img.shields.io/badge/-Claude_API-D97757?style=flat" />
</p>

<p>
  <img src="https://img.shields.io/badge/-React-61DAFB?style=flat&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/-Node.js-339933?style=flat&logo=node.js&logoColor=white" />
  <img src="https://img.shields.io/badge/-Flask-000000?style=flat&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/-Dash-008DE4?style=flat&logo=plotly&logoColor=white" />
  <img src="https://img.shields.io/badge/-Supabase-3ECF8E?style=flat&logo=supabase&logoColor=white" />
  <img src="https://img.shields.io/badge/-PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/-SQLite-003B57?style=flat&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/-Docker-2496ED?style=flat&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/-Git-F05032?style=flat&logo=git&logoColor=white" />
  <img src="https://img.shields.io/badge/-pytest-0A9EDC?style=flat&logo=pytest&logoColor=white" />
</p>

---

## 🎓 About

- **B.S. Computer Science**, Minor in Psychology — California Lutheran University (May 2026, **3.9 GPA**)
- 📜 Certified in **AI Engineering & Applied AI**, Computer Hardware and Systems
- 🌍 Fluent in **English**, native **Turkish**, conversational **Spanish**
- 💼 Currently open to **AI / ML Engineer** and **Software Engineer** new-grad roles for 2026
- 🎯 Interested in: applied ML, quantitative finance, developer tools, systems that learn from their own mistakes

---

## 💬 What I believe about engineering

> **Rigorous validation over demo-day magic.**
> My trading system's ensemble looked great in-sample — 59.7% win rate at prob ≥ 0.70. Out-of-sample it collapsed to 48.5%, worse than a coin flip. I caught the overfit myself, documented it, and rebuilt around academic-validated strategies instead of shipping the lie. That's the work.

---

## 📫 Let's connect

<p>
  <a href="mailto:efebskn@gmail.com"><img src="https://img.shields.io/badge/-efebskn@gmail.com-D14836?style=flat&logo=gmail&logoColor=white" /></a>
  <a href="https://www.linkedin.com/in/efe-biskin-923397400"><img src="https://img.shields.io/badge/-LinkedIn-0A66C2?style=flat&logo=linkedin&logoColor=white" /></a>
  <a href="https://github.com/efebiskin"><img src="https://img.shields.io/badge/-GitHub-181717?style=flat&logo=github&logoColor=white" /></a>
</p>

<p align="center"><sub><em>Flagship project source is private. Happy to walk through architecture, design decisions, or demo live on request.</em></sub></p>
