"""
This module provides an explanation of arrays in Python, along with code examples.
It covers the basics of arrays, including creation, indexing, and common operations.
"""

import numpy as np

def create_array() -> np.ndarray:
    """
    Creates a sample array with integers from 0 to 9.
    
    Returns:
    np.ndarray: A numpy array with integers from 0 to 9.
    """
    return np.arange(10)

def index_array(array: np.ndarray, index: int) -> int:
    """
    Retrieves the element at the specified index from the given array.
    
    Args:
    array (np.ndarray): The input array.
    index (int): The index of the element to retrieve.
    
    Returns:
    int: The element at the specified index.
    """
    return array[index]

def modify_array(array: np.ndarray, index: int, value: int) -> np.ndarray:
    """
    Modifies the element at the specified index in the given array.
    
    Args:
    array (np.ndarray): The input array.
    index (int): The index of the element to modify.
    value (int): The new value for the element.
    
    Returns:
    np.ndarray: The modified array.
    """
    array[index] = value
    return array

def main():
    # Create a sample array
    array = create_array()
    print("Original array:", array)
    
    # Retrieve an element from the array
    index = 5
    element = index_array(array, index)
    print(f"Element at index {index}: {element}")
    
    # Modify an element in the array
    new_value = 10
    modified_array = modify_array(array, index, new_value)
    print("Modified array:", modified_array)

if __name__ == "__main__":
    main()