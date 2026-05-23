"""
Tests for Flask transfer endpoint.

One of these tests is incorrectly mocked and doesn't catch the bugs.
Run with: pytest test_app.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
import json
from app import app, accounts


@pytest.fixture
def client():
    """Create a test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestTransferEndpoint:
    """Test suite for /transfer endpoint."""
    
    def test_transfer_success(self, client):
        """Test successful transfer."""
        response = client.post('/transfer', 
            json={'from_user': 'user1', 'to_user': 'user2', 'amount': 100},
            content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['amount'] == 100
    
    def test_transfer_insufficient_funds(self, client):
        """Test transfer with insufficient funds."""
        response = client.post('/transfer',
            json={'from_user': 'user1', 'to_user': 'user2', 'amount': 5000},
            content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_transfer_invalid_account(self, client):
        """Test transfer to non-existent account."""
        response = client.post('/transfer',
            json={'from_user': 'user1', 'to_user': 'nonexistent', 'amount': 100},
            content_type='application/json')
        
        assert response.status_code == 400
    
    # BUG 3: This test is incorrectly mocked and always passes
    # It mocks the entire accounts dict, so it never catches the race condition
    @patch('app.accounts')
    def test_transfer_authentication_check(self, mock_accounts, client):
        """
        Test that authentication is verified.
        
        BUG: This test is mocked incorrectly—it patches accounts entirely,
        so the missing auth check is never triggered. The test always passes
        even though the bug exists.
        """
        mock_accounts.__getitem__.side_effect = lambda x: {'balance': 1000}
        mock_accounts.__contains__.return_value = True
        
        # This should fail if auth is not checked, but the mock hides the bug
        response = client.post('/transfer',
            json={'from_user': 'user1', 'to_user': 'user2', 'amount': 100},
            content_type='application/json')
        
        # Test passes because we're mocking accounts, but auth is never checked!
        assert response.status_code == 200
    
    def test_get_balance(self, client):
        """Test balance retrieval."""
        response = client.get('/balance/user1')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user_id'] == 'user1'
        assert 'balance' in data
    
    def test_health_check(self, client):
        """Test health endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
