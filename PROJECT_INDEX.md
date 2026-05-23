# GitAgent Interviewer - Project Index

## Complete Project Delivery

This document indexes all files created for GitAgent Interviewer, a complete multi-agent autonomous technical interviewer system.

**Status:** ✓ COMPLETE - All 21 core files + supporting files created
**Date:** 2026-05-23
**Version:** 1.0.0

---

## File Manifest

### Configuration & Standards
- ✓ `agent.yaml` (20 lines) - GitAgent configuration per open standard
- ✓ `SOUL.md` (45 lines) - Agent values, ethics, and decision-making philosophy
- ✓ `RULES.md` (95 lines) - Operational rules and policies for fair evaluation
- ✓ `.env.example` (13 lines) - Environment variable template
- ✓ `.gitignore` (33 lines) - Git ignore patterns
- ✓ `LICENSE` (21 lines) - MIT License

### Documentation
- ✓ `README.md` (320 lines) - User guide, setup, examples
- ✓ `TECHNICAL_GUIDE.md` (450 lines) - Deep dive architecture and implementation
- ✓ `PROJECT_INDEX.md` (this file) - Complete file manifest

### Skills (Agent Definitions)
- ✓ `skills/profile.md` (115 lines) - Profile Agent skill definition
- ✓ `skills/challenge.md` (130 lines) - Challenge Setter skill definition
- ✓ `skills/watchdog.md` (115 lines) - Watchdog Agent skill definition
- ✓ `skills/evaluator.md` (265 lines) - Evaluator Agent skill definition

### Tools (Python Implementation)
- ✓ `tools/__init__.py` (1 line) - Package marker
- ✓ `tools/github_api.py` (320 lines) - GitHub API client with error handling
- ✓ `tools/poll_pr.py` (120 lines) - PR polling and watchdog logic
- ✓ `tools/scorer.py` (520 lines) - Comprehensive evaluation rubric implementation

### Challenge Templates
- ✓ `templates/challenge_junior/main.py` (45 lines) - Buggy Python stats function
- ✓ `templates/challenge_junior/test_main.py` (75 lines) - Tests exposing bugs
- ✓ `templates/challenge_junior/conftest.py` (5 lines) - Test configuration
- ✓ `templates/challenge_senior/app.py` (85 lines) - Buggy Flask API endpoint
- ✓ `templates/challenge_senior/test_app.py` (105 lines) - Tests exposing bugs
- ✓ `templates/challenge_senior/conftest.py` (5 lines) - Test configuration

### Memory & Hooks
- ✓ `memory/candidates.md` (22 lines) - Candidate history template
- ✓ `hooks/on_session_end.py` (95 lines) - Session completion handler

### Entry Points & Scripts
- ✓ `main.py` (750 lines) - CLI entry point, orchestrates full pipeline
- ✓ `demo.py` (280 lines) - Demo script with formatted output
- ✓ `quickstart.py` (70 lines) - Quick setup verification
- ✓ `setup.sh` (50 lines) - Linux/Mac setup script
- ✓ `setup.bat` (50 lines) - Windows setup script

### Dependencies
- ✓ `requirements.txt` (7 lines) - Python package requirements

### Directories
- ✓ `skills/` - Created and populated
- ✓ `tools/` - Created and populated
- ✓ `templates/` - Created and populated
- ✓ `templates/challenge_junior/` - Created and populated
- ✓ `templates/challenge_senior/` - Created and populated
- ✓ `memory/` - Created and populated
- ✓ `hooks/` - Created and populated
- ✓ `results/` - Created (for output files)

---

## Total Lines of Code

| Category | Files | Lines | Language |
|----------|-------|-------|----------|
| Configuration | 6 | ~230 | YAML/Markdown |
| Documentation | 3 | ~770 | Markdown |
| Skills | 4 | ~625 | Markdown |
| Tools | 4 | ~960 | Python |
| Templates | 6 | ~310 | Python |
| Memory/Hooks | 2 | ~117 | Python/Markdown |
| Entry Points | 5 | ~1,200 | Python/Shell |
| **TOTAL** | **30** | **~4,212** | |

---

## 4-Agent Pipeline Summary

### Agent 1: Profile Agent
**Purpose:** Analyze GitHub user history and determine skill level
**Technology:** GitHub REST API, profile analysis
**Output:** Candidate profile JSON with skill level (junior/mid/senior)

### Agent 2: Challenge Setter Agent
**Purpose:** Create challenge repository and GitHub Issue
**Technology:** GitHub fork API, issue creation
**Output:** Challenge configuration with fork URL and issue number

### Agent 3: Watchdog Agent
**Purpose:** Poll for PR submission and enforce 60-minute timeout
**Technology:** GitHub PR polling, timestamp validation
**Output:** PR data with submission time, or timeout result

### Agent 4: Evaluator Agent
**Purpose:** Score PR against comprehensive rubric
**Technology:** Diff analysis, scoring heuristics, feedback generation
**Output:** Evaluation JSON with verdict, score breakdown, and feedback

---

## Challenge Templates

### Template A: Python `calculate_stats` (Junior/Mid)
- **Bugs:** 3 intentional (off-by-one, wrong operator, no null check)
- **Tests:** 6 test cases
- **Expected time:** 15-30 minutes

### Template B: Flask `/transfer` API (Senior)
- **Bugs:** 3 intentional (race condition, missing auth, broken test)
- **Tests:** 7 test cases
- **Expected time:** 30-45 minutes

---

## Setup Quick Start

```bash
# 1. Clone
git clone https://github.com/lyzr-ai/gitagent-interviewer.git
cd gitagent-interviewer

# 2. Install
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add GITHUB_TOKEN

# 3. Test
python quickstart.py

# 4. Run demo
python demo.py

# 5. Run interview
python main.py <github_username>
```

---

## Running the System

### Demo Mode (Recommended for Testing)
```bash
python demo.py [username]
```
- Uses 10-second polling interval
- Shows all agent outputs
- Perfect for demonstration/screencast

### Production Mode
```bash
python main.py <github_username>
```
- Full 60-minute time window
- Real 60-second polling interval
- Saves results to `results/` directory

---

## Evaluation Rubric

**Correctness (0-30):** Did all bugs get fixed? Tests passing?
**Code Quality (0-25):** Clean code? Follows project style?
**Edge Cases (0-20):** Handles nulls, boundaries, errors?
**Approach (0-15):** Elegant solution? Shows understanding?
**Commit Clarity (0-10):** Clear messages? Good PR description?

**Verdicts:**
- **85-100:** strong hire
- **75-84:** hire
- **60-74:** consider
- **<60:** no hire

---

## Key Features

✓ Fully autonomous - zero human intervention required
✓ Real GitHub integration - actual pull requests and issues
✓ Strict time enforcement - exactly 60 minutes, no exceptions
✓ Objective rubric - same evaluation criteria for all candidates
✓ Detailed feedback - specific, actionable comments on PRs
✓ Reproducible - all decisions logged and saved as JSON
✓ GitAgent compliant - follows open GitAgent/GitClaw standards
✓ Production-ready - error handling, logging, retry logic
✓ Configurable - easy to modify templates, rubric, time limits

---

## Testing

```bash
# Run challenge tests
cd templates/challenge_junior
pytest test_main.py -v

cd ../challenge_senior
pytest test_app.py -v

# Test the interviewer itself
python quickstart.py    # Verifies setup
python demo.py          # Full end-to-end test
```

---

## Files Summary

```
gitagent-interviewer/
├── agent.yaml                          # GitAgent config
├── SOUL.md                             # Agent philosophy
├── RULES.md                            # Operational rules
├── README.md                           # User guide
├── TECHNICAL_GUIDE.md                  # Architecture details
├── LICENSE                             # MIT License
├── .gitignore                          # Git ignore
├── requirements.txt                    # Dependencies
├── .env.example                        # Config template
├── 
├── main.py                             # CLI entry point
├── demo.py                             # Demo script
├── quickstart.py                       # Setup checker
├── setup.sh                            # Linux setup
├── setup.bat                           # Windows setup
├── 
├── skills/
│   ├── profile.md                      # Profile agent
│   ├── challenge.md                    # Challenge setter
│   ├── watchdog.md                     # Watchdog agent
│   └── evaluator.md                    # Evaluator agent
├── 
├── tools/
│   ├── __init__.py
│   ├── github_api.py                   # GitHub client
│   ├── poll_pr.py                      # PR watchdog
│   └── scorer.py                       # Evaluation engine
├── 
├── templates/
│   ├── challenge_junior/
│   │   ├── main.py                     # Buggy code
│   │   ├── test_main.py                # Tests
│   │   └── conftest.py
│   └── challenge_senior/
│       ├── app.py                      # Buggy API
│       ├── test_app.py                 # Tests
│       └── conftest.py
├── 
├── memory/
│   └── candidates.md                   # Candidate history
├── 
├── hooks/
│   └── on_session_end.py               # Session handler
└── 
└── results/                            # Output directory
    ├── {username}_{timestamp}.json
    ├── {username}_{timestamp}_evaluation.json
    └── {username}_{timestamp}_logs.txt
```

---

## Next Steps

1. **Setup:** Follow instructions in `README.md`
2. **Run Demo:** `python demo.py` to see the system in action
3. **Try It:** `python main.py <github_username>` for real interview
4. **Customize:** Modify templates and rubric as needed
5. **Deploy:** Use in hiring pipeline or evaluation system

---

## Support & Contribution

- See `TECHNICAL_GUIDE.md` for implementation details
- See `skills/` directory for agent definitions
- See `tools/` directory for Python implementation
- Create new templates in `templates/` directory
- Modify rubric in `tools/scorer.py`

---

## Standards Compliance

✓ GitAgent 1.0 standard
✓ GitClaw 1.0 standard
✓ GitHub API v3
✓ Python 3.11+
✓ PEP 8 style guidelines

---

**Built with Claude + Lyzr AI | Open GitAgent Standard | May 2026**
