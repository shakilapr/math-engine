#!/usr/bin/env python3
"""Debug float on MagicMock"""
import sys
sys.path.insert(0, 'backend')
from unittest.mock import MagicMock, patch
from core.verifier import CrossVerifier

print('Testing float on MagicMock')
m = MagicMock()
print('Mock:', m)
try:
    f = float(m)
    print('float(mock) =', f)
except Exception as e:
    print('float(mock) raised:', e)

print('\n--- Testing _results_match with mocked sympify ---')
with patch('core.verifier.sp') as mock_sp:
    mock_sp.sympify.side_effect = lambda x: MagicMock()
    mock_sp.simplify.return_value = MagicMock(__eq__=lambda self, other: False)
    result = CrossVerifier._results_match('x', 'y')
    print('Result:', result)
    print('sympify calls:', mock_sp.sympify.call_args_list)
    print('simplify calls:', mock_sp.simplify.call_args_list)
    if mock_sp.simplify.called:
        args = mock_sp.simplify.call_args[0][0]
        print('simplify argument:', args)
        # Evaluate simplify(...) == 0
        eq_result = mock_sp.simplify.return_value == 0
        print('simplify(...) == 0 yields:', eq_result)
    # Check numeric path
    try:
        sa = mock_sp.sympify('x')
        sb = mock_sp.sympify('y')
        fa = float(sa)
        fb = float(sb)
        print('float(sa) =', fa, 'float(sb) =', fb)
        print('diff =', abs(fa - fb))
        print('diff < 1e-10?', abs(fa - fb) < 1e-10)
    except Exception as e:
        print('numeric path exception:', e)

print('\n--- Testing with __eq__ returning True ---')
with patch('core.verifier.sp') as mock_sp:
    mock_sp.sympify.side_effect = lambda x: MagicMock()
    mock_sp.simplify.return_value = MagicMock(__eq__=lambda self, other: True)
    result = CrossVerifier._results_match('x', 'y')
    print('Result:', result)
    print('simplify called?', mock_sp.simplify.called)