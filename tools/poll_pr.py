"""
PR polling utility for GitAgent Interviewer.

Polls a fork repository at regular intervals to detect PR submissions
and enforce the 60-minute time window.
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from .github_api import GitHubClient


class PRWatchdog:
    """Monitors a fork repository for PR submissions."""
    
    def __init__(self, github_client: GitHubClient, fork_owner: str, fork_repo: str,
                 issue_created_at: str, time_limit_minutes: int = 60):
        self.client = github_client
        self.fork_owner = fork_owner
        self.fork_repo = fork_repo
        self.issue_created_at = datetime.fromisoformat((issue_created_at or '').replace("Z", "+00:00"))
        self.time_limit = timedelta(minutes=time_limit_minutes)
        self.start_time = datetime.utcnow()
        self.poll_count = 0
        self.max_polls = time_limit_minutes  # One poll per minute
    
    def poll(self) -> Optional[Dict[str, Any]]:
        """
        Poll for PRs. Returns PR data when found, None if still waiting.
        
        Returns: {
            'pr_number': int,
            'pr_url': str,
            'pr_title': str,
            'pr_body': str,
            'created_at': str,
            'author': str,
            'time_taken_minutes': int,
            'status': 'success' | 'timeout' | 'waiting'
        }
        """
        self.poll_count += 1
        current_time = datetime.utcnow()
        elapsed = current_time - self.issue_created_at
        
        # Check if time limit exceeded
        if elapsed > self.time_limit:
            return {
                'pr_number': None,
                'status': 'timeout',
                'time_taken_minutes': int(elapsed.total_seconds() / 60),
                'time_limit_minutes': int(self.time_limit.total_seconds() / 60),
                'message': 'Time limit exceeded. No PR submission within window.'
            }
        
        # Fetch open PRs
        try:
            prs = self.client.get_open_prs(self.fork_owner, self.fork_repo)
        except Exception as e:
            # In demo mode, repo doesn't exist
            if '404' in str(e):
                self.client.log_event(f"Demo mode: Repo not found. Returning demo timeout.", "warning")
                return {
                    'status': 'demo_timeout',
                    'message': 'Demo mode: Repository does not exist',
                    'demo_timeout': True
                }
            raise
        
        if prs:
            # Use the first PR (earliest created)
            pr = sorted(prs, key=lambda x: x['created_at'])[0]
            pr_created = datetime.fromisoformat((pr.get('created_at') or '').replace("Z", "+00:00"))
            time_taken = int((pr_created - self.issue_created_at).total_seconds() / 60)
            
            # Check if PR was created within window
            if time_taken <= int(self.time_limit.total_seconds() / 60):
                self.client.log_event(f"PR #{pr['number']} detected at T+{time_taken}min")
                
                # Fetch the full diff
                diff = self.client.get_pr_diff(self.fork_owner, self.fork_repo, pr['number'])
                
                return {
                    'pr_number': pr['number'],
                    'pr_url': pr['url'],
                    'pr_title': pr['title'],
                    'pr_body': pr['body'],
                    'created_at': pr['created_at'],
                    'author': pr['user'],
                    'time_taken_minutes': time_taken,
                    'status': 'success',
                    'pr_diff': diff
                }
            else:
                # PR submitted after time window
                return {
                    'pr_number': pr['number'],
                    'pr_url': pr['url'],
                    'status': 'late',
                    'time_taken_minutes': time_taken,
                    'time_limit_minutes': int(self.time_limit.total_seconds() / 60),
                    'message': 'PR submitted after 60-minute window.'
                }
        
        # Still waiting
        minutes_remaining = int((self.time_limit - elapsed).total_seconds() / 60)
        self.client.log_event(f"Poll #{self.poll_count}: No PR yet. {minutes_remaining}min remaining.")
        
        return {
            'status': 'waiting',
            'poll_count': self.poll_count,
            'time_elapsed_minutes': int(elapsed.total_seconds() / 60),
            'time_remaining_minutes': minutes_remaining
        }
    
    def wait_for_submission(self, poll_interval_seconds: int = 60) -> Dict[str, Any]:
        """
        Block and poll until PR is submitted or time limit is reached.
        
        Returns: PR data or timeout result
        """
        max_demo_polls = 3  # Demo mode: timeout after 3 polls instead of 60 minutes
        poll_count_demo = 0
        
        while True:
            result = self.poll()
            
            # In demo mode (repo doesn't exist), timeout early
            if result.get('demo_timeout'):
                return result
            
            # Count demo polls and timeout if threshold reached
            if poll_count_demo >= max_demo_polls and result['status'] == 'waiting':
                self.client.log_event("Demo mode: Timeout after 3 polls. No real PR submitted.")
                return {
                    'status': 'demo_timeout',
                    'message': 'Demo mode: Reached poll limit without PR submission',
                    'polls_attempted': poll_count_demo
                }
            poll_count_demo += 1
            
            if result['status'] in ['success', 'timeout', 'late']:
                return result
            
            # Still waiting, sleep and retry
            self.client.log_event(f"Waiting {poll_interval_seconds}s before next poll...")
            time.sleep(poll_interval_seconds)
