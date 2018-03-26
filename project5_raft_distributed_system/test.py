#!/usr/bin/env python

import getpass, os, argparse, atexit
from run import Simulation

LEADERBOARD_OUTPUT = '/course/cs3700sp18/stats/project5/'

# Constants for tuning the difficulty of the tests
PACKETS_LOW = 500.0
PACKETS_MID = 800.0
PACKETS_HIGH = 1000.0
REPLICAS = 5.0
MAYFAIL_LOW = 0.01
MAYFAIL_HIGH = 0.1
LATENCY_LOW = 0.05 # In fractions of a second
LATENCY_MID = 0.09 
LATENCY_HIGH = 0.5

parser = argparse.ArgumentParser()
parser.add_argument("--config-directory",
                    dest='config_dir',
                    default=None,
                    help='A subdirectory for run configs')
args = parser.parse_args()

sim = None

# Attempt to kill child processes regardless of how Python shuts down (e.g. via an exception or ctrl-C)
@atexit.register
def kill_simulation():
    if sim:
        try: sim.shutdown()
        except: pass

def run_test(filename, description, requests, replicas, mayfail, tolerance, latency, log=None):
    global sim
        
    if args.config_dir: sim = Simulation(os.path.join(args.config_dir, filename))
    else: sim = Simulation(filename)

    sim.run()
    stats = sim.stats    
    sim.shutdown()
    sim = None
        
    pf = 'PASS'
    if stats.incorrect:
        print '\t\tTesting error: >0 incorrect responses to get()'
        pf = 'FAIL'
    if stats.died:
        print '\t\tTesting error: >0 replicas died unexpectedly'
        pf = 'FAIL'
    if stats.failed_get + stats.unanswered_get > requests * mayfail:
        print '\t\tTesting error: Too many failed and/or unanswered responses to client get() requests'
        pf = 'FAIL'
    if stats.failed_put + stats.unanswered_put > requests * mayfail:
        print '\t\tTesting error: Too many failed and/or unanswered responses to client put() requests'
        pf = 'FAIL'
    if stats.total_msgs > requests * replicas * 2 * tolerance:
        print '\t\tTesting error: Too many total messages'
        pf = 'FAIL'
    if stats.mean_latency > latency:
        print '\t\tTesting error: Latency of requests is too high'
        pf = 'FAIL'

    if pf == 'PASS' and log:
        log.write('%s %i %i %i %f %f\n' % (filename, stats.total_msgs, stats.failed_get + stats.unanswered_get,
                                           stats.failed_put + stats.unanswered_put,
                                           stats.mean_latency, stats.median_latency))

    print '\t%-40s\t[%s]' % (description, pf)
    return pf == 'PASS'

trials = []

print 'Basic tests (5 replicas, 30 seconds, 500 requests):'
trials.append(run_test('simple-1.json', 'No drops, no failures, 80% read',
                       PACKETS_LOW, REPLICAS, MAYFAIL_LOW, 1.2, LATENCY_LOW))
trials.append(run_test('simple-2.json', 'No drops, no failures, 20% read',
                       PACKETS_LOW, REPLICAS, MAYFAIL_LOW, 1.2, LATENCY_LOW))

print 'Unreliable network tests (5 replicas, 30 seconds, 500 requests):'
trials.append(run_test('unreliable-1.json', '5% drops, no failures, 20% read',
                       PACKETS_LOW, REPLICAS, MAYFAIL_LOW, 1.25, LATENCY_LOW))
trials.append(run_test('unreliable-2.json', '10% drops, no failures, 20% read',
                       PACKETS_LOW, REPLICAS, MAYFAIL_LOW, 1.3, LATENCY_MID))
trials.append(run_test('unreliable-3.json', '15% drops, no failures, 20% read',
                       PACKETS_LOW, REPLICAS, MAYFAIL_LOW, 1.35, LATENCY_MID))

print 'Crash failure tests (5 replicas, 30 seconds, 500 requests):'
trials.append(run_test('crash-1.json', 'No drops, 1 replica failure, 20% read',
                       PACKETS_LOW, REPLICAS, MAYFAIL_LOW, 1.2, LATENCY_LOW))
trials.append(run_test('crash-2.json', 'No drops, 2 replica failures, 20% read',
                       PACKETS_LOW, REPLICAS, MAYFAIL_LOW, 1.2, LATENCY_LOW))
trials.append(run_test('crash-3.json', 'No drops, 1 leader failure, 20% read',
                       PACKETS_LOW, REPLICAS, MAYFAIL_HIGH, 1.3, LATENCY_LOW))
trials.append(run_test('crash-4.json', 'No drops, 2 leader failures, 20% read',
                       PACKETS_LOW, REPLICAS, MAYFAIL_HIGH, 1.4, LATENCY_LOW))

print 'Partition tests (5 replicas, 30 seconds, 500 requests):'
trials.append(run_test('partition-1.json', 'No drops, 1 easy partition, 20% read',
                       PACKETS_LOW, REPLICAS, MAYFAIL_LOW, 1.3, LATENCY_LOW))
trials.append(run_test('partition-2.json', 'No drops, 2 easy partitions, 20% read',
                       PACKETS_LOW, REPLICAS, MAYFAIL_LOW, 1.4, LATENCY_LOW))
trials.append(run_test('partition-3.json', 'No drops, 1 hard partition, 20% read',
                       PACKETS_LOW, REPLICAS, MAYFAIL_HIGH, 1.5, LATENCY_HIGH))
trials.append(run_test('partition-4.json', 'No drops, 2 hard partitions, 20% read',
                       PACKETS_LOW, REPLICAS, MAYFAIL_HIGH, 1.5, LATENCY_HIGH))

ldr = open(LEADERBOARD_OUTPUT + getpass.getuser(), 'w')

print 'Bring the pain (5 replicas, 30 seconds):'
trials.append(run_test('advanced-1.json', '1000 requests, 10% drops, 2 hard partitions and 1 leader failures, 20% read',
                       PACKETS_HIGH, REPLICAS, MAYFAIL_HIGH, 1.5, LATENCY_HIGH, ldr))
trials.append(run_test('advanced-2.json', '800 requests, 15% drops, 2 leader failures, 20% read',
                       PACKETS_MID, REPLICAS, MAYFAIL_HIGH, 1.5, LATENCY_MID, ldr))
trials.append(run_test('advanced-3.json', '500 requests, 50% drops, 1 leader failure, 20% read',
                       PACKETS_LOW, REPLICAS, 0.3, 2, LATENCY_HIGH, ldr))

print 'Bonus Mode Extra Credit! (5 replicas, 30 seconds, 1000 requests):'
trials.append(run_test('advanced-4.json', '10% drops, 3 hard partions and 1 leader kill, 20% read',
                       PACKETS_HIGH, REPLICAS, MAYFAIL_HIGH, 2, LATENCY_HIGH, ldr))

print 'Passed', sum([1 for x in trials if x]), 'out of', len(trials), 'tests'
