# GitAgent Interviewer Technical Guide

## System Overview

GitAgent Interviewer is a fully autonomous multi-agent system that evaluates engineers through live technical interviews conducted entirely on GitHub. The system requires zero human intervention once started — it profiles candidates, creates challenge repositories, enforces time limits, scores submissions, and posts detailed feedback all autonomously.

## Architecture

### Four-Agent Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                     GitHub Candidate                                 │
│  (forks repo, reads issue, submits PR with code fix)                 │
└────────────┬──────────────────────────────────────────────────────┬──┘
             │                                                        │
             │ Step 1: Fetch Profile                                 │
             │                                                        │
    ┌────────▼────────────────────────────────────────────────────┐  │
    │ PROFILE AGENT                                                │  │
    │  • Fetches user repos, commit history                        │  │
    │  • Extracts languages, frameworks, activity                  │  │
    │  • Infers skill level (junior/mid/senior)                   │  │
    │  • Output: Candidate profile JSON                            │  │
    └────────┬─────────────────────────────────────────────────────┘  │
             │                                                        │
             │ Step 2: Create Challenge                              │
             │                                                        │
    ┌────────▼─────────────────────────────────────────────────────┐ │
    │ CHALLENGE SETTER AGENT                                        │ │
    │  • Selects template based on skill level                      │ │
    │  • Forks challenge repo to candidate namespace                │ │
    │  • Creates GitHub Issue with task description                 │ │
    │  • Starts 60-minute timer                                     │ │
    │  • Output: Challenge configuration JSON                       │ │
    └────────┬──────────────────────────────────────────────────────┘ │
             │                                                        │
             │ Step 3: Poll for Submission                            │
             │  (every 60 seconds)                                    │
             │                                                        │
    ┌────────▼──────────────────────────────────────────────────────┐ │
    │ WATCHDOG AGENT                                                 │ │
    │  • Polls fork for open PRs                                     │ │
    │  • Enforces 60-minute time window strictly                     │ │
    │  • Fetches PR diff and metadata                                │ │
    │  • Output: PR data or timeout result                           │ │
    └────────┬──────────────────────────────────────────────────────┘ │
             │                                                        │
             │ Step 4: Score & Evaluate                               │
             │                                                        │
    ┌────────▼──────────────────────────────────────────────────────┐ │
    │ EVALUATOR AGENT                                                │ │
    │  • Analyzes PR diff against rubric                             │ │
    │  • Scores: correctness, quality, edge cases, approach, clarity │ │
    │  • Generates verdict: strong hire / hire / consider / no hire  │ │
    │  • Posts formatted comment to PR                               │ │
    │  • Output: Evaluation JSON + PR comment                        │ │
    └────────┬──────────────────────────────────────────────────────┘ │
             │                                                        │
             │                                                        │
    ┌────────▼──────────────────────────────────────────────────────┐ │
    │ RESULTS                                                        │ │
    │ • results/{username}_{timestamp}.json                          │ │
    │ • results/{username}_{timestamp}_evaluation.json               │ │
    │ • results/{username}_{timestamp}_logs.txt                      │ │
    └───────────────────────────────────────────────────────────────┘ │
             │                                                        │
             └────────────────────────────────────────────────────────┘
```

## Component Details

### Profile Agent (`tools/github_api.py` + `skills/profile.md`)

**Input:** GitHub username (string)

**Process:**
1. Fetch user's public repositories using GitHub REST API
2. Analyze programming languages used
3. Extract frameworks and tools
4. Calculate activity score (commits in last 30 days vs historical)
5. Estimate years of experience
6. Determine skill level

**Skill Level Inference:**
- **Junior:** <6 months consistent activity, mostly personal projects
- **Mid:** 1-3 years, mix of personal and open-source, 2-4 languages
- **Senior:** 3+ years, significant contributions, 3+ languages, architectural complexity

**Output:**
```json
{
  "username": "torvalds",
  "skill_level": "senior",
  "top_languages": ["C", "Shell", "Python"],
  "frameworks": [],
  "activity_score": 0.45,
  "estimated_years_experience": 30.5
}
```

### Challenge Setter Agent (`tools/github_api.py` + `skills/challenge.md`)

**Input:** Candidate profile JSON

**Process:**
1. Select template based on `skill_level`:
   - Junior/Mid → Template A (Python: `calculate_stats`)
   - Senior → Template B (Flask: `/transfer` endpoint)
2. Fork source template repo to candidate's GitHub namespace
3. Create GitHub Issue with:
   - Task description
   - Acceptance criteria
   - 60-minute deadline
   - Rules (one PR only, no copy-paste, etc.)
4. Store challenge metadata in `.challenge.json`

**Output:**
```json
{
  "fork_url": "https://github.com/torvalds/gitagent-challenge-senior",
  "issue_number": 1,
  "challenge_template": "challenge_senior",
  "time_limit_minutes": 60,
  "status": "ready"
}
```

### Watchdog Agent (`tools/poll_pr.py` + `skills/watchdog.md`)

**Input:** Fork URL, issue number, issue creation timestamp

**Process:**
1. Poll fork repository every 60 seconds: `GET /repos/{owner}/{repo}/pulls?state=open`
2. On PR detected:
   - Extract PR number, URL, title, body
   - Fetch full diff
   - Calculate time taken from issue creation
3. Enforce time window:
   - If `time_taken ≤ 60 minutes` → success, pass to evaluator
   - If `time_taken > 60 minutes` → timeout, close issue, fail
   - If no PR after 60 minutes → no submission, close issue, fail

**Output:**
```json
{
  "pr_number": 3,
  "pr_url": "https://github.com/torvalds/gitagent-challenge-senior/pull/3",
  "time_taken_minutes": 45,
  "status": "success",
  "pr_diff": "... unified diff ..."
}
```

### Evaluator Agent (`tools/scorer.py` + `skills/evaluator.md`)

**Input:** PR diff, challenge template type, candidate username, time taken

**Process:**
1. Parse PR diff and analyze changes
2. Score each dimension:
   - **Correctness (0-30):** Did all bugs get fixed? Tests passing?
   - **Code Quality (0-25):** Clean, readable? Follows project style?
   - **Edge Cases (0-20):** Handles nulls, boundaries, errors?
   - **Approach (0-15):** Elegant or brute force? Shows understanding?
   - **Commit Clarity (0-10):** Clear messages? Good PR description?
3. Calculate total score (0-100)
4. Generate verdict based on score:
   - 85-100: "strong hire"
   - 75-84: "hire"
   - 60-74: "consider"
   - <60: "no hire"
5. Write specific, actionable feedback
6. Post formatted comment to PR
7. Close GitHub Issue

**Output:**
```json
{
  "verdict": "strong hire",
  "score_breakdown": {
    "correctness": 28,
    "code_quality": 22,
    "edge_cases": 19,
    "approach": 14,
    "commit_clarity": 9,
    "total": 92
  },
  "feedback": "Excellent submission..."
}
```

## Challenge Templates

### Template A: Python `calculate_stats` (Junior/Mid)

**File:** `templates/challenge_junior/`

**Bugs:**
1. **Off-by-one in average:** Divides by `len(numbers) + 1` instead of `len(numbers)`
2. **Wrong operator in max:** Uses `<` instead of `>` when finding max value
3. **No null check:** Function crashes on empty list

**Tests:** `test_main.py` — 6 test cases that expose all 3 bugs

**Expected Fix Time:** 15-30 minutes

### Template B: Flask `/transfer` Endpoint (Senior)

**File:** `templates/challenge_senior/`

**Bugs:**
1. **Race condition:** Reads balance then updates without atomic transaction (two separate DB queries)
2. **Missing authentication:** No check that requester owns the source account
3. **Broken test:** Test is incorrectly mocked and always passes even when bugs exist

**Tests:** `test_app.py` — Tests that expose all 3 issues

**Expected Fix Time:** 30-45 minutes

## Data Flow & Logging

### File Structure
```
results/
├── {username}_{timestamp}.json              # Full pipeline result
├── {username}_{timestamp}_evaluation.json   # Detailed evaluation
└── {username}_{timestamp}_logs.txt          # All API calls & decisions
```

### Session JSON Structure
```json
{
  "session_id": "abc12345",
  "username": "torvalds",
  "start_time": "2026-05-23T14:30:00Z",
  "end_time": "2026-05-23T15:30:00Z",
  "profile": { ... },
  "challenge": { ... },
  "watchdog_result": { ... },
  "evaluation": {
    "verdict": "strong hire",
    "score_breakdown": { ... },
    "feedback": "..."
  },
  "github_logs": [ ... ]
}
```

## Error Handling

### GitHub API Errors
- **404 (User not found):** Profile Agent fails gracefully, logs error
- **403 (Permission denied):** Usually fork permissions — log and continue
- **429 (Rate limited):** Exponential backoff, max 5 retries
- **5xx (Server error):** Log and retry after 60 seconds

### Time Window Enforcement
- No flexibility: exactly 60 minutes from issue creation timestamp
- If PR is 1 second late, it's late — marks as "no hire"
- Prevents candidates from exploiting timezone edge cases

### Test Failures
- If any test fails in the forked repo, scoring reflects it
- Evaluator does not assume "tests pass" — analyzes diff for evidence

## Security Considerations

### What the System Does NOT Do
- Does not execute code (only parses diffs)
- Does not send code to external services
- Does not store code locally beyond evaluation period
- Does not scan for vulnerabilities (only diff analysis)
- Does not modify candidate's code (only reads it)

### What the System DOES Protect
- GitHub Personal Access Token (kept in `.env`, never logged)
- Google Gemini API Key (kept in `.env`, never logged)
- Candidate's full repository is only read when necessary

## Performance & Scalability

### Single Interview
- **Profile Agent:** 2-5 seconds (GitHub API calls)
- **Challenge Setter:** 5-10 seconds (fork + issue creation)
- **Watchdog Agent:** 3600 seconds max (60 minutes of polling)
- **Evaluator Agent:** 2-3 seconds (diff parsing + scoring)
- **Total:** 60+ minutes (dominated by watchdog waiting)

### Polling Efficiency
- Polls every 60 seconds (configurable)
- Each poll is single API call (~100ms)
- Total API calls for full timeout: ~60 calls
- Well within GitHub's 5000/hour rate limit

### Concurrent Interviews
- Multiple instances can run independently
- Each maintains separate `.challenge.json` in its fork
- No shared state except GitHub (which handles concurrency)
- Scalable to hundreds of concurrent interviews

## Customization

### Adding New Challenge Templates
1. Create `templates/challenge_xxx/` directory
2. Add `main.py` (or `app.py`) with intentional bugs
3. Add `test_xxx.py` with tests that expose bugs
4. Update Challenge Setter to recognize template
5. Update Evaluator rubric if needed

### Modifying the Rubric
Edit `tools/scorer.py`:
- Change max points for each dimension
- Adjust verdict thresholds
- Modify feedback generation logic

### Adjusting Time Limits
Edit `skills/challenge.md` and `tools/poll_pr.py`:
- `time_limit_minutes: 60` → change to desired limit
- Polling interval in `poll_pr.py`: 60 seconds → adjust

## Testing & Development

### Run the Demo
```bash
python demo.py [username]
```
Uses a 10-second polling interval for quick testing. Shows all agent outputs.

### Run a Single Interview
```bash
python main.py <github_username>
```
Runs full 60-minute pipeline (or exits earlier if PR submitted).

### Run Unit Tests
```bash
pytest templates/challenge_junior/test_main.py -v
pytest templates/challenge_senior/test_app.py -v
```

### Local Testing Without GitHub
Edit `main.py` to mock GitHub API calls for local development.

## Monitoring & Debugging

### Logs
All operations are logged with timestamps:
```
[2026-05-23T14:30:00Z] INFO: Fetching profile for @torvalds
[2026-05-23T14:30:01Z] INFO: Found 47 public repos
[2026-05-23T14:30:05Z] INFO: Forking gitagent-challenge-senior...
```

### API Call Tracing
Every GitHub API call is logged:
```
[2026-05-23T14:30:05Z] INFO: POST https://api.github.com/repos/lyzr/gitagent-challenge-senior/forks
[2026-05-23T14:30:06Z] INFO: Response: 202 Created
```

### Error Investigation
Check `results/{username}_*_logs.txt` for full trace of what happened.

## Compliance & Standards

### GitAgent/GitClaw Compliance
- `agent.yaml` — Valid GitAgent 1.0 format
- `SOUL.md` — Agent values and decision-making principles
- `RULES.md` — Operational rules and policies
- `skills/` — Skill definitions (markdown)
- `tools/` — Tool implementations (Python)
- `memory/` — Persistent state (markdown)

### GitHub API Compliance
- Uses PyGithub library (official client)
- Respects rate limits
- Uses Personal Access Token (standard auth)
- Logs all API calls

### Ethical Considerations
- Fair evaluation: same rubric for everyone
- Transparent: feedback is specific and actionable
- Reproducible: all decisions are logged
- Non-discriminatory: evaluated only on code ability

---

**Technical Contact:** GitHub Issues
**Standards:** Open GitAgent + GitHub API v3
**Last Updated:** 2026-05-23
