# Evaluator Agent Skill

## Purpose
Analyze the PR submission and score it against a comprehensive rubric.

## Input
- PR diff (from Watchdog)
- Challenge template type (junior or senior)
- PR metadata (title, description, commits)
- Candidate username
- Time taken (minutes)

## Process

### 1. Code Analysis
Parse the PR diff and analyze:
- Which files were changed
- What lines were modified
- Commit messages (one per commit)
- PR description quality

For junior challenge (calculate_stats):
- Check if off-by-one bug is fixed (average division)
- Check if comparison operator is fixed (max check)
- Check if null check is added (empty list handling)
- Verify no unintended changes to other functions
- Run mental test execution

For senior challenge (Flask /transfer):
- Check if balance is fetched and updated atomically OR with proper locking
- Check if user authentication is verified before transfer
- Check if the incorrect test is fixed AND if fixes are real
- Verify error handling for edge cases
- Check for potential race conditions in the fix

### 2. Scoring Rubric

Each dimension scored independently, then summed:

#### Correctness (0-30 points)
- **30:** All 3 bugs fixed, all tests pass, no regressions
- **25:** All 3 bugs fixed, all tests pass, minor style regression
- **20:** 2 bugs fixed completely, 1 partially, tests pass
- **15:** 2 bugs fixed, some tests failing
- **10:** 1 bug fixed, multiple test failures
- **5:** Partial fixes, tests mostly failing
- **0:** No bugs fixed or tests still failing

#### Code Quality (0-25 points)
- **25:** Fix is clean, reads naturally, no unnecessary changes, follows project style
- **20:** Fix works, minor style issues, perhaps one unnecessary line
- **15:** Fix works, some rough edges, inconsistent with project style
- **10:** Fix works but hacky, multiple style violations
- **5:** Very hacky, hard to read, but technically works
- **0:** Unreadable, unmaintainable, or violates security practices

#### Edge Case Handling (0-20 points)
- **20:** Thoughtful handling of nulls, empty/invalid inputs, boundary conditions, all tests pass
- **15:** Handles most edge cases, tests pass but coverage is narrow
- **10:** Handles happy path edge cases only, ignores some potential issues
- **5:** Limited edge case handling, brittle to variation
- **0:** No edge case consideration, crashes on edge inputs, or tests don't pass

#### Approach & Reasoning (0-15 points)
- **15:** Elegant solution that shows deep understanding, efficient, well-commented
- **12:** Solid fix that clearly understands the problem, straightforward approach
- **9:** Fix works but approach is naive, could be simpler
- **6:** Brute force fix, works but inelegant
- **3:** Random changes that happen to work, no clear reasoning
- **0:** Does not fix the problem, or approach is fundamentally flawed

#### Commit Clarity (0-10 points)
- **10:** Clear commit message(s) + detailed PR description explaining the fix
- **8:** Clear commit message, minimal PR description
- **6:** Adequate message, lacks detail or context
- **4:** Vague message like "fix bug", minimal context
- **2:** Unclear what the commit does
- **0:** No message or context

### 3. Verdict Logic

```
total_score = sum of all dimensions

if total_score >= 85:
    verdict = "strong hire"
    reasoning = "Demonstrated mastery. This engineer ships clean, thoughtful code under pressure."
elif total_score >= 75:
    verdict = "hire"
    reasoning = "Solid fundamentals. Would be productive on the team immediately."
elif total_score >= 60:
    verdict = "consider"
    reasoning = "Shows promise but has gaps. Could work with mentorship or specific growth areas."
else:
    verdict = "no hire"
    reasoning = "Does not meet bar for this role. Recommend revisiting after building more experience."
```

Adjust verdict based on context:
- If correctness < 20: Never "hire" or above, regardless of other scores
- If code_quality < 10: Never "strong hire"
- If edge_cases < 10 AND senior challenge: downgrade one level

### 4. Feedback Generation

Write 3-5 sentences of specific feedback:
- Cite exact lines from the diff where applicable
- Point out what was done well
- Highlight areas for improvement
- Be honest but constructive
- Do not flatter, do not be cruel

Examples:
- "The off-by-one fix on line 12 is correct, but the null check uses `if not numbers:` which shadows the return value. Consider `if len(numbers) == 0: return None` for clarity."
- "Strong atomic transaction fix on lines 34-38. However, the authentication check should happen before the balance query, not after. Currently, an unauthenticated user can still trigger the query."

## Output JSON

```json
{
  "username": "candidate",
  "challenge_template": "challenge_junior",
  "time_taken_minutes": 45,
  "submission_timestamp": "2026-05-23T15:15:00Z",
  "evaluation_timestamp": "2026-05-23T15:16:00Z",
  "pr_number": 3,
  "pr_url": "https://github.com/candidate/challenge_junior/pull/3",
  
  "rubric": {
    "correctness": {
      "score": 28,
      "max": 30,
      "reasoning": "All 3 bugs fixed. One minor regression in test output format, not functional."
    },
    "code_quality": {
      "score": 22,
      "max": 25,
      "reasoning": "Clean fix, follows project style. One extra variable that could be removed."
    },
    "edge_cases": {
      "score": 19,
      "max": 20,
      "reasoning": "Handles empty list, negative numbers, floats. Does not handle non-numeric input."
    },
    "approach": {
      "score": 14,
      "max": 15,
      "reasoning": "Clear, straightforward fixes. Shows understanding of the bugs."
    },
    "commit_clarity": {
      "score": 9,
      "max": 10,
      "reasoning": "Good commit messages. PR description could be more detailed."
    }
  },
  
  "score_breakdown": {
    "correctness": 28,
    "code_quality": 22,
    "edge_cases": 19,
    "approach": 14,
    "commit_clarity": 9,
    "total": 92
  },
  
  "verdict": "strong hire",
  "feedback": "Excellent submission. You identified all three bugs and fixed them cleanly. The null check on line 11 is particularly well done. One minor note: the max function comparison was fixed correctly, but consider adding a comment explaining why `>` was the right operator. Overall, this demonstrates solid problem-solving under time pressure."
}
```

## Output Actions

1. **Post PR Comment** with the formatted evaluation (see spec in main README)
2. **Close Issue** with a closing comment: "Challenge complete. Evaluation submitted."
3. **Save JSON Result** to `results/{username}_{timestamp}.json`
4. **Log** all decisions to stdout with clear formatting

## Error Handling
- If PR cannot be fetched: log error, output null evaluation, do not crash
- If diff parsing fails: log with detail, re-attempt with fallback parser
- If tests cannot be inferred: score lower on correctness but continue
- All errors are logged with timestamp for debugging

## Notes
- Evaluation is deterministic; same code input should always yield same score
- Verdicts are not subjective; they flow from the rubric
- Feedback must be specific and actionable, never generic
- If a candidate scores high on junior challenge: note that they could handle senior challenge
- If a candidate scores low on senior challenge: it does not necessarily mean junior challenge would be better (different problem domain)
