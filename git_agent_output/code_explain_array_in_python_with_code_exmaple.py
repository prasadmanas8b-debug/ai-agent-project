"""
This module provides an explanation of arrays in Python, along with code examples.
It covers the basics of arrays, including creation, indexing, and manipulation.
"""

import numpy as np

def create_array() -> np.ndarray:
    """
    Creates a sample array using numpy.
    
    Returns:
    np.ndarray: A 1D array with integers from 0 to 9.
    """
    return np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

def index_array(array: np.ndarray, index: int) -> int:
    """
    Retrieves an element from the array at the specified index.
    
    Args:
    array (np.ndarray): The input array.
    index (int): The index of the element to retrieve.
    
    Returns:
    int: The element at the specified index.
    """
    try:
        return array[index]
    except IndexError:
        print("Index out of bounds")
        return None

def manipulate_array(array: np.ndarray) -> np.ndarray:
    """
    Demonstrates basic array manipulation operations.
    
    Args:
    array (np.ndarray): The input array.
    
    Returns:
    np.ndarray: The modified array.
    """
    # Append a new element to the array
    array = np.append(array, 10)
    
    # Insert a new element at a specific position
    array = np.insert(array, 0, -1)
    
    # Remove the first occurrence of a specified value
    array = np.delete(array, np.where(array == 0))
    
    return array

if __name__ == "__main__":
    array = create_array()
    print("Original array:", array)
    
    index = 5
    print("Element at index", index, ":", index_array(array, index))
    
    modified_array = manipulate_array(array)
    print("Modified array:", modified_array)