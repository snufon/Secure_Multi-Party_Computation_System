"""
Unit tests for the secret sharing scheme.
Testing secret sharing is not obligatory.

MODIFY THIS FILE.
"""

from secret_sharing import *


def test_1():
	shares = share_secret(52 ,13)
	secret = reconstruct_secret(shares)
	assert (secret == 52)

def test_2():
	shares = share_secret(2598 ,5)
	secret = reconstruct_secret(shares)
	assert (secret == 2598)

def test_3():
	shares = share_secret(135 ,20)
	secret = reconstruct_secret(shares)
	assert (secret == 135)
