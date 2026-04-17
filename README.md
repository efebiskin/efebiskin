# Hi, I'm Efecan 👋

**Computer Science senior at California Lutheran University** *(3.9 GPA, graduating May 2026)* building full-stack production systems with ML at their core.

I like rigorous validation, honest failure analysis, and shipping things that actually work — not demos.

<p align="left">
  <img src="https://komarev.com/ghpvc/?username=efebiskin&label=Profile%20views&color=0e75b6&style=flat" alt="profile views" />
</p>

---

<p align="center">
  <a href="https://github.com/efebiskin">
    <img height="165" src="https://github-readme-stats.vercel.app/api?username=efebiskin&show_icons=true&theme=tokyonight&hide_border=true&count_private=true&include_all_commits=true" alt="GitHub stats" />
  </a>
  <a href="https://github.com/efebiskin">
    <img height="165" src="https://github-readme-stats.vercel.app/api/top-langs/?username=efebiskin&layout=compact&theme=tokyonight&hide_border=true&langs_count=8" alt="Top languages" />
  </a>
</p>

<p align="center">
  <img src="https://github-readme-streak-stats.herokuapp.com/?user=efebiskin&theme=tokyonight&hide_border=true" alt="GitHub streak" />
</p>

<p align="center">
  <img src="https://github-profile-trophy.vercel.app/?username=efebiskin&theme=tokyonight&no-frame=true&no-bg=true&margin-w=6&column=7" alt="GitHub trophies" />
</p>

---

## What I'm building

### 🧠 Autonomous ML Trading Platform
Ensemble-model trading system *(XGBoost + LightGBM + Random Forest, stacked, isotonic-calibrated)* with walk-forward cross-validation and time-series embargo to prevent look-ahead bias. After rigorous out-of-sample testing revealed the ensemble overfit, I pivoted to **two academic-backed alpha strategies** (insider-buying, post-earnings drift). Live backtest results:

| Strategy | Win Rate | Alpha vs S&P 500 | Sharpe | Sample |
|---|---|---|---|---|
| Insider-buy + momentum filter | **64.6%** | +3.31% | 1.21 | 164 trades, 3 years |
| Post-earnings drift | **65.5%** | +4.46% | 0.91 | 142 events, 3 years |

Production infra: Popen-based watchdog with exponential-backoff restart, Telegram `/panic` kill switch, daily performance digest, live-trading gate blocking real-money execution until thresholds met, 17-test pytest invariant suite, Flask dashboard integrating 9 data sources (SEC EDGAR, yfinance, FRED, Congressional disclosures, ARK, Google News, Reddit, Alpaca, in-house news-radar).

### 🌐 LFVI — Land Future Value Index
AI-powered real-estate investment intelligence. End-to-end ML pipeline ingesting **7+ U.S. government data APIs** (Census ACS, IRS, BLS, FRED, FEMA, Zillow), engineering **50+ features per county**, training **5 ensemble models** to score all 3,100+ U.S. counties. Extends down to individual parcels via APN polygon lookups with a Deal Analyzer that estimates max rational purchase price. Delivered as an interactive Dash choropleth dashboard with tract-level drilldown.

### 💪 Olympiq — Fitness Web App *(CSC499 Senior Capstone)*
Zero-install single-file web application (~214 KB HTML) with a **hand-rolled 208-line React-like runtime** (virtual DOM, hook system, event delegation) compiled from JSX via esbuild. **No framework dependencies.** Supabase auth + Postgres backend. Offline-capable.

### 🤖 HERA — Personal AI Assistant
Jarvis-style orchestration: Claude API (reasoning), Telegram Bot API (mobile), Obsidian vault (persistent memory across sessions), ElevenLabs (voice), Windows desktop avatar overlay.

### 🎮 BEF Games
Contributor to *The Boss Gangsters: Nightlife* on Steam. Ship features, patches, and trilingual localization (EN/TR/ES). Brokered the studio's publishing partnership with Tripwire Interactive.

---

## Tech

![Python](https://img.shields.io/badge/-Python-3776AB?style=flat&logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/-JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black)
![Java](https://img.shields.io/badge/-Java-007396?style=flat&logo=java&logoColor=white)
![C++](https://img.shields.io/badge/-C%2B%2B-00599C?style=flat&logo=c%2B%2B&logoColor=white)
![SQL](https://img.shields.io/badge/-SQL-4479A1?style=flat&logo=postgresql&logoColor=white)

![XGBoost](https://img.shields.io/badge/-XGBoost-EB5E28?style=flat)
![scikit-learn](https://img.shields.io/badge/-scikit--learn-F7931E?style=flat&logo=scikit-learn&logoColor=white)
![LightGBM](https://img.shields.io/badge/-LightGBM-0288D1?style=flat)
![pandas](https://img.shields.io/badge/-pandas-150458?style=flat&logo=pandas&logoColor=white)
![Claude](https://img.shields.io/badge/-Claude_API-D97757?style=flat)

![Flask](https://img.shields.io/badge/-Flask-000000?style=flat&logo=flask&logoColor=white)
![Dash](https://img.shields.io/badge/-Dash-008DE4?style=flat&logo=plotly&logoColor=white)
![Supabase](https://img.shields.io/badge/-Supabase-3ECF8E?style=flat&logo=supabase&logoColor=white)
![SQLite](https://img.shields.io/badge/-SQLite-003B57?style=flat&logo=sqlite&logoColor=white)
![pytest](https://img.shields.io/badge/-pytest-0A9EDC?style=flat&logo=pytest&logoColor=white)

---

## About me

- 🎓 **B.S. Computer Science**, Minor in Psychology — California Lutheran University (May 2026, 3.9 GPA)
- 📜 Certified in AI Engineering & Applied AI, Computer Hardware and Systems
- 🌍 Fluent in English, native Turkish, conversational Spanish
- 💼 Currently open to **AI / ML Engineer** and **Software Engineer** new-grad roles for 2026

---

## Let's connect

- 📧 [efebskn@gmail.com](mailto:efebskn@gmail.com)
- 💼 [LinkedIn](https://linkedin.com/in/efe-biskin-923397400)

*Project code is currently private — happy to walk through architecture, design decisions, or demo any of the above on request.*
