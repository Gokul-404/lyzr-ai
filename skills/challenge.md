# Challenge Setter Agent Skill

## Purpose
Select and configure a challenge template based on candidate skill level, fork it to their namespace, and open a GitHub Issue with clear instructions.

## Input
- Candidate profile JSON (from Profile Agent)
- GitHub username

## Process

### 1. Template Selection
Read `skill_level` from candidate profile:
- **"junior" or "mid"** → Use **Template A** (Python: `calculate_stats` with 3 bugs)
- **"senior"** → Use **Template B** (Flask API: `/transfer` endpoint with 3 bugs)

### 2. Fork Repository
- Determine source template repo path based on skill level
- Use GitHub API: `POST /repos/{owner}/{repo}/forks`
- Target: fork into candidate's namespace
- Extract fork URL and repo

### 3. Open GitHub Issue
In the newly forked repo, create Issue with:
- **Title:** "Your mission: find and fix the bugs"
- **Body:** Use the GitHub Issue template (see main spec)
- **Labels:** "challenge", "interview", "60-minute-deadline"
- **Assignee:** The candidate (if possible)
- Extract: issue_number, creation_timestamp

### 4. Initialize Challenge Config
Create or update a `.challenge.json` file in the repo root:

```json
{
  "challenge_id": "uuid",
  "template": "challenge_junior|challenge_senior",
  "username": "candidate_username",
  "issue_number": 1,
  "issue_created_at": "2026-05-23T14:30:00Z",
  "time_limit_minutes": 60,
  "expected_tests": ["test_calculate_stats", "test_handle_empty_list"],
  "bugs_to_fix": 3,
  "status": "waiting_for_pr"
}
```

## Output JSON

```json
{
  "fork_url": "https://github.com/candidate/challenge_junior",
  "fork_owner": "candidate",
  "fork_name": "challenge_junior",
  "issue_number": 1,
  "issue_url": "https://github.com/candidate/challenge_junior/issues/1",
  "challenge_template": "challenge_junior",
  "time_limit_minutes": 60,
  "creation_timestamp": "2026-05-23T14:30:00Z",
  "expected_bugs": 3,
  "status": "ready"
}
```

## Challenge Templates

### Template A (Junior/Mid): Python `calculate_stats`

**Repo Name:** `gitagent-challenge-junior`

**Files:**
- `main.py` - Broken implementation with 3 bugs
- `test_main.py` - Tests that expose the bugs
- `README.md` - Clear problem statement

**Bugs:**
1. **Off-by-one:** Average calculation divides by `len(numbers) + 1` instead of `len(numbers)`
2. **Wrong operator:** Finding max uses `<` instead of `>` in comparison
3. **No null check:** Function crashes on empty list instead of returning None or raising

**Test requirements:** All 3 must pass for a complete fix.

### Template B (Senior): Flask API with `/transfer` Endpoint

**Repo Name:** `gitagent-challenge-senior`

**Files:**
- `app.py` - Flask app with /transfer endpoint
- `test_app.py` - Tests (some correctly mock, some are broken)
- `requirements.txt` - Flask, pytest, pytest-mock
- `README.md` - Clear problem statement

**Bugs:**
1. **Race condition:** Reads balance from database, then writes without atomic transaction (two separate queries)
2. **Missing auth:** `/transfer` endpoint does not verify that requester owns the source account
3. **Broken test:** A test is mocked incorrectly (always passes even when bug exists)

**Test requirements:** All tests must pass AND the fixes must be real (not just fixing the test).

## Error Handling
- If fork fails (repo already exists): detect and reuse existing fork, update .challenge.json
- If Issue creation fails: log error, but do not halt (Watchdog will detect repo state)
- If .challenge.json cannot be written: log and continue (non-critical)
- Rate limit handling: exponential backoff

## Notes
- The fork is public so the candidate can clone it
- All instructions are in the GitHub Issue, not in code comments
- The candidate must read the Issue to understand what they're fixing
- Challenge repos are read-only to everyone except the fork owner
