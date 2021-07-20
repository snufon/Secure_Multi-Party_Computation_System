import time
from multiprocessing import Process, Queue
from functools import reduce

import pytest

from expression import Scalar, Secret, gen_id
from protocol import ProtocolSpec
from server import run

from smc_party import SMCParty
import pandas as pd
import random

Q = 6827


def smc_client(client_id, prot, value_dict, queue,times):
    cli = SMCParty(
        client_id,
        "localhost",
        5000,
        protocol_spec=prot,
        value_dict=value_dict
    )

    start = time.time()
    res = cli.run()
    end = time.time()
    queue.put(res)
    times.put(end-start)
    print(f"{client_id} has finished!")


def smc_server(args):
    run("localhost", 5000, args)


def run_processes(server_args, *client_args):
    queue = Queue()
    times = Queue()

    server = Process(target=smc_server, args=(server_args,))
    clients = [Process(target=smc_client, args=(*args, queue, times))
               for args in client_args]

    server.start()
    time.sleep(3)
    for client in clients:
        client.start()

    results = list()
    times_res = list()
    for client in clients:
        client.join()

    for client in clients:
        results.append(queue.get())
        times_res.append(times.get())

    server.terminate()
    server.join()

    # To "ensure" the workers are dead.
    time.sleep(2)

    print("Server stopped.")

    return results,times_res


def suite(parties, expr, expected):
    participants = list(parties.keys())

    prot = ProtocolSpec(expr=expr, participant_ids=participants)
    clients = [(name, prot, value_dict)
               for name, value_dict in parties.items()]

    results,times = run_processes(participants, *clients)

    for result in results:
        assert result == expected

    return times


#Does the performance evalutation for secret addition and saves the measurments in a csv (also tests that every circuit works)
def test_perf_add():

    import sys
    lim = sys.getrecursionlimit()
    sys.setrecursionlimit(4000)

    nb_add = [4 ,20, 100, 500,1000]
    clients = ["Alice", "Bob", "Charlie", "Dave"]
    stats = pd.DataFrame(columns = nb_add)


    for n in nb_add:

        times = []

        for run in range(10):

            #to avoid hitting pythons's recursion ceiling
            expressions = [Scalar(0),Scalar(0),Scalar(0),Scalar(0)]
            expected = 0

            parties = {
                "Alice": {},
                "Bob": {},
                "Charlie": {},
                "Dave": {}
            }

            #generates secrets for all 4 parties
            for j in range(int(n/4)):
                secrets = [Secret(), Secret(), Secret(), Secret()]

                for i, c in enumerate(clients):
                    r = random.randint(0, Q-1)
                    parties[c][secrets[i]] = r
                    expressions[i] = expressions[i] + secrets[i]
                    expected = expected + r


            expression = reduce(lambda a,b: a + b, expressions)
            expected = expected % Q

            times.extend(suite(parties, expression, expected))

        stats[n] = times
    
    stats.to_csv("stats_add.csv")

#Does the performance evalutation for secret multiplication and saves the measurments in a csv (also tests that every circuit works)
def test_perf_mul():

    import sys
    lim = sys.getrecursionlimit()
    sys.setrecursionlimit(4000)

    nb_mul = [4 ,20, 100, 500,1000]
    clients = ["Alice", "Bob", "Charlie", "Dave"]
    stats = pd.DataFrame(columns = nb_mul)


    for n in nb_mul:

        times = []

        for run in range(10):

            #to avoid hitting pythons's recursion ceiling, we do 4 epxression that we then multiply
            expressions = [Scalar(1),Scalar(1),Scalar(1),Scalar(1)]
            expected = 1

            #generates secrets for all 4 parties
            parties = {
                "Alice": {},
                "Bob": {},
                "Charlie": {},
                "Dave": {}
            }

            for j in range(int(n/4)):
                secrets = [Secret(), Secret(), Secret(), Secret()]

                for i, c in enumerate(clients):
                    r = random.randint(1, Q-1)
                    parties[c][secrets[i]] = r
                    expressions[i] = expressions[i] * secrets[i]
                    expected = expected * r


            expression = reduce(lambda a,b: a * b, expressions)
            expected = expected % Q

            times.extend(suite(parties, expression, expected))

        stats[n] = times
    
    stats.to_csv("stats_mul.csv")


#Does the performance evalutation for scalar addition and saves the measurments in a csv (also tests that every circuit works)
def test_perf_add_scalar():

    import sys
    lim = sys.getrecursionlimit()
    sys.setrecursionlimit(4000)

    nb_add = [4 ,20, 100, 500,1000]
    clients = ["Alice", "Bob", "Charlie", "Dave"]
    stats = pd.DataFrame(columns = nb_add)


    for n in nb_add:

        times = []

        for run in range(10):

            #to avoid hitting pythons's recursion ceiling
            expressions = [Secret(),Secret(),Secret(),Secret()]
            expected = 0

            parties = {
                "Alice": {expressions[0]: 0},
                "Bob": {expressions[1]: 0},
                "Charlie": {expressions[2]: 0},
                "Dave": {expressions[3]: 0}
            }

            #generates the tested amount of scalars
            for j in range(n):
                r = random.randint(0, Q-1)
                expressions[j%4] = expressions[j%4] + Scalar(r)
                expected = expected + r

            expression = reduce(lambda a,b: a + b, expressions)
            expected = expected % Q

            times.extend(suite(parties, expression, expected))

        stats[n] = times
    
    stats.to_csv("stats_add_scalar.csv")

#Does the performance evalutation for scalar multiplication and saves the measurments in a csv (also tests that every circuit works)
def test_perf_mul_scalar():

    import sys
    lim = sys.getrecursionlimit()
    sys.setrecursionlimit(4000)

    nb_mul = [4 ,20, 100, 500,1000]
    clients = ["Alice", "Bob", "Charlie", "Dave"]
    stats = pd.DataFrame(columns = nb_mul)


    for n in nb_mul:

        times = []

        for run in range(10):

            #to avoid hitting pythons's recursion ceiling
            expressions = [Secret(),Secret(),Secret(),Secret()]
            expected = 1

            parties = {
                "Alice": {expressions[0]: 1},
                "Bob": {expressions[1]: 1},
                "Charlie": {expressions[2]: 1},
                "Dave": {expressions[3]: 1}
            }

            #generates the tested amount of scalars
            for j in range(n):
                r = random.randint(1, Q-1)
                expressions[j%4] = expressions[j%4] * Scalar(r)
                expected = expected * r

            expression = reduce(lambda a,b: a * b, expressions)
            expected = expected % Q

            times.extend(suite(parties, expression, expected))

        stats[n] = times
    
    stats.to_csv("stats_mul_scalar.csv")


#Does the performance evalutation of th effect of number of parties and saves the measurments in a csv (also tests that every circuit works)
def test_perf_parties():

    import sys
    lim = sys.getrecursionlimit()
    sys.setrecursionlimit(4000)

    nb_parties = [2 ,10, 25, 50, 100]
    stats = pd.DataFrame(columns = ["nb_parties","time"])

    secrets = []

    #cretaing 100 secrets that we will share between all parties
    for i in range(100):
        secrets.append(Secret())

    #columns of our stats dataframe
        times = []
        nb_p = []


    for n in nb_parties:
  
        clients = []

        #creating n random clients
        for c in range(n):
            clients.append(str(gen_id()))

        for run in range(10):

            parties = {}
            expected = 0

            #distributes the 100 secrets equally among all tested parties
            for i,c in enumerate(clients):
                parties[c] = {}

                for j in range(i * int(100/n), (i + 1) * int(100/n)):
                    r = random.randint(0, Q-1)
                    parties[c][secrets[j]] = r
                    expected += r


            expression = reduce(lambda a,b: a + b, secrets)
            expected = expected % Q

            res = suite(parties, expression, expected)
            times.extend(res)
            nb_p.extend([n for i in range(len(res))])

    stats["nb_parties"] = nb_p
    stats["time"] = times
    
    stats.to_csv("stats_parties.csv")