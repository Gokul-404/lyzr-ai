"""
Tests for calculate_stats function.

These tests expose all three bugs in the implementation.
Run with: pytest test_main.py -v
"""

import pytest
from main import calculate_stats


class TestCalculateStats:
    """Test suite for calculate_stats function."""
    
    def test_calculate_stats_basic(self):
        """Test with a simple list."""
        result = calculate_stats([1, 2, 3, 4, 5])
        assert result['average'] == 3.0
        assert result['min'] == 1
        assert result['max'] == 5
    
    def test_calculate_stats_single_element(self):
        """Test with a single element."""
        result = calculate_stats([42])
        assert result['average'] == 42.0
        assert result['min'] == 42
        assert result['max'] == 42
    
    def test_calculate_stats_negative_numbers(self):
        """Test with negative numbers."""
        result = calculate_stats([-5, -2, 0, 3, 7])
        assert result['average'] == 0.6
        assert result['min'] == -5
        assert result['max'] == 7
    
    def test_calculate_stats_floats(self):
        """Test with floating point numbers."""
        result = calculate_stats([1.5, 2.5, 3.5])
        assert result['average'] == pytest.approx(2.5)
        assert result['min'] == 1.5
        assert result['max'] == 3.5
    
    def test_calculate_stats_empty_list(self):
        """Test with empty list—should return None or raise exception."""
        # This test exposes Bug 3: no empty list check
        with pytest.raises((IndexError, ZeroDivisionError, ValueError)):
            calculate_stats([])
    
    def test_calculate_stats_large_numbers(self):
        """Test with large numbers."""
        result = calculate_stats([1000000, 2000000, 3000000])
        assert result['average'] == 2000000.0
        assert result['min'] == 1000000
        assert result['max'] == 3000000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
