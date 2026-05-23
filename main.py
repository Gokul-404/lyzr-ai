"""
GitAgent Interviewer - Main entry point.

Orchestrates the 4-agent pipeline:
1. Profile Agent - Build candidate profile from GitHub
2. Challenge Setter - Create forked challenge repo and GitHub Issue
3. Watchdog Agent - Poll for PR submission with 60-min timeout
4. Evaluator Agent - Score PR submission

Usage:
    python main.py <github_username>
"""

import sys
import os
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from tools.github_api import GitHubClient
from tools.poll_pr import PRWatchdog
from tools.scorer import SubmissionScorer


def get_env(key: str, default: str = "") -> str:
    """Get environment variable safely."""
    value = os.getenv(key, default)
    if not value:
        raise ValueError(f"Missing environment variable: {key}")
    return value


def load_env():
    """Load environment variables from .env file."""
    from dotenv import load_dotenv
    load_dotenv()
    
    # Verify required environment variables
    required_keys = ["GITHUB_TOKEN", "GEMINI_API_KEY", "GITHUB_USERNAME"]
    missing = [key for key in required_keys if not os.getenv(key)]
    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}")
        print("Please set these in your .env file")
        sys.exit(1)


def profile_agent(github_client: GitHubClient, username: str) -> Dict[str, Any]:
    """
    AGENT 1: Profile Agent
    
    Analyzes GitHub user and determines skill level.
    Returns candidate profile for Challenge Setter.
    """
    print("\n" + "="*60)
    print("AGENT 1: PROFILE AGENT")
    print("="*60)
    
    profile_data = github_client.get_user_profile(username)
    
    # Infer skill level
    repos = profile_data.get('repos', [])
    years_active = _estimate_years_active(profile_data.get('created_at'))
    
    if years_active < 0.5:
        skill_level = "junior"
    elif years_active < 2:
        skill_level = "junior" if len(repos) < 5 else "mid"
    else:
        skill_level = "senior" if profile_data.get('followers', 0) > 10 else "mid"
    
    profile = {
        'username': username,
        'skill_level': skill_level,
        'top_languages': _extract_languages(repos),
        'frameworks': _extract_frameworks(repos),
        'activity_score': _calculate_activity_score(repos),
        'repos_analyzed': len(repos),
        'public_repos_count': profile_data.get('public_repos', 0),
        'estimated_years_experience': years_active,
        'last_commit': profile_data.get('updated_at', ''),
        'contribution_frequency': _estimate_frequency(repos),
        'summary': f"Profile for @{username} (skill: {skill_level})"
    }
    
    print(f"\nProfile generated:")
    print(f"  Username: {profile['username']}")
    print(f"  Skill Level: {profile['skill_level']}")
    print(f"  Top Languages: {', '.join(profile['top_languages'][:3])}")
    print(f"  Activity Score: {profile['activity_score']:.2f}")
    print(f"  Public Repos: {profile['public_repos_count']}")
    
    return profile


def challenge_setter_agent(github_client: GitHubClient, profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    AGENT 2: Challenge Setter Agent
    
    Selects template based on skill level, forks repo, creates Issue.
    """
    print("\n" + "="*60)
    print("AGENT 2: CHALLENGE SETTER AGENT")
    print("="*60)
    
    username = profile['username']
    skill_level = profile['skill_level']
    
    # Select template
    if skill_level in ['junior', 'mid']:
        template = 'challenge_junior'
    else:
        template = 'challenge_senior'
    
    print(f"\nTemplate selected: {template}")
    
    # Fork repository
    fork_data = github_client.fork_repository(
        source_owner='Gokul-404',
        source_repo='lyzr',
        target_user=username
    )
    
    fork_url = fork_data['fork_url']
    fork_owner = fork_data['fork_owner']
    fork_name = fork_data['fork_name']
    
    print(f"Fork created: {fork_url}")
    
    # Create GitHub Issue
    issue_title = "Your mission: find and fix the bugs"
    issue_body = _create_issue_body(template)
    
    issue_data = github_client.create_issue(
        owner=fork_owner,
        repo=fork_name,
        title=issue_title,
        body=issue_body,
        labels=['challenge', 'interview', '60-minute-deadline']
    )
    
    challenge = {
        'fork_url': fork_url,
        'fork_owner': fork_owner,
        'fork_name': fork_name,
        'issue_number': issue_data['issue_number'],
        'issue_url': issue_data['issue_url'],
        'challenge_template': template,
        'time_limit_minutes': 60,
        'creation_timestamp': issue_data['created_at'],
        'expected_bugs': 3,
        'status': 'ready'
    }
    
    print(f"\nChallenge configured:")
    print(f"  Issue URL: {challenge['issue_url']}")
    print(f"  Time Limit: {challenge['time_limit_minutes']} minutes")
    print(f"  Template: {challenge['challenge_template']}")
    
    return challenge


def watchdog_agent(github_client: GitHubClient, challenge: Dict[str, Any]) -> Dict[str, Any]:
    """
    AGENT 3: Watchdog Agent
    
    Polls for PR submission, enforces 60-minute timeout.
    """
    print("\n" + "="*60)
    print("AGENT 3: WATCHDOG AGENT")
    print("="*60)
    
    fork_owner = challenge['fork_owner']
    fork_repo = challenge['fork_name']
    issue_created_at = challenge['creation_timestamp']
    
    print(f"\nPolling for PR in {fork_owner}/{fork_repo}")
    print(f"Issue created: {issue_created_at}")
    print(f"Time limit: 60 minutes")
    
    watchdog = PRWatchdog(
        github_client=github_client,
        fork_owner=fork_owner,
        fork_repo=fork_repo,
        issue_created_at=issue_created_at,
        time_limit_minutes=60
    )
    
    # Poll with shorter timeout for demo (30 seconds instead of full 60 min)
    print("\nStarting poll loop (using 10-second demo interval for testing)...\n")
    
    result = watchdog.wait_for_submission(poll_interval_seconds=10)
    
    if result['status'] == 'success':
        print(f"\n✓ PR detected: #{result['pr_number']} ({result['time_taken_minutes']} minutes)")
        print(f"  URL: {result['pr_url']}")
        return result
    
    elif result['status'] == 'timeout':
        print(f"\n✗ Timeout: No PR submitted within {result['time_limit_minutes']} minutes")
        
        # Close the issue
        github_client.close_issue(
            owner=fork_owner,
            repo=fork_repo,
            issue_number=challenge['issue_number'],
            closing_comment="60 minutes have elapsed with no PR submission. Challenge incomplete."
        )
        
        return result
    
    else:
        print(f"\n⏳ Poll incomplete (demo mode)")
        return {'status': 'demo_timeout', 'message': 'Demo mode: skipping full 60-minute wait'}


def evaluator_agent(github_client: GitHubClient, watchdog_result: Dict[str, Any], 
                   challenge: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    AGENT 4: Evaluator Agent
    
    Scores PR submission against rubric, generates verdict and feedback.
    """
    print("\n" + "="*60)
    print("AGENT 4: EVALUATOR AGENT")
    print("="*60)
    
    # Handle demo timeout
    if watchdog_result.get('status') == 'demo_timeout':
        print("\nSkipping evaluation (no real PR in demo mode)")
        return {
            'status': 'demo_skipped',
            'message': 'Demo mode: evaluation skipped',
            'verdict': 'pending',
            'score': 0
        }
    
    if watchdog_result['status'] != 'success':
        print(f"\nCannot evaluate: {watchdog_result.get('message')}")
        return {
            'status': 'not_evaluated',
            'reason': watchdog_result.get('message'),
            'verdict': 'no hire'
        }
    
    print(f"\nEvaluating PR #{watchdog_result['pr_number']}")
    print(f"Time taken: {watchdog_result['time_taken_minutes']} minutes")
    
    # Score the submission
    scorer = SubmissionScorer(
        challenge_template=challenge['challenge_template'],
        pr_diff=watchdog_result.get('pr_diff', ''),
        pr_title=watchdog_result.get('pr_title', ''),
        pr_body=watchdog_result.get('pr_body', ''),
        commit_messages=['Sample commit']  # Would parse from PR in real scenario
    )
    
    evaluation = scorer.score()
    
    # Post PR comment
    pr_comment = _create_pr_comment(profile['username'], challenge, watchdog_result, evaluation)
    
    try:
        github_client.post_pr_comment(
            owner=challenge['fork_owner'],
            repo=challenge['fork_name'],
            pr_number=watchdog_result['pr_number'],
            comment_body=pr_comment
        )
        print("\nEvaluation posted to PR")
    except Exception as e:
        print(f"\nWarning: Could not post PR comment: {e}")
    
    # Close the issue
    try:
        github_client.close_issue(
            owner=challenge['fork_owner'],
            repo=challenge['fork_name'],
            issue_number=challenge['issue_number'],
            closing_comment="Challenge complete. Evaluation submitted."
        )
    except Exception as e:
        print(f"\nWarning: Could not close issue: {e}")
    
    # Build final report
    report = {
        'username': profile['username'],
        'challenge_template': challenge['challenge_template'],
        'time_taken_minutes': watchdog_result['time_taken_minutes'],
        'submission_timestamp': watchdog_result.get('created_at', ''),
        'pr_number': watchdog_result['pr_number'],
        'pr_url': watchdog_result['pr_url'],
        'rubric': evaluation['rubric'],
        'score_breakdown': evaluation['score_breakdown'],
        'verdict': evaluation['verdict'],
        'feedback': evaluation['feedback']
    }
    
    print(f"\n✓ Evaluation complete")
    print(f"  Verdict: {evaluation['verdict']}")
    print(f"  Score: {evaluation['score_breakdown']['total']}/100")
    
    return report


def run_pipeline(username: str) -> Dict[str, Any]:
    """
    Run the complete 4-agent interview pipeline.
    """
    print(f"\n{'='*60}")
    print(f"GitAgent Interviewer - Technical Interview")
    print(f"{'='*60}")
    print(f"Candidate: @{username}")
    print(f"Started: {datetime.utcnow().isoformat()}Z")
    
    session_id = str(uuid.uuid4())[:8]
    start_time = datetime.utcnow().isoformat() + "Z"
    
    try:
        # Initialize GitHub client
        github_token = get_env('GITHUB_TOKEN')
        github_client = GitHubClient(github_token)
        
        # Run agents
        profile = profile_agent(github_client, username)
        challenge = challenge_setter_agent(github_client, profile)
        watchdog_result = watchdog_agent(github_client, challenge)
        evaluation = evaluator_agent(github_client, watchdog_result, challenge, profile)
        
        end_time = datetime.utcnow().isoformat() + "Z"
        
        # Build final output
        final_report = {
            'session_id': session_id,
            'username': username,
            'start_time': start_time,
            'end_time': end_time,
            'profile': profile,
            'challenge': challenge,
            'watchdog_result': watchdog_result,
            'evaluation': evaluation,
            'github_logs': github_client.get_logs()
        }
        
        # Save results
        results_dir = os.path.join(os.path.dirname(__file__), 'results')
        os.makedirs(results_dir, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(results_dir, f"{username}_{timestamp}.json")
        
        with open(output_file, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        print(f"\n{'='*60}")
        print("PIPELINE COMPLETE")
        print(f"{'='*60}")
        print(f"Results saved to: {output_file}")
        
        return final_report
        
    except Exception as e:
        print(f"\n✗ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e), 'status': 'failed'}


# Helper functions

def _estimate_years_active(created_at: str) -> float:
    """Estimate years since account creation."""
    try:
        created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        delta = datetime.utcnow() - created
        return delta.days / 365.25
    except:
        return 0.5


def _extract_languages(repos: list) -> list:
    """Extract top programming languages from repos."""
    languages = {}
    for repo in repos:
        lang = repo.get('language')
        if lang:
            languages[lang] = languages.get(lang, 0) + 1
    
    sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
    return [lang for lang, _ in sorted_langs[:5]]


def _extract_frameworks(repos: list) -> list:
    """Extract frameworks from repo names and descriptions."""
    frameworks = set()
    
    common_frameworks = {
        'react', 'vue', 'angular', 'django', 'flask', 'fastapi', 
        'spring', 'node', 'express', 'nestjs', 'rails', 'golang',
        'kubernetes', 'docker', 'aws', 'azure', 'gcp'
    }
    
    for repo in repos:
        name = (repo.get('name') or '').lower()
        desc = (repo.get('description') or '').lower()
        
        for fw in common_frameworks:
            if fw in name or fw in desc:
                frameworks.add(fw.title())
    
    return list(frameworks)[:5]


def _calculate_activity_score(repos: list) -> float:
    """Calculate activity score based on update frequency."""
    if not repos:
        return 0.0
    
    from datetime import timedelta
    now = datetime.utcnow()
    active = 0
    
    for repo in repos:
        try:
            updated = datetime.fromisoformat(repo['updated_at'].replace('Z', '+00:00'))
            days_ago = (now - updated).days
            
            if days_ago < 30:
                active += 1
            elif days_ago < 90:
                active += 0.5
        except:
            pass
    
    return min(1.0, active / max(1, len(repos) * 0.5))


def _estimate_frequency(repos: list) -> str:
    """Estimate contribution frequency."""
    score = _calculate_activity_score(repos)
    
    if score >= 0.8:
        return 'daily'
    elif score >= 0.5:
        return 'weekly'
    elif score >= 0.2:
        return 'monthly'
    else:
        return 'sporadic'


def _create_issue_body(template: str) -> str:
    """Create GitHub Issue body."""
    base = """## Your mission

This repo has bugs. Find them. Fix them. Ship a PR.

**Time limit:** 60 minutes from now
**Rules:** One PR only. Your commit messages matter. No AI-generated fixes — we can tell.

**Acceptance criteria:**
- All tests pass
- No regressions introduced
- Code is clean and readable

When you're ready, open a PR against the main branch. The agent will evaluate it automatically.

Good luck.
"""
    
    if template == 'challenge_junior':
        return base + "\n\n**Challenge:** Fix the `calculate_stats` function. It has 3 bugs related to statistics calculation."
    else:
        return base + "\n\n**Challenge:** Fix the Flask `/transfer` endpoint. It has 3 bugs related to atomicity, authentication, and testing."


def _create_pr_comment(username: str, challenge: Dict, watchdog_result: Dict, 
                      evaluation: Dict) -> str:
    """Create PR comment with evaluation results."""
    score = evaluation['score_breakdown']
    
    comment = f"""## GitAgent Interviewer — Evaluation Report

**Candidate:** @{username}
**Challenge:** {challenge['challenge_template']}
**Time taken:** {watchdog_result['time_taken_minutes']} minutes
**Verdict:** {evaluation['verdict']}

### Score breakdown
| Dimension | Score | Max |
|-----------|-------|-----|
| Correctness | {score['correctness']} | 30 |
| Code quality | {score['code_quality']} | 25 |
| Edge case handling | {score['edge_cases']} | 20 |
| Approach & reasoning | {score['approach']} | 15 |
| Commit clarity | {score['commit_clarity']} | 10 |
| **Total** | **{score['total']}** | **100** |

### Feedback
{evaluation['feedback']}

---
*Evaluated autonomously by GitAgent Interviewer · Built with GitClaw + Claude*
"""
    
    return comment


def main():
    """CLI entry point."""
    load_env()
    
    if len(sys.argv) < 2:
        print("Usage: python main.py <github_username>")
        print("Example: python main.py torvalds")
        sys.exit(1)
    
    username = sys.argv[1]
    
    try:
        result = run_pipeline(username)
        
        # Print final report
        if 'error' not in result:
            print("\nFinal Report:")
            print(json.dumps(result.get('evaluation', {}), indent=2))
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
