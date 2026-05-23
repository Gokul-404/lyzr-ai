"""
GitAgent Interviewer - Demo Script

Runs the full interview pipeline on a hardcoded username.
Use this to demonstrate the system end-to-end.

Usage:
    python demo.py
"""

import os
import sys
import json
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from main import run_pipeline


def print_separator(title: str = ""):
    """Print a visual separator."""
    if title:
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}\n")
    else:
        print(f"\n{'-'*70}\n")


def demo():
    """Run the demo."""
    
    print(f"""
╔════════════════════════════════════════════════════════════════════╗
║                  GitAgent Interviewer — DEMO                       ║
║         Autonomous Technical Hiring via GitHub Pull Requests        ║
╚════════════════════════════════════════════════════════════════════╝

This demo runs the complete 4-agent interview pipeline:
  1. PROFILE AGENT — Analyze candidate's GitHub history
  2. CHALLENGE SETTER — Create fork and GitHub Issue with task
  3. WATCHDOG AGENT — Poll for PR submission (60-min timeout)
  4. EVALUATOR AGENT — Score the submission and post results

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

""")
    
    # Use the GitHub username passed as argument, or default to 'torvalds'
    username = sys.argv[1] if len(sys.argv) > 1 else 'torvalds'
    
    print(f"Demo Username: @{username}")
    print(f"Start Time: {datetime.utcnow().isoformat()}Z")
    print("\nNote: This demo uses a 10-second polling interval for testing.")
    print("In production, polling occurs every 60 seconds with a 60-minute timeout.\n")
    
    try:
        # Run the pipeline
        result = run_pipeline(username)
        
        # Print results
        print_separator("INTERVIEW RESULTS")
        
        if 'error' in result:
            print(f"✗ Interview failed: {result['error']}")
            return 1
        
        # Print agent outputs
        print_separator("AGENT 1: Profile Agent Output")
        profile = result.get('profile', {})
        print(f"""
Username: @{profile.get('username')}
Skill Level: {profile.get('skill_level')}
Top Languages: {', '.join(profile.get('top_languages', [])[:3])}
Activity Score: {profile.get('activity_score', 0):.2f}/1.0
Public Repos: {profile.get('public_repos_count')}
Estimated Experience: {profile.get('estimated_years_experience', 0):.1f} years
Summary: {profile.get('summary')}
""")
        
        print_separator("AGENT 2: Challenge Setter Output")
        challenge = result.get('challenge', {})
        print(f"""
Fork URL: {challenge.get('fork_url')}
Issue Number: #{challenge.get('issue_number')}
Challenge Template: {challenge.get('challenge_template')}
Time Limit: {challenge.get('time_limit_minutes')} minutes
Status: {challenge.get('status')}
""")
        
        print_separator("AGENT 3: Watchdog Agent Output")
        watchdog = result.get('watchdog_result', {})
        if watchdog.get('status') == 'demo_timeout':
            print(f"""
Status: Demo Mode (skipped full 60-minute wait)
Message: {watchdog.get('message')}

(In production, this agent would poll for 60 minutes waiting for PR submission)
""")
        else:
            print(f"""
Status: {watchdog.get('status')}
Message: {watchdog.get('message', 'No PR detected')}
Time Elapsed: {watchdog.get('time_elapsed_minutes', 0)} minutes
""")
        
        print_separator("AGENT 4: Evaluator Agent Output")
        evaluation = result.get('evaluation', {})
        if evaluation.get('status') == 'demo_skipped':
            print(f"""
Status: {evaluation.get('status')}
Message: {evaluation.get('message')}

(In production, this agent would score the PR submission against a comprehensive rubric)
""")
        else:
            score = evaluation.get('score_breakdown', {})
            print(f"""
Verdict: {evaluation.get('verdict', 'pending')}
Total Score: {score.get('total', 0)}/100

Score Breakdown:
  - Correctness: {score.get('correctness', 0)}/30
  - Code Quality: {score.get('code_quality', 0)}/25
  - Edge Cases: {score.get('edge_cases', 0)}/20
  - Approach: {score.get('approach', 0)}/15
  - Commit Clarity: {score.get('commit_clarity', 0)}/10

Feedback:
{evaluation.get('feedback', 'N/A')}
""")
        
        print_separator("PIPELINE SUMMARY")
        print(f"""
Session ID: {result.get('session_id')}
Candidate: @{result.get('username')}
Duration: {_calculate_duration(result.get('start_time'), result.get('end_time'))} minutes
Start: {result.get('start_time')}
End: {result.get('end_time')}

GitHub API Calls Logged: {len(result.get('github_logs', []))}
""")
        
        print_separator("RAW EVALUATION JSON")
        print(json.dumps(result.get('evaluation', {}), indent=2))
        
        print_separator()
        print(f"""
✓ Demo completed successfully!

Files saved:
  - results/@{username}_*.json — Full pipeline result
  - results/@{username}_*_evaluation.json — Evaluation detail
  - results/@{username}_*_logs.txt — System logs

Next Steps:
  1. Review the evaluation results in the results/ directory
  2. Visit the GitHub Issue URL to see the challenge posted
  3. In a real scenario, the watchdog would wait up to 60 minutes for a PR
  4. When a PR is submitted, the evaluator scores it and posts results to the PR

For production use:
  python main.py <github_username>

Built with GitClaw + Claude | Open GitAgent Standard
""")
        
        return 0
        
    except Exception as e:
        print_separator("ERROR")
        print(f"✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def _calculate_duration(start_iso: str, end_iso: str) -> int:
    """Calculate duration in minutes."""
    try:
        from datetime import datetime
        start = datetime.fromisoformat(start_iso.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_iso.replace('Z', '+00:00'))
        return int((end - start).total_seconds() / 60)
    except:
        return 0


if __name__ == '__main__':
    # Load and verify environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    required_keys = ["GITHUB_TOKEN", "GEMINI_API_KEY", "GITHUB_USERNAME"]
    missing = [key for key in required_keys if not os.getenv(key)]
    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}")
        print("Please set these in your .env file")
        print("\nRun: cp .env.example .env")
        print("Then edit .env and add your GITHUB_TOKEN and GEMINI_API_KEY")
        sys.exit(1)
    
    sys.exit(demo())
