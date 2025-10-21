
import numpy as np
import pytest
from bot.trading_engine import convert_numpy_types

def test_convert_numpy_types():
    """
    Tests the convert_numpy_types function to ensure it correctly converts
    various NumPy data types to their standard Python equivalents.
    """
    # Test case 1: Simple dictionary with NumPy types
    data1 = {
        'integer': np.int64(10),
        'float': np.float64(20.5),
        'boolean': np.bool_(True),
        'array': np.array([1, 2, 3])
    }
    expected1 = {
        'integer': 10,
        'float': 20.5,
        'boolean': True,
        'array': [1, 2, 3]
    }
    assert convert_numpy_types(data1) == expected1

    # Test case 2: Nested dictionary
    data2 = {
        'level1': {
            'integer': np.int32(5),
            'boolean': np.bool_(False)
        },
        'float': np.float32(99.9)
    }
    expected2 = {
        'level1': {
            'integer': 5,
            'boolean': False
        },
        'float': 99.9
    }
    converted_data2 = convert_numpy_types(data2)
    assert converted_data2['level1'] == expected2['level1']
    assert converted_data2['float'] == pytest.approx(expected2['float'])

    # Test case 3: List of NumPy types
    data3 = [np.int16(1), np.float16(2.0), np.bool_(True)]
    expected3 = [1, 2.0, True]
    assert convert_numpy_types(data3) == expected3

    # Test case 4: List of dictionaries
    data4 = [
        {'value': np.int64(1)},
        {'value': np.bool_(False)}
    ]
    expected4 = [
        {'value': 1},
        {'value': False}
    ]
    assert convert_numpy_types(data4) == expected4

    # Test case 5: No NumPy types
    data5 = {'a': 1, 'b': 'hello', 'c': [1, 2, 3]}
    expected5 = {'a': 1, 'b': 'hello', 'c': [1, 2, 3]}
    assert convert_numpy_types(data5) == expected5
