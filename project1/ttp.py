"""
Trusted parameters generator.

MODIFY THIS FILE.
"""

import collections
from typing import (
    Dict,
    Set,
    Tuple,
)

from communication import Communication
from secret_sharing import(
    share_secret,
    Share,
)

import random
Q = 6827

# Feel free to add as many imports as you want.


class TrustedParamGenerator:
    """
    A trusted third party that generates random values for the Beaver triplet multiplication scheme.
    """

    def __init__(self):
        self.participant_ids: Set[str] = set()
        self.triplets = dict()


    def add_participant(self, participant_id: str) -> None:
        """
        Add a participant.
        """
        self.participant_ids.add(participant_id)

    def retrieve_share(self, client_id: str, op_id: str) -> Tuple[Share, Share, Share]:
        """
        Retrieve a triplet of shares for a given client_id.
        """
        #if triplet already generated for given operation, get the shares for the given client
        if op_id in self.triplets:
            return self.triplets[op_id][client_id]

        #else generate the triplet for the operation
        else:
            #get random a,b and c
            a = random.randint(0, Q - 1)
            b = random.randint(0, Q - 1)
            c = a * b

            #get shares for a,b and c
            shares_a = share_secret(a, len(self.participant_ids))
            shares_b = share_secret(b, len(self.participant_ids))
            shares_c = share_secret(c, len(self.participant_ids))

            #save them in the dictionarry to be accessed again
            self.triplets[op_id] = dict((cl_id,(a,b,c)) for cl_id,a,b,c in zip(list(self.participant_ids), shares_a, shares_b, shares_c))

            return self.triplets[op_id][client_id]

        

    # Feel free to add as many methods as you want.
