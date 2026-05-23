"""
GitHub API utilities for GitAgent Interviewer.

Provides abstracted methods for:
- Fetching user profiles and repository data
- Forking repositories
- Creating GitHub Issues
- Polling Pull Requests
- Posting PR comments
"""

import os
import json
import time
from datetime import datetime
from typing import Optional, Dict, List, Any
import requests
from github import Github, GithubException


class GitHubClient:
    """Wraps PyGithub with error handling and logging."""
    
    def __init__(self, token: str):
        self.token = token
        self.client = Github(token)
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"token {token}"})
        self.rate_limit_remaining = 5000
        self.log = []
    
    def log_event(self, event: str, level: str = "info"):
        """Log an event with timestamp."""
        timestamp = datetime.utcnow().isoformat() + "Z"
        log_entry = f"[{timestamp}] {(level or 'INFO').upper()}: {event}"
        self.log.append(log_entry)
        print(log_entry)
    
    def get_user_profile(self, username: str) -> Dict[str, Any]:
        """
        Fetch GitHub user profile and repository statistics.
        
        Returns: {
            'username': str,
            'public_repos': int,
            'followers': int,
            'following': int,
            'created_at': str,
            'updated_at': str,
            'repos': List[Dict]
        }
        """
        try:
            self.log_event(f"Fetching profile for @{username}")
            user = self.client.get_user(username)
            
            repos = []
            for repo in user.get_repos(sort="updated"):
                if not repo.fork:  # Exclude forks from analysis
                    repos.append({
                        'name': repo.name,
                        'url': repo.html_url,
                        'language': repo.language,
                        'stars': repo.stargazers_count,
                        'forks': repo.forks_count,
                        'updated_at': repo.updated_at.isoformat(),
                        'description': repo.description,
                        'topics': repo.topics
                    })
            
            self.log_event(f"Found {len(repos)} public repos for @{username}")
            
            return {
                'username': user.login,
                'public_repos': user.public_repos,
                'followers': user.followers,
                'following': user.following,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat(),
                'repos': repos[:50]  # Top 50
            }
        except GithubException as e:
            self.log_event(f"GitHub error fetching @{username}: {e.status} {e.data}", "error")
            raise
        except Exception as e:
            self.log_event(f"Error fetching profile: {str(e)}", "error")
            raise
    
    def fork_repository(self, source_owner: str, source_repo: str, 
                       target_user: str) -> Optional[Dict[str, Any]]:
        """
        Fork a repository into target user's namespace.
        
        Returns: {
            'fork_url': str,
            'fork_owner': str,
            'fork_name': str,
            'fork_created_at': str
        }
        """
        try:
            self.log_event(f"Forking {source_owner}/{source_repo} to @{target_user}")
            
            try:
                source_repo_obj = self.client.get_repo(f"{source_owner}/{source_repo}")
            except GithubException as e:
                # Source repo doesn't exist - use demo mode with mock fork
                self.log_event(f"Source repo {source_owner}/{source_repo} not found. Using demo mock fork.")
                
                # Return mock fork data for demo
                return {
                    'fork_url': f"https://github.com/{target_user}/{source_repo}",
                    'fork_owner': target_user,
                    'fork_name': source_repo,
                    'fork_created_at': datetime.utcnow().isoformat(),
                    'demo_mode': True
                }
            
            
            # Check if fork already exists
            try:
                existing_fork = self.client.get_user(target_user).get_repo(source_repo)
                self.log_event(f"Fork already exists: {existing_fork.html_url}")
                return {
                    'fork_url': existing_fork.html_url,
                    'fork_owner': target_user,
                    'fork_name': source_repo,
                    'fork_created_at': existing_fork.created_at.isoformat(),
                    'reused': True
                }
            except GithubException:
                pass  # Fork doesn't exist, create it
            
            # Create new fork
            fork = source_repo_obj.create_fork()
            time.sleep(2)  # Wait for fork to be created
            
            self.log_event(f"Fork created: {fork.html_url}")
            
            return {
                'fork_url': fork.html_url,
                'fork_owner': target_user,
                'fork_name': source_repo,
                'fork_created_at': fork.created_at.isoformat(),
                'reused': False
            }
        except GithubException as e:
            self.log_event(f"GitHub error forking repo: {e.status} {e.data}", "error")
            raise
        except Exception as e:
            self.log_event(f"Error forking repository: {str(e)}", "error")
            raise
    
    def create_issue(self, owner: str, repo: str, title: str, body: str,
                     labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a GitHub Issue.
        
        Returns: {
            'issue_number': int,
            'issue_url': str,
            'created_at': str
        }
        """
        try:
            self.log_event(f"Creating issue in {owner}/{repo}: {title}")
            
            repo_obj = self.client.get_repo(f"{owner}/{repo}")
            issue = repo_obj.create_issue(
                title=title,
                body=body,
                labels=labels or []
            )
            
            self.log_event(f"Issue created: #{issue.number}")
            
            return {
                'issue_number': issue.number,
                'issue_url': issue.html_url,
                'created_at': issue.created_at.isoformat()
            }
        except GithubException as e:
            # In demo mode, return mock issue data
            if e.status == 404:
                self.log_event(f"Demo mode: Repo {owner}/{repo} not found. Using mock issue.", "warning")
                return {
                    'issue_number': 1,
                    'issue_url': f"https://github.com/{owner}/{repo}/issues/1",
                    'created_at': datetime.utcnow().isoformat(),
                    'demo_mode': True
                }
            self.log_event(f"GitHub error creating issue: {e.status} {e.data}", "error")
            raise
        except Exception as e:
            self.log_event(f"Error creating issue: {str(e)}", "error")
            raise
    
    def get_open_prs(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """
        Get all open PRs in a repository.
        
        Returns list of: {
            'number': int,
            'title': str,
            'url': str,
            'created_at': str,
            'updated_at': str,
            'user': str
        }
        """
        try:
            repo_obj = self.client.get_repo(f"{owner}/{repo}")
            prs = []
            
            for pr in repo_obj.get_pulls(state="open"):
                prs.append({
                    'number': pr.number,
                    'title': pr.title,
                    'url': pr.html_url,
                    'created_at': pr.created_at.isoformat(),
                    'updated_at': pr.updated_at.isoformat(),
                    'user': pr.user.login,
                    'body': pr.body or ""
                })
            
            return prs
        except GithubException as e:
            self.log_event(f"GitHub error fetching PRs: {e.status} {e.data}", "error")
            return []
        except Exception as e:
            self.log_event(f"Error fetching PRs: {str(e)}", "error")
            return []
    
    def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """
        Get the full diff for a PR.
        
        Returns: unified diff text
        """
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
            response = self.session.get(url, headers={"Accept": "application/vnd.github.v3.diff"})
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.log_event(f"Error fetching PR diff: {str(e)}", "error")
            return ""
    
    def post_pr_comment(self, owner: str, repo: str, pr_number: int, 
                       comment_body: str) -> Dict[str, Any]:
        """
        Post a comment on a PR.
        
        Returns: {
            'comment_id': int,
            'comment_url': str,
            'posted_at': str
        }
        """
        try:
            self.log_event(f"Posting comment to {owner}/{repo}#{pr_number}")
            
            repo_obj = self.client.get_repo(f"{owner}/{repo}")
            pr = repo_obj.get_pull(pr_number)
            comment = pr.create_issue_comment(comment_body)
            
            self.log_event(f"Comment posted: {comment.html_url}")
            
            return {
                'comment_id': comment.id,
                'comment_url': comment.html_url,
                'posted_at': comment.created_at.isoformat()
            }
        except GithubException as e:
            self.log_event(f"GitHub error posting comment: {e.status} {e.data}", "error")
            raise
        except Exception as e:
            self.log_event(f"Error posting comment: {str(e)}", "error")
            raise
    
    def close_issue(self, owner: str, repo: str, issue_number: int, 
                   closing_comment: Optional[str] = None) -> Dict[str, Any]:
        """Close a GitHub Issue with optional closing comment."""
        try:
            repo_obj = self.client.get_repo(f"{owner}/{repo}")
            issue = repo_obj.get_issue(issue_number)
            
            if closing_comment:
                issue.create_comment(closing_comment)
                self.log_event(f"Closing comment posted to issue #{issue_number}")
            
            issue.edit(state="closed")
            self.log_event(f"Issue #{issue_number} closed")
            
            return {
                'issue_number': issue_number,
                'closed_at': datetime.utcnow().isoformat() + "Z",
                'status': 'closed'
            }
        except GithubException as e:
            self.log_event(f"GitHub error closing issue: {e.status} {e.data}", "error")
            raise
        except Exception as e:
            self.log_event(f"Error closing issue: {str(e)}", "error")
            raise
    
    def get_logs(self) -> List[str]:
        """Return all logged events."""
        return self.log
