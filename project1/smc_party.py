"""
Implementation of an SMC client.

MODIFY THIS FILE.
"""
# You might want to import more classes if needed.

import collections
import json
import time

from ttp import TrustedParamGenerator

from typing import (
    Dict,
    Set,
    Tuple,
    Union
)

from communication import Communication
from expression import (
    Expression,
    Secret,
    Scalar,
    Addition,
    Substraction,
    Multiplication
)
from protocol import ProtocolSpec
from secret_sharing import(
    reconstruct_secret,
    share_secret,
    Share,
)

# Feel free to add as many imports as you want.


class SMCParty:
    """
    A client that executes an SMC protocol to collectively compute a value of an expression together
    with other clients.

    Attributes:
        client_id: Identifier of this client
        server_host: hostname of the server
        server_port: port of the server
        protocol_spec (ProtocolSpec): Protocol specification
        value_dict (dict): Dictionary assigning values to secrets belonging to this client.
    """

    def __init__(
        self,
        client_id: str,
        server_host: str,
        server_port: int,
        protocol_spec: ProtocolSpec,
        value_dict: Dict[Secret, int]
    ):
        self.comm = Communication(server_host, server_port, client_id)

        self.client_id = client_id
        self.protocol_spec = protocol_spec
        self.value_dict = value_dict

    def run(self) -> int:
        """
        The method the client use to do the SMC.
        """

        # There can be multiple keys per participant in our own application
        for key in self.value_dict:
            value = self.value_dict[key]
            n = len(self.protocol_spec.participant_ids)
            shares = share_secret(value, n)
            # Privately send each share to each participant (including the client itself for simplicity)
            for i in range(n):
                self.comm.send_private_message(
                    self.protocol_spec.participant_ids[i], str(key.id), str(shares[i].s))


        share = self.process_expression(self.protocol_spec.expr)
        self.comm.publish_message(
            str(self.protocol_spec.expr.id), str(share.s))

        shares = []
        # We retrieve every public share from the final output
        for id in self.protocol_spec.participant_ids:
            shares.append(Share(int(
                self.comm.retrieve_public_message(id, str(self.protocol_spec.expr.id)))))

        return reconstruct_secret(shares)


    def process_expression(
        self,
        expr: Expression,
    ) -> Share:

        # if expr is an addition operation:
        if isinstance(expr, Addition):

            #if addition of scalar, then we must only add it to the share of the client with the "smallest" client_id
            if isinstance(expr.left, Scalar):
                if self.client_id == min(self.protocol_spec.participant_ids):
                    return self.process_expression(expr.left) + self.process_expression(expr.right)
                else:
                    return self.process_expression(expr.right)

            #same but if the scalar is on the right hand side
            elif isinstance(expr.right, Scalar):
                if self.client_id == min(self.protocol_spec.participant_ids):
                    return self.process_expression(expr.left) + self.process_expression(expr.right)
                else:
                    return self.process_expression(expr.left)


            # if addition between two expr
            else:
                return self.process_expression(expr.left) + self.process_expression(expr.right)

        
        
        # if expr is an substraction operation:
        if isinstance(expr, Substraction):

            #if substraction of scalar, then we must only substract it to the share of the client with the "smallest" client_id
            if isinstance(expr.left, Scalar):
                if self.client_id == min(self.protocol_spec.participant_ids):
                    return self.process_expression(expr.left) - self.process_expression(expr.right)
                else:
                    return self.process_expression(expr.right)

            #same but if the scalar is on the right hand side
            elif isinstance(expr.right, Scalar):
                if self.client_id == min(self.protocol_spec.participant_ids):
                    return self.process_expression(expr.left) - self.process_expression(expr.right)
                else:
                    return self.process_expression(expr.left)


            # if substraction between two expr
            else:
                return self.process_expression(expr.left) - self.process_expression(expr.right)

        
        
        # if expr is a multiplication operation:
        if isinstance(expr, Multiplication):

            #if scalar multiplication
            if isinstance(expr.left, Scalar) or isinstance(expr.right, Scalar):
                return self.process_expression(expr.left) * self.process_expression(expr.right)

            #if multiplication between two expr
            else :
                #get beaver triplets share for given operation
                a,b,c = self.comm.retrieve_beaver_triplet_shares(str(expr.id))
                x = self.process_expression(expr.left) 
                y = self.process_expression(expr.right) 

                x_a = x - Share(a)
                y_b = y - Share(b)

                #publishing shares for both x-a and y-b (label for x - a is the string expr.id + '1' and for y-b is expr.id + '2')
                self.comm.publish_message(
                    str(expr.id) + "1", str(x_a.s))
                self.comm.publish_message(
                    str(expr.id) + "2", str(y_b.s))

                #retrieve every public share for x-a and y-b to reconstruct them
                shares_x_a = []
                shares_y_b = []
                
                for id in self.protocol_spec.participant_ids:
                    shares_x_a.append(Share(int(
                        self.comm.retrieve_public_message(id, str(expr.id) + "1"))))
                    shares_y_b.append(Share(int(
                        self.comm.retrieve_public_message(id, str(expr.id) + "2"))))

                #reconstructing x-a and y-b
                full_x_a = Share(reconstruct_secret(shares_x_a))
                full_y_b = Share(reconstruct_secret(shares_y_b))

                share_z = Share(c) + (x * full_y_b) + (y * full_x_a)

                #done only for one client
                if self.client_id == min(self.protocol_spec.participant_ids):
                    share_z = share_z - (full_x_a * full_y_b)

                return share_z



        # if expr is a secret:
        if isinstance(expr, Secret):
            share = int(self.comm.retrieve_private_message(str(expr.id)))
            return Share(share)

        # if expr is a scalar:
        if isinstance(expr, Scalar):
            return Share(expr.value)
