# GitAgent Interviewer — Rules of Operation

## Pipeline Rules

### Rule 1: One Challenge Per Candidate, One PR Per Challenge
Each candidate gets exactly one forked repo and one attempt. Multiple PRs are ignored; only the first counts. If they close it and open a new one, the system halts — they already got their shot.

### Rule 2: Time Window is Absolute
From the moment the GitHub Issue is created, 60 minutes start. Not "60 minutes from when they notice" — from creation. The Watchdog Agent enforces this strictly. At 60 minutes + 1 second, the evaluation window closes. New commits after that point are not evaluated.

### Rule 3: All Tests Must Pass
If a single test fails in the repository, the evaluation stops there. Partial fixes do not count. The rubric assumes a baseline of "code that runs without errors."

### Rule 4: No Scaffolding, Only Bugs
The challenge repos have one job: expose specific bugs the candidate must fix. The repos do not have:
- Misleading comments
- Red herrings
- Syntax errors (only logic bugs)
- Dependencies they don't understand
- Ambiguous requirements

### Rule 5: Score Independently, Evaluate Together
Each dimension is scored independently (0-30 for correctness, etc.). The final verdict is not mechanical — it considers context:
- A junior who scores 72 with clean code is a stronger signal than a senior who scores 72 with clever hacks.
- But the rubric itself is the same.

### Rule 6: Log Everything
Every API call, every timeout, every parse error gets logged with a timestamp. If evaluation fails, someone should be able to replay it.

### Rule 7: Graceful Degradation
If the GitHub API goes down mid-challenge, the system logs it, waits 30 seconds, and retries. It does not spam the API. It does not fail silently.

### Rule 8: No Pre-Baked Verdicts
The verdict is computed from the score, not the other way around. Do not read a candidate's GitHub profile and predetermine a verdict. Score the submission first, then judge.

---

## Interaction Rules

### For the Candidate
- You have 60 minutes from Issue creation.
- You can view the code, run tests locally, think, and ship one PR.
- Your commit message is part of the evaluation — explain your fix.
- No copy-paste solutions. We can tell.

### For the System
- Post one evaluation comment per PR.
- Be honest and specific.
- Do not re-open the Issue.
- Do not comment outside the PR thread.
- Log all results to `results/{username}_{timestamp}.json`.

---

## Scoring Rules

Each dimension is scored as a range, not binary:

- **Correctness (0-30):** 30 = all bugs fixed, no regressions. 15 = some bugs fixed, some regressions. 0 = no bugs fixed or all tests fail.
- **Code Quality (0-25):** 25 = reads like it was always there, no cleanup needed. 12 = works but has some rough edges. 0 = unreadable, hacky, violates project style.
- **Edge Cases (0-20):** 20 = thoughtful handling of nulls, bounds, invalid input. 10 = handles the happy path only. 0 = crashes on edge cases or ignores them entirely.
- **Approach (0-15):** 15 = elegant solution that shows understanding of the problem. 8 = straightforward fix that works. 0 = brute force, or no clear reasoning.
- **Commit Clarity (0-10):** 10 = clear message + description in PR. 5 = short message with no context. 0 = "fix bug" with no explanation.

---

*These rules are not negotiable. They exist so candidates trust the process and so you stay honest.*
