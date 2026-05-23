"""
Flask API with a broken /transfer endpoint.

This service has three intentional bugs:
1. Race condition: reads balance then writes without atomic transaction
2. Missing authentication: any user can transfer from any account
3. Broken test: mocked incorrectly, always passes even when bug exists
"""

from flask import Flask, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

# In-memory account store (normally a database)
accounts = {
    'user1': {'balance': 1000, 'user_id': 'user1'},
    'user2': {'balance': 500, 'user_id': 'user2'},
}


@app.route('/balance/<user_id>', methods=['GET'])
def get_balance(user_id):
    """Get account balance."""
    if user_id not in accounts:
        return jsonify({'error': 'Account not found'}), 404
    return jsonify({'user_id': user_id, 'balance': accounts[user_id]['balance']})


@app.route('/transfer', methods=['POST'])
def transfer():
    """
    Transfer money from one account to another.
    
    BUG 1: Race condition - reads balance, then updates without locking
    BUG 2: Missing authentication - doesn't verify requester owns source account
    
    Request body: {
        "from_user": "user1",
        "to_user": "user2", 
        "amount": 100
    }
    """
    data = request.get_json()
    from_user = data.get('from_user')
    to_user = data.get('to_user')
    amount = data.get('amount', 0)
    
    # BUG 2: No authentication check here! Anyone can transfer from any account.
    # Should check: if request.user.id != from_user: return 403
    
    if from_user not in accounts or to_user not in accounts:
        return jsonify({'error': 'Invalid account'}), 400
    
    # BUG 1: Race condition - read and write are separate operations
    # If two requests happen simultaneously, one will overwrite the other
    source_balance = accounts[from_user]['balance']  # Read
    
    if source_balance < amount:
        return jsonify({'error': 'Insufficient funds'}), 400
    
    # No atomic guarantee between read and write
    accounts[from_user]['balance'] = source_balance - amount  # Write
    accounts[to_user]['balance'] += amount
    
    return jsonify({
        'status': 'success',
        'from_user': from_user,
        'to_user': to_user,
        'amount': amount,
        'from_balance': accounts[from_user]['balance'],
        'to_balance': accounts[to_user]['balance'],
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
