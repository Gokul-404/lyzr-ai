"""
Scoring utility for GitAgent Interviewer.

Evaluates PR submissions against the comprehensive rubric
using Google Gemini 1.5 Flash API (free tier).
"""

import json
import os
import time
from typing import Dict, Any, List, Tuple
from datetime import datetime
import google.generativeai as genai


class SubmissionScorer:
    """Scores PR submissions using Google Gemini 1.5 Flash API."""
    
    CORRECTNESS_MAX = 30
    CODE_QUALITY_MAX = 25
    EDGE_CASES_MAX = 20
    APPROACH_MAX = 15
    COMMIT_CLARITY_MAX = 10
    TOTAL_MAX = 100
    
    def __init__(self, challenge_template: str, pr_diff: str, pr_title: str, 
                 pr_body: str, commit_messages: List[str]):
        self.challenge_template = challenge_template
        self.pr_diff = pr_diff
        self.pr_title = pr_title
        self.pr_body = pr_body
        self.commit_messages = commit_messages
        
        # Initialize Gemini API client (free tier - gemini-1.5-flash)
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def analyze_diff(self) -> Dict[str, Any]:
        """Parse and analyze the diff."""
        analysis = {
            'files_changed': [],
            'lines_added': 0,
            'lines_removed': 0,
            'functions_modified': [],
            'has_refactoring': False,
            'diff_complexity': 'simple'
        }
        
        lines = (self.pr_diff or '').split('\n')
        current_file = None
        
        for line in lines:
            if line.startswith('diff --git'):
                parts = line.split()
                if len(parts) >= 4:
                    current_file = parts[3].lstrip('b/')
                    if current_file not in analysis['files_changed']:
                        analysis['files_changed'].append(current_file)
            elif line.startswith('+') and not line.startswith('+++'):
                analysis['lines_added'] += 1
            elif line.startswith('-') and not line.startswith('---'):
                analysis['lines_removed'] += 1
            elif line.startswith('def ') or line.startswith('class '):
                func_name = line.split('(')[0].replace('def ', '').replace('class ', '')
                if func_name not in analysis['functions_modified']:
                    analysis['functions_modified'].append(func_name)
        
        # Estimate refactoring (many lines changed vs added/removed)
        ratio = (analysis['lines_added'] + analysis['lines_removed']) / max(1, len(lines))
        if ratio > 0.3:
            analysis['has_refactoring'] = True
            analysis['diff_complexity'] = 'moderate'
        if ratio > 0.5:
            analysis['diff_complexity'] = 'complex'
        
        return analysis
    
    def score_correctness(self, diff_analysis: Dict[str, Any]) -> Tuple[int, str]:
        """Score correctness dimension (0-30)."""
        # This is heuristic-based; real grading would run tests
        
        diff_lower = (self.pr_diff or '').lower()
        score = 0
        reasoning = []
        
        if self.challenge_template == 'challenge_junior':
            # Look for bug fixes
            
            # Bug 1: off-by-one in average
            if 'len(numbers)' in self.pr_diff and '/ len(numbers)' in self.pr_diff:
                score += 10
                reasoning.append("Off-by-one error fixed (average division)")
            
            # Bug 2: wrong operator in max
            if 'max_val' in diff_lower and '>' in self.pr_diff:
                score += 10
                reasoning.append("Max comparison operator fixed")
            
            # Bug 3: null check for empty list
            if 'if not numbers' in self.pr_diff or 'if len(numbers) == 0' in self.pr_diff:
                score += 10
                reasoning.append("Empty list null check added")
            
        elif self.challenge_template == 'challenge_senior':
            # Look for complex bug fixes
            
            # Bug 1: race condition / atomic transaction
            if 'transaction' in diff_lower or 'atomic' in diff_lower or 'with session' in diff_lower:
                score += 12
                reasoning.append("Race condition fixed with atomic transaction")
            elif 'lock' in diff_lower or 'mutex' in diff_lower:
                score += 10
                reasoning.append("Race condition addressed with locking")
            
            # Bug 2: authentication check
            if 'auth' in diff_lower or 'user_id' in diff_lower or 'verify' in diff_lower:
                score += 12
                reasoning.append("Authentication check added")
            
            # Bug 3: test fix
            if '@patch' in self.pr_diff or 'mock' in diff_lower:
                score += 6
                reasoning.append("Test mocking corrected")
        
        # Penalize overly complex changes
        if diff_analysis['has_refactoring'] and score > 20:
            score -= 5
            reasoning.append("(Slight penalty for unnecessary refactoring)")
        
        score = min(score, self.CORRECTNESS_MAX)
        return score, " ".join(reasoning)
    
    def score_code_quality(self, diff_analysis: Dict[str, Any]) -> Tuple[int, str]:
        """Score code quality dimension (0-25)."""
        score = 15  # Start with baseline
        reasoning = []
        
        # Check for style violations
        if '\t' in self.pr_diff:
            score -= 2
            reasoning.append("Contains tabs (style violation)")
        
        # Check line length
        long_lines = [line for line in self.pr_diff.split('\n') if len(line) > 100]
        if long_lines:
            score -= min(5, len(long_lines) // 2)
            reasoning.append(f"Some long lines (>{100})")
        
        # Check for unnecessary changes
        if diff_analysis['has_refactoring'] and diff_analysis['diff_complexity'] == 'complex':
            score -= 5
            reasoning.append("Over-engineered fix")
        
        # Check for readability
        if self.pr_diff and '#' in self.pr_diff:
            score += 2
            reasoning.append("Contains comments")
        
        # Penalize one-liner changes that might be unclear
        if diff_analysis['lines_added'] + diff_analysis['lines_removed'] < 3 and score < 20:
            score = max(10, score)
            reasoning.append("Minimal changes (unclear impact)")
        
        score = min(max(0, score), self.CODE_QUALITY_MAX)
        return score, " ".join(reasoning)
    
    def score_edge_cases(self, diff_analysis: Dict[str, Any]) -> Tuple[int, str]:
        """Score edge case handling (0-20)."""
        score = 10  # Start with baseline
        reasoning = []
        
        diff_lower = (self.pr_diff or '').lower()
        
        # Check for edge case patterns
        edge_case_keywords = [
            'if not', 'if len', 'try:', 'except', 'none',
            'empty', 'null', 'zero', 'negative', 'boundary'
        ]
        
        edge_case_count = sum(1 for keyword in edge_case_keywords if keyword in diff_lower)
        score += min(10, edge_case_count * 2)
        
        if edge_case_count > 3:
            reasoning.append("Good edge case handling")
        elif edge_case_count > 0:
            reasoning.append("Some edge cases considered")
        else:
            reasoning.append("Limited edge case consideration")
        
        score = min(max(0, score), self.EDGE_CASES_MAX)
        return score, " ".join(reasoning)
    
    def score_approach(self, diff_analysis: Dict[str, Any]) -> Tuple[int, str]:
        """Score approach & reasoning (0-15)."""
        score = 8  # Start with baseline
        reasoning = []
        
        # More commits = shows iterative thinking
        if len(self.commit_messages) > 1:
            score += 3
            reasoning.append("Multiple thoughtful commits")
        elif len(self.commit_messages) == 1:
            reasoning.append("Single commit")
        
        # Check for explanation in PR body
        if self.pr_body and len(self.pr_body) > 50:
            score += 3
            reasoning.append("Detailed PR description")
        
        # Check for clever vs brute force
        if diff_analysis['diff_complexity'] == 'simple':
            score += 2
            reasoning.append("Clean, simple approach")
        elif diff_analysis['diff_complexity'] == 'complex':
            score -= 2
            reasoning.append("Overly complex approach")
        
        score = min(max(0, score), self.APPROACH_MAX)
        return score, " ".join(reasoning)
    
    def score_commit_clarity(self) -> Tuple[int, str]:
        """Score commit clarity (0-10)."""
        score = 0
        reasoning = []
        
        if not self.commit_messages:
            return 0, "No commits found"
        
        # Score based on commit message quality
        for msg in self.commit_messages:
            words = len(msg.split())
            if words >= 5:
                score += 5
            elif words >= 3:
                score += 3
            else:
                score += 1
        
        score = score // len(self.commit_messages)
        
        # Bonus for PR description
        if self.pr_body and len(self.pr_body) > 30:
            score += 2
            reasoning.append("Good PR body explanation")
        
        if score >= 8:
            reasoning.append("Clear commit and PR descriptions")
        elif score >= 5:
            reasoning.append("Adequate commit messages")
        else:
            reasoning.append("Minimal commit descriptions")
        
        score = min(max(0, score), self.COMMIT_CLARITY_MAX)
        return score, " ".join(reasoning)
    
    def generate_verdict(self, total_score: int) -> Tuple[str, str]:
        """Generate verdict based on total score."""
        if total_score >= 85:
            return "strong hire", "Demonstrated mastery. This engineer ships clean, thoughtful code under pressure."
        elif total_score >= 75:
            return "hire", "Solid fundamentals. Would be productive on the team immediately."
        elif total_score >= 60:
            return "consider", "Shows promise but has gaps. Could work with mentorship or specific growth areas."
        else:
            return "no hire", "Does not meet bar for this role. Recommend revisiting after building more experience."
    
    def score(self) -> Dict[str, Any]:
        """
        Evaluate the submission using Gemini 1.5 Flash API and return complete score report.
        Includes rate limiting (2 second pause) and 429 error handling.
        """
        # Build evaluation prompt
        evaluation_prompt = self._build_evaluation_prompt()
        
        try:
            # Call Gemini 1.5 Flash API with rate limiting
            print("Calling Gemini 1.5 Flash API for evaluation...")
            response = self.model.generate_content(evaluation_prompt)
            
            # Rate limiting: pause to avoid hitting free tier limits
            time.sleep(2)
            
            # Parse Gemini's JSON response
            response_text = response.text
            evaluation = self._parse_gemini_response(response_text)
            
            return evaluation
            
        except Exception as e:
            error_str = str(e)
            
            # Handle rate limiting (429 error)
            if error_str and ("429" in error_str or "rate limit" in error_str.lower()):
                print("Rate limited by Gemini API. Waiting 10 seconds...")
                time.sleep(10)
                try:
                    response = self.model.generate_content(evaluation_prompt)
                    time.sleep(2)
                    evaluation = self._parse_gemini_response(response.text)
                    return evaluation
                except Exception as e2:
                    print(f"Retry failed: {e2}. Using heuristic scoring.")
                    return self._heuristic_score()
            else:
                print(f"Warning: Gemini API call failed: {e}. Using heuristic scoring.")
                return self._heuristic_score()
    
    def _build_evaluation_prompt(self) -> str:
        """Build the evaluation prompt for Gemini 1.5 Flash."""
        # Truncate diff to stay within free tier context limits
        diff_preview = self.pr_diff[:2000] if self.pr_diff else ""
        
        prompt = f"""You are a senior engineering hiring manager. Evaluate this pull request diff and return ONLY a valid JSON object with no extra text, no markdown, no code fences.

PR Diff:
{diff_preview}

Challenge: {self.challenge_template}
PR Title: {self.pr_title or 'N/A'}
PR Body: {self.pr_body or 'N/A'}
Commits: {', '.join(self.commit_messages) if self.commit_messages else 'N/A'}

Score using this exact rubric:
- correctness: 0-30 (did they fix all bugs correctly?)
- code_quality: 0-25 (clean, readable, no unnecessary changes?)
- edge_cases: 0-20 (null checks, empty inputs, error handling?)
- approach: 0-15 (smart targeted fix or brute force?)
- commit_clarity: 0-10 (clear commit message and PR description?)

Return this exact JSON structure:
{{
  "correctness": <int>,
  "code_quality": <int>,
  "edge_cases": <int>,
  "approach": <int>,
  "commit_clarity": <int>,
  "total": <int>,
  "verdict": "strong hire or hire or consider or no hire",
  "feedback": "<3-5 sentences citing specific lines from the diff>"
}}"""
        
        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini's JSON response and build evaluation dict."""
        try:
            # Clean markdown fences if Gemini adds them
            clean_text = (response_text or '').strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]  # Remove ```json
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]  # Remove ```
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]  # Remove trailing ```
            
            clean_text = clean_text.strip()
            
            # Parse JSON
            gemini_eval = json.loads(clean_text)
            
            # Extract scores (with defaults if missing)
            correctness = int(gemini_eval.get('correctness', 15))
            code_quality = int(gemini_eval.get('code_quality', 12))
            edge_cases = int(gemini_eval.get('edge_cases', 10))
            approach = int(gemini_eval.get('approach', 8))
            commit_clarity = int(gemini_eval.get('commit_clarity', 5))
            
            # Validate scores are in range
            correctness = min(max(0, correctness), self.CORRECTNESS_MAX)
            code_quality = min(max(0, code_quality), self.CODE_QUALITY_MAX)
            edge_cases = min(max(0, edge_cases), self.EDGE_CASES_MAX)
            approach = min(max(0, approach), self.APPROACH_MAX)
            commit_clarity = min(max(0, commit_clarity), self.COMMIT_CLARITY_MAX)
            
            total = min(correctness + code_quality + edge_cases + approach + commit_clarity, self.TOTAL_MAX)
            
            verdict = (gemini_eval.get('verdict', 'consider') or 'consider').strip().lower()
            if verdict not in ['strong hire', 'hire', 'consider', 'no hire']:
                verdict = 'consider'
            
            feedback = gemini_eval.get('feedback', 'Evaluation complete.')
            
            return {
                'rubric': {
                    'correctness': {
                        'score': correctness,
                        'max': self.CORRECTNESS_MAX,
                    },
                    'code_quality': {
                        'score': code_quality,
                        'max': self.CODE_QUALITY_MAX,
                    },
                    'edge_cases': {
                        'score': edge_cases,
                        'max': self.EDGE_CASES_MAX,
                    },
                    'approach': {
                        'score': approach,
                        'max': self.APPROACH_MAX,
                    },
                    'commit_clarity': {
                        'score': commit_clarity,
                        'max': self.COMMIT_CLARITY_MAX,
                    }
                },
                'score_breakdown': {
                    'correctness': correctness,
                    'code_quality': code_quality,
                    'edge_cases': edge_cases,
                    'approach': approach,
                    'commit_clarity': commit_clarity,
                    'total': total
                },
                'verdict': verdict,
                'feedback': feedback
            }
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse Gemini JSON response: {e}")
            print(f"Response text: {response_text[:200]}")
            return self._heuristic_score()
        except Exception as e:
            print(f"Error processing Gemini response: {e}")
            return self._heuristic_score()
    
    def _heuristic_score(self) -> Dict[str, Any]:
        """Fallback heuristic scoring when Claude API is unavailable."""
        diff_analysis = self.analyze_diff()
        
        correctness, correct_reasoning = self.score_correctness(diff_analysis)
        code_quality, quality_reasoning = self.score_code_quality(diff_analysis)
        edge_cases, edge_reasoning = self.score_edge_cases(diff_analysis)
        approach, approach_reasoning = self.score_approach(diff_analysis)
        commit_clarity, commit_reasoning = self.score_commit_clarity()
        
        total = correctness + code_quality + edge_cases + approach + commit_clarity
        verdict, _ = self.generate_verdict(total)
        
        feedback = self._generate_feedback(
            correctness, code_quality, edge_cases, approach, commit_clarity,
            total, verdict
        )
        
        return {
            'rubric': {
                'correctness': {
                    'score': correctness,
                    'max': self.CORRECTNESS_MAX,
                    'reasoning': correct_reasoning
                },
                'code_quality': {
                    'score': code_quality,
                    'max': self.CODE_QUALITY_MAX,
                    'reasoning': quality_reasoning
                },
                'edge_cases': {
                    'score': edge_cases,
                    'max': self.EDGE_CASES_MAX,
                    'reasoning': edge_reasoning
                },
                'approach': {
                    'score': approach,
                    'max': self.APPROACH_MAX,
                    'reasoning': approach_reasoning
                },
                'commit_clarity': {
                    'score': commit_clarity,
                    'max': self.COMMIT_CLARITY_MAX,
                    'reasoning': commit_reasoning
                }
            },
            'score_breakdown': {
                'correctness': correctness,
                'code_quality': code_quality,
                'edge_cases': edge_cases,
                'approach': approach,
                'commit_clarity': commit_clarity,
                'total': total
            },
            'verdict': verdict,
            'feedback': feedback
        }
    
    def _generate_feedback(self, correct: int, quality: int, edges: int, 
                          approach: int, clarity: int, total: int, verdict: str) -> str:
        """Generate specific, actionable feedback."""
        feedback_parts = []
        
        # Positive feedback
        if correct >= 25:
            feedback_parts.append("All bugs were correctly identified and fixed.")
        elif correct >= 18:
            feedback_parts.append("Most bugs were fixed, though some handling could be improved.")
        
        if quality >= 20:
            feedback_parts.append("The code is clean and follows project conventions.")
        elif quality >= 15:
            feedback_parts.append("The code works, but consider addressing style issues.")
        
        if edges >= 16:
            feedback_parts.append("Strong handling of edge cases and error scenarios.")
        elif edges >= 10:
            feedback_parts.append("Good coverage of common edge cases, though some scenarios remain untested.")
        
        if approach >= 12:
            feedback_parts.append("The approach shows clear understanding of the underlying problem.")
        
        if clarity >= 8:
            feedback_parts.append("Your commit messages and PR description were clear and helpful.")
        
        # Constructive feedback
        if correct < 20:
            feedback_parts.append("Review the test failures carefully—some bugs may still be present.")
        
        if quality < 15:
            feedback_parts.append("Consider reviewing your code for style consistency with the project standards.")
        
        if edges < 12:
            feedback_parts.append("Think about edge cases: what happens with empty inputs, invalid data, or boundary conditions?")
        
        if approach < 10:
            feedback_parts.append("The fix works, but consider whether there's a more elegant or maintainable approach.")
        
        if clarity < 6:
            feedback_parts.append("Future PRs: invest more in commit messages and PR descriptions—they help reviewers understand intent.")
        
        # Summary
        if verdict == "strong hire":
            feedback_parts.append(f"Overall: Excellent work. This is a strong submission that demonstrates both technical skill and attention to detail.")
        elif verdict == "hire":
            feedback_parts.append(f"Overall: Well done. You fixed the issues and shipped clean code—you're ready to contribute to a real team.")
        elif verdict == "consider":
            feedback_parts.append(f"Overall: You're on the right track. With more practice on edge case thinking and code clarity, you'll be there.")
        else:
            feedback_parts.append(f"Overall: This submission doesn't meet the bar yet. Focus on understanding why each bug exists, not just making tests pass.")
        
        return " ".join(feedback_parts)
