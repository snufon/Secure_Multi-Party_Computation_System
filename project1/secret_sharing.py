"""
Secret sharing scheme.
"""

from typing import List
import random

# Prime number
Q = 6827


class Share:
    """
    A secret share in a finite field.
    """

    def __init__(self, num):
        # Adapt constructor arguments as you wish
        self.s = num

    def __repr__(self):
        # Helps with debugging.
        return f"{self.s}"

    def __add__(self, other):
        return Share((self.s + other.s) % Q)

    def __sub__(self, other):
        return Share((self.s - other.s) % Q)

    def __mul__(self, other):
        return Share((self.s * other.s) % Q)


def share_secret(secret: int, num_shares: int) -> List[Share]:
    """Generate secret shares."""
    l = []
    total = 0
    ## n-1 random shares
    for _ in range(num_shares - 1):
        # Second argument Q-1 is inclusive, we do not want both 0 and Q
        r = random.randint(0, Q-1)
        l.append(Share(r))
        total += r
    # We choose the last share so that the sum of all shares mod Q is the secret
    l.append(Share((secret-total) % Q))
    return l


def reconstruct_secret(shares: List[Share]) -> int:
    """Reconstruct the secret from shares."""
    # We assume the input contains every share, thus we can use its sum to get the secret
    total = 0
    for share in shares:
        total += share.s
    return total % Q

