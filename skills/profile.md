# Profile Agent Skill

## Purpose
Analyze a GitHub username and build a structured candidate profile by querying public GitHub data.

## Input
- GitHub username (string)

## Process

1. **Fetch Public Repositories**
   - Use `GET /users/{username}/repos?sort=updated&per_page=100`
   - Extract: repo names, stars, language breakdown, last updated date
   - Look for active repos in the last 12 months

2. **Analyze Commit History**
   - For top 5 repos, fetch commit history
   - Count commits in last 6 months, last month
   - Estimate contribution frequency (daily/weekly/sporadic)
   - Look for consistency patterns

3. **Extract Tech Stack**
   - Identify primary languages (by commit count, not just repo count)
   - Identify frameworks/tools used (from repo names, files, package managers)
   - Flag if candidate is polyglot vs. single-language

4. **Assess PR Activity**
   - Fetch recent PRs as author
   - Look for collaborative behavior: do they review others' code?
   - Estimated skill level based on repo complexity + activity

5. **Determine Skill Level**

   **Junior signals:**
   - < 6 months consistent GitHub history
   - Mostly tutorial repos or coursework
   - Few commits to established projects
   - Limited language diversity (1-2 languages)
   - Low PR activity

   **Mid signals:**
   - 1-3 years active history
   - Mix of personal projects and contributions to others' repos
   - 2-4 languages regularly used
   - Some PR activity, shows code review understanding
   - Projects are non-trivial (API, library, tool)

   **Senior signals:**
   - 3+ years sustained activity
   - Significant contributions to well-known projects
   - Comfortable in 3+ languages
   - Active reviewer/mentor (PRs to other repos)
   - Projects are architecturally sophisticated (frameworks, distributed systems)
   - Leadership in repo (issue triage, release management)

## Output JSON

```json
{
  "username": "octocat",
  "skill_level": "mid",
  "top_languages": ["Python", "JavaScript", "Go"],
  "frameworks": ["Flask", "React", "gRPC"],
  "activity_score": 0.85,
  "repos_analyzed": 5,
  "public_repos_count": 23,
  "estimated_years_experience": 2.5,
  "last_commit": "2026-05-22T14:32:00Z",
  "contribution_frequency": "weekly",
  "summary": "Mid-level full-stack engineer, most active in Python and JavaScript. Regular contributor, last active 1 day ago. Shows interest in backend systems and testing."
}
```

## Error Handling
- If user not found: return error with HTTP 404
- If user has no public repos: return skill_level = "unknown", summary = "No public history available"
- If API rate limited: wait 60 seconds and retry
- Log all API calls with timestamp

## Notes
- Skill level is inferred, not definitive. The challenge will confirm.
- Activity score ranges 0.0 to 1.0 (frequency of commits in last month vs. historical baseline)
- This agent does not make a hiring decision. It informs the Challenge Setter which template to use.
