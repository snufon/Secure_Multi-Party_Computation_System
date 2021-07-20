

import time
from multiprocessing import Process, Queue

import pytest
import random
from secret_sharing import Q

from expression import Scalar, Secret
from protocol import ProtocolSpec
from server import run

from smc_party import SMCParty


def smc_client(client_id, prot, value_dict, queue):
    cli = SMCParty(
        client_id,
        "localhost",
        5000,
        protocol_spec=prot,
        value_dict=value_dict
    )
    res = cli.run()
    queue.put(res)
    print(f"{client_id} has finished!")


def smc_server(args):
    run("localhost", 5000, args)


def run_processes(server_args, *client_args):
    queue = Queue()

    server = Process(target=smc_server, args=(server_args,))
    clients = [Process(target=smc_client, args=(*args, queue))
               for args in client_args]

    server.start()
    time.sleep(3)
    for client in clients:
        client.start()

    results = list()
    for client in clients:
        client.join()

    for client in clients:
        results.append(queue.get())

    server.terminate()
    server.join()

    # To "ensure" the workers are dead.
    time.sleep(2)

    print("Server stopped.")

    return results


def suite(parties, expr, expected):
    participants = list(parties.keys())

    prot = ProtocolSpec(expr=expr, participant_ids=participants)
    clients = [(name, prot, value_dict)
               for name, value_dict in parties.items()]

    results = run_processes(participants, *clients)

    for result in results:
        assert result == expected


def test_application():
    """
    f(a, b, cN, cA, cB) = (a*cA) - (b*cB) + cN
    """
    alice_secret = Secret()
    bob_secret = Secret()
    charlie_noise = Secret()
    charlie_multA = Secret()
    charlie_multB = Secret()

    parties = {
        "Alice": {alice_secret: 3},
        "Bob": {bob_secret: 4},
        "Charlie": {charlie_noise: 2,
                    charlie_multA: 11,
                    charlie_multB: 9}
    }

    expr = (
        (alice_secret * charlie_multA) -
        (bob_secret * charlie_multB)
        + charlie_noise
    )
    expected = ((3 * 11) - (4 * 9) + 2) % Q
    suite(parties, expr, expected)


def test_application_randomized():
    """
    f(a, b, cN, cA, cB) = (a*cA) - (b*cB) + cN
    """
    alice_secret = Secret()
    bob_secret = Secret()
    charlie_noise = Secret()
    charlie_multA = Secret()
    charlie_multB = Secret()

    ## A score of 0 should be avoided since it would not be impacted by multiplicators
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    cN = random.randint(1, 5)
    ## Giving too much power to player C with a high multiplicator range would allow him to single-handedly decide who wins
    ## between players A and B and encourage him to cooperate with one of them, hence the realistic 9 to 11 range.
    cA = random.randint(9, 11)  
    cB = random.randint(9, 11)

    parties = {
        "Alice": {alice_secret: a},
        "Bob": {bob_secret: b},
        "Charlie": {charlie_noise: cN,
                    charlie_multA: cA,
                    charlie_multB: cB}
    }

    expr = (
        (alice_secret * charlie_multA) -
        (bob_secret * charlie_multB)
        + charlie_noise
    )
    expected = ((a * cA) - (b * cB) + cN) % Q
    suite(parties, expr, expected)
