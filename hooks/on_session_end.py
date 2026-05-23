"""
Session end hook for GitAgent Interviewer.

Runs after each interview session completes, saving state and generating summary.
"""

import json
import os
from datetime import datetime


def on_session_end(session_data):
    """
    Called when an interview session ends (success, timeout, or error).
    
    session_data contains:
    {
        'username': str,
        'session_id': str,
        'start_time': str (ISO),
        'end_time': str (ISO),
        'challenge_template': str,
        'status': 'completed' | 'timeout' | 'error',
        'pr_number': int or None,
        'evaluation': dict or None,
        'logs': list of str
    }
    """
    
    # Ensure results directory exists
    results_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    # Generate summary
    summary = {
        'username': session_data.get('username'),
        'session_id': session_data.get('session_id'),
        'start_time': session_data.get('start_time'),
        'end_time': session_data.get('end_time'),
        'duration_minutes': _calculate_duration(
            session_data.get('start_time'),
            session_data.get('end_time')
        ),
        'challenge_template': session_data.get('challenge_template'),
        'status': session_data.get('status'),
        'pr_number': session_data.get('pr_number'),
        'verdict': session_data.get('evaluation', {}).get('verdict', 'not_evaluated'),
        'score': session_data.get('evaluation', {}).get('score_breakdown', {}).get('total', 0),
        'logs_count': len(session_data.get('logs', []))
    }
    
    # Save summary
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"{session_data.get('username')}_{timestamp}.json"
    filepath = os.path.join(results_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Save full evaluation if available
    if session_data.get('evaluation'):
        eval_filename = f"{session_data.get('username')}_{timestamp}_evaluation.json"
        eval_filepath = os.path.join(results_dir, eval_filename)
        
        with open(eval_filepath, 'w') as f:
            json.dump(session_data.get('evaluation'), f, indent=2)
    
    # Save logs
    if session_data.get('logs'):
        log_filename = f"{session_data.get('username')}_{timestamp}_logs.txt"
        log_filepath = os.path.join(results_dir, log_filename)
        
        with open(log_filepath, 'w') as f:
            f.write('\n'.join(session_data.get('logs')))
    
    print(f"Session summary saved to {filepath}")


def _calculate_duration(start_iso: str, end_iso: str) -> int:
    """Calculate duration in minutes between two ISO timestamps."""
    try:
        start = datetime.fromisoformat(start_iso.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_iso.replace('Z', '+00:00'))
        return int((end - start).total_seconds() / 60)
    except:
        return 0
