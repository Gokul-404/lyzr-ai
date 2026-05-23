"""
calculate_stats function with intentional bugs.

This module contains a function to calculate statistics (average, min, max)
on a list of numbers. It has three intentional bugs that must be fixed.
"""


def calculate_stats(numbers):
    """
    Calculate average, minimum, and maximum of a list of numbers.
    
    Args:
        numbers: List of numeric values
    
    Returns:
        Dictionary with 'average', 'min', and 'max' keys
    
    BUG 1: Off-by-one error in average calculation
    BUG 2: Wrong comparison operator in max detection  
    BUG 3: No null/empty list check
    """
    # Bug 3: This will crash on empty list
    total = sum(numbers)
    # Bug 1: Dividing by len(numbers) + 1 instead of len(numbers)
    average = total / (len(numbers) + 1)
    
    min_val = numbers[0]
    max_val = numbers[0]
    
    for num in numbers[1:]:
        if num < min_val:
            min_val = num
        # Bug 2: Using < instead of > for max check
        if num < max_val:
            max_val = num
    
    return {
        'average': average,
        'min': min_val,
        'max': max_val
    }
