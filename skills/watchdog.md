# Watchdog Agent Skill

## Purpose
Poll the forked challenge repository for a Pull Request and enforce the 60-minute time window.

## Input
- Fork URL (from Challenge Setter)
- Issue number
- Creation timestamp
- Time limit in minutes (usually 60)

## Process

### 1. Polling Loop
- Poll the fork repo every 60 seconds: `GET /repos/{owner}/{repo}/pulls?state=open`
- Maximum 60 attempts (total 60 minutes)
- On each check, note the current time

### 2. PR Detection
When a PR is detected (open status, targetted at main/master branch):
- Extract: PR number, PR URL, title, description, creation timestamp
- Fetch the PR diff: `GET /repos/{owner}/{repo}/pulls/{number}/files`
- Parse the diff into a structured format
- Calculate time_taken_minutes from Issue creation to PR creation

### 3. Time Window Enforcement

**Three outcomes:**

A) **PR within window (time_taken <= 60 minutes)**
   - Status: "success"
   - Action: Trigger Evaluator Agent with PR data
   - Output and continue

B) **PR after window closes (time_taken > 60 minutes)**
   - Status: "timeout"
   - Action: Post comment on the PR: "This PR was opened after the 60-minute window. Evaluation halted."
   - Close the Issue with comment: "Time limit exceeded. Challenge failed."
   - Output timeout result, do not proceed to evaluation

C) **No PR in 60 minutes (60 attempts exhausted)**
   - Status: "no_submission"
   - Action: Close the Issue with comment: "60 minutes have elapsed with no PR submission. Challenge incomplete."
   - Output result, do not proceed to evaluation

### 4. PR Validation

Before handing to Evaluator, check:
- PR has at least one commit
- PR has a non-empty title and/or description
- PR is targetted at main/master (not a draft or random branch)

If validation fails:
- Post comment: "Invalid PR format. Please ensure: PR has commits, PR has description, PR targets main branch."
- Continue polling (do not fail, give them more time)

## Output JSON

```json
{
  "pr_number": 3,
  "pr_url": "https://github.com/candidate/challenge_junior/pull/3",
  "pr_title": "Fix calculate_stats bugs",
  "pr_description": "Fixed off-by-one error in average, wrong operator in max check, and added null check for empty list",
  "pr_created_at": "2026-05-23T15:15:00Z",
  "time_taken_minutes": 45,
  "commit_count": 2,
  "files_changed": 2,
  "additions": 15,
  "deletions": 8,
  "status": "success",
  "pr_diff": "... (full diff text) ...",
  "ready_for_evaluation": true
}
```

### Timeout Output JSON

```json
{
  "status": "timeout",
  "time_elapsed_minutes": 61,
  "time_limit_minutes": 60,
  "pr_detected": false,
  "issue_number": 1,
  "failure_reason": "No PR submission within 60-minute window",
  "ready_for_evaluation": false
}
```

## Error Handling
- API errors (5xx): log and retry after 60 seconds
- Rate limit (429): back off exponentially, max 5 retries
- Invalid repo state: log clearly and fail with explanation
- Network timeouts: retry logic with jitter

## Logging
Every poll cycle should log:
- [HH:MM:SS] Polling /repos/{owner}/{repo}/pulls...
- If PR found: [HH:MM:SS] PR #{number} detected at T+{minutes}min
- If timeout: [HH:MM:SS] 60 minutes elapsed. No submission. Closing challenge.

## Notes
- The Watchdog runs independently and does not block other operations
- If multiple PRs exist, use the first one opened (earliest created_at)
- Whitespace changes are ignored in the diff for evaluation purposes
- The Watchdog is responsible for time enforcement; the Evaluator trusts the time_taken_minutes field
