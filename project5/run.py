#!/usr/bin/env python

import sys, os, time, json, socket, select, random, subprocess, string, hashlib, bisect, atexit

VERSION = "0.6"

REPLICA_PROG = './3700kvstore'
NUM_CLIENTS = 8

#######################################################################################################

# Parses and validates config files for simulations
class Config:
    def __init__(self, filename):
        # load the json
        conf = json.loads(open(filename).read())

        # check for required fields
        if 'lifetime' not in conf or 'replicas' not in conf or 'requests' not in conf:
            raise AttributeError("Required field is missing from the config file")
        
        # load the required fields and sanity check them
        self.lifetime = int(conf['lifetime'])
        if self.lifetime < 5:
            raise ValueError("Simulation lifetime must be at least 5 seconds")
        self.replicas = int(conf['replicas'])
        if self.replicas < 3 or self.replicas > 21:
            raise ValueError("Number of replicas must be at least 3 and at most 21")
        self.requests = int(conf['requests'])
        if self.requests < 0:
            raise ValueError("Number of requests cannot be negative")

        # initialize the random number generator
        if 'seed' in conf: self.seed = conf['seed']
        else: self.seed = None
        random.seed(self.seed)
        
        # load the default variables
        self.mix = self.__get_default__(conf, 'mix', 0, 1, 0.8, "Read/Write mix must be between 0 and 1")
        self.start_wait = self.__get_default__(conf, 'start_wait', 0, self.lifetime, 2.0,
            "Start wait must be between 0 and %s" % (self.lifetime))
        self.end_wait = self.__get_default__(conf, 'end_wait', 0, self.lifetime, 2.0,
            "End wait must be between 0 and %s" % (self.lifetime))
        self.drops = self.__get_default__(conf, 'drops', 0, 1, 0.0, "Drops must be between 0 and 1")
        self.max_packets = self.__get_default__(conf, 'max_packets', self.requests, 900000,
                                                20000, "max_packets must be between %i and %i" %
                                                (self.requests, 900000))
        
        if 'events' in conf: self.events = conf['events']
        else: self.events = []

        # sanity check the events
        for event in self.events:
            if event['type'] not in ['kill_leader', 'kill_non_leader', 'part_easy', 'part_hard', 'part_end']:
                raise ValueError("Unknown event type: %s" % (event['type']))
            if event['time'] < 0 or event['time'] > self.lifetime:
                raise ValueError("Event time must be between 0 and %s" % (self.lifetime))

    def __get_default__(self, conf, field, low, high, default, exception):
        if field in conf:
            temp = float(conf[field])
            if temp < low or temp > high:
                raise ValueError(exception)
        else: temp = default
        return temp
    
    def dump(self):
        print ('%8s %s\n' * 9) % ('Lifetime', self.lifetime, 'Replicas', self.replicas,
                                  'Requests', self.requests, 'Seed', self.seed,
                                  'Mix', self.mix, 'Start Wait', self.start_wait,
                                  'End Wait', self.end_wait, 'Drops', self.drops,
                                  'Max Packets', self.max_packets),
        for event in self.events:
            print '%8s %15s %s' % ('Event', event['type'], event['time'])

#######################################################################################################

class Stats:
    def __init__(self):
        self.total_msgs = 0
        self.total_drops = 0
        self.total_get = 0
        self.total_put = 0
        self.failed_get = 0
        self.failed_put = 0
        self.incorrect = 0
        self.duplicates = 0
        self.unanswered_get = 0
        self.unanswered_put = 0
        self.redirects = 0
        self.latencies = []
        self.died = 0
        self.killed = 0
        self.mean_latency = 0.0
        self.median_latency = 0.0                        
        self.leaders = []

    def add_leader(self, ldr):
        if len(self.leaders) == 0 or self.leaders[-1] != ldr:
            self.leaders.append(ldr)
        
    def finalize(self):
        if len(self.latencies) > 0:
            self.latencies.sort()
            self.mean_latency = float(sum(self.latencies))/len(self.latencies)
            self.median_latency = self.latencies[len(self.latencies)/2]

    def dump(self):
        print 'Simulation finished.'
        print 'Leaders:', ' '.join(self.leaders)
        print 'Replicas that died/were killed: %i/%i' % (self.died, self.killed)
        print 'Total messages sent:', self.total_msgs
        print 'Total messages dropped:', self.total_drops
        print 'Total client get()/put() requests: %i/%i' % (self.total_get, self.total_put)
        print 'Total duplicate responses:', self.duplicates
        print 'Total unanswered get()/put() requests: %i/%i' % (self.unanswered_get, self.unanswered_put)
        print 'Total redirects:', self.redirects
        print 'Total get()/put() failures: %i/%i' % (self.failed_get, self.failed_put)
        print 'Total get() with incorrect response:', self.incorrect
        if len(self.latencies) > 0:
            print 'Mean/Median query latency: %fsec/%fsec' % (float(sum(self.latencies))/len(self.latencies),
                                                              self.latencies[len(self.latencies)/2])


#######################################################################################################

class Client:
    class Request:
        def __init__(self, get, key, val=None):
            self.get = get
            self.key = key
            self.val = val
            self.ts = time.time()

    def __init__(self, simulator, cid):
        self.reqs = {}
        self.items = {}
        self.completed = set()
        self.sim = simulator
        self.cid = cid
        self.leader = 'FFFF'

    def forget(self):
        self.leader = 'FFFF'
        
    def __get_rand_str__(self, size=16, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def __get_destination__(self):
        if self.leader == 'FFFF' or self.leader not in self.sim.living_rids:
            self.leader = 'FFFF'
            return random.choice(list(self.sim.living_rids))
        return self.leader
    
    def __create_get__(self, key):
        self.sim.stats.total_get += 1
        mid = self.__get_rand_str__()
        self.reqs[mid] = self.Request(True, key)
        dst = self.__get_destination__()
        return {'src': self.cid, 'dst': dst, 'leader': self.leader,
                'type': 'get', 'MID': mid, 'key': key}
        
    def __create_put__(self, key, value):
        self.sim.stats.total_put += 1
        mid = self.__get_rand_str__()
        self.reqs[mid] = self.Request(False, key, value)
        dst = self.__get_destination__()
        return {'src': self.cid, 'dst': dst, 'leader': self.leader,
                'type': 'put', 'MID': mid, 'key': key, 'value': value}

    def finalize(self):
        for req in self.reqs.itervalues():
            if req.get: self.sim.stats.unanswered_get += 1
            else: self.sim.stats.unanswered_put += 1
        
    def create_req(self, get=True):
        # create a get message, if possible
        if get and len(self.items) > 0:
            return self.__create_get__(random.choice(self.items.keys()))
        
        # decide to add a new key, or update an existing key
        if len(self.items) == 0 or random.random() > 0.5:
            k = self.__get_rand_str__(size=32)
            v = hashlib.md5(k).hexdigest()
        else:
            k = random.choice(self.items.keys())
            v = hashlib.md5(self.items[k]).hexdigest()
        return self.__create_put__(k, v)
                    
    def deliver(self, raw_msg, msg):
        # validate the message
        if 'MID' not in msg:
            print "*** Simulator Error - Message missing mid field: %s" % (raw_msg)
            self.sim.stats.incorrect += 1
            return None
        if msg['type'] not in ['ok', 'fail', 'redirect']:
            print "*** Simulator Error - Unknown message type sent to client: %s" % (raw_msg)
            self.sim.stats.incorrect += 1
            return None
        
        mid = msg['MID']

        # is this a duplicate?
        if mid in self.completed:
            self.sim.stats.duplicates += 1
            return None
        
        # is this a message that I'm expecting?
        try:
            req = self.reqs[mid]
        except:
            print "*** Simulator Error - client received an unexpected MID: %s" % (raw_msg)
            self.sim.stats.incorrect += 1
            return None
        
        del self.reqs[mid]
        self.leader = msg['leader']
        self.sim.stats.latencies.append(time.time() - req.ts)
        
        # if this is a redirect or a fail, try again
        if msg['type'] in ['redirect', 'fail']:
            if req.get:
                if msg['type'] == 'fail': self.sim.stats.failed_get += 1
                self.sim.stats.redirects += 1
                return self.__create_get__(req.key)            
            if msg['type'] == 'fail': self.sim.stats.failed_put += 1            
            self.sim.stats.redirects += 1
            return self.__create_put__(req.key, req.val)
        
        # msg type must be ok, mark it as completed
        self.completed.add(mid)
        if req.get:
            if 'value' not in msg:
                print "*** Simulator Error - get() response missing the value of the key: %s" % (raw_msg)
                self.sim.stats.incorrect += 1
    
            if self.items[req.key] != msg['value']:
                print "*** Simulator Error - client received an incorrect value for a key: %s" % (raw_msg)
                self.sim.stats.incorrect += 1
        else:
            self.items[req.key] = req.val
        
        return None

#######################################################################################################

# Represents a replica, the associated process, and it's sockets
class Replica:
    def __init__(self, rid):
        self.rid = rid
        self.client_sock = None
        self.alive = False
        
        # try and delete the old domain socket, just in case
        try: os.unlink(rid)
        except: pass

        # create the listen socket for this replica
        self.listen_sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        self.listen_sock.bind(rid)
        self.listen_sock.listen(1)

    def run(self, rids):
        args = [REPLICA_PROG, self.rid]
        args.extend(rids - set([self.rid]))
        self.proc = subprocess.Popen(args)
        self.alive = True
        
    def shutdown(self):
        if self.alive:
            self.alive = False
            if self.client_sock: self.client_sock.close()
            self.listen_sock.close()
            self.listen_sock = None
            self.client_sock = None
            self.proc.kill()
            self.proc.wait()
            os.unlink(self.rid)

    def deliver(self, raw_msg):
        if self.alive:
            try:
                self.client_sock.send(raw_msg)
                return True
            except:
                print '*** Simulator Error - Unable to send to replica'
                self.shutdown()
        return False
                                
#######################################################################################################

# Represents and executes the entire simulation
class Simulation:        
    def __init__(self, filename):
        self.leader = 'FFFF'
        self.events = []
        
        # stats tracking
        self.stats = Stats()
                
        # virtual network partitions
        self.partition = None
                
        # Load the config file
        self.conf = Config(filename)
        #self.conf.dump()
        
        # Create the clients
        self.cids = set()
        self.clients = {}
        for i in xrange(self.conf.replicas + 16, self.conf.replicas + 16 + NUM_CLIENTS):
            cid = ('%04x' % (i)).upper()
            self.cids.add(cid)
            self.clients[cid] = Client(self, cid)
                
        # Create the sockets and the replicas
        self.rids = set()
        self.replicas = {}
        for i in xrange(self.conf.replicas):
            rid = ('%04x' % (i)).upper()
            self.rids.add(rid)
            self.replicas[rid] = Replica(rid)

        self.living_rids = self.rids.copy()
    
    def run(self):
        for r in self.replicas.itervalues():
            r.run(self.rids)
        
        # initialize the clock and create all the get(), put(), and kill() events
        clock = start = time.time()
        self.__populate_event_queue__(clock)
        
        # the main event loop
        while clock - start < self.conf.lifetime and self.stats.total_msgs < self.conf.max_packets:
            # populate the list of living sockets
            sockets = []
            listen_socks = set()
            for r in self.replicas.itervalues():
                if r.listen_sock:
                    sockets.append(r.listen_sock)
                    listen_socks.add(r.listen_sock)
                if r.client_sock: sockets.append(r.client_sock)

            ready = select.select(sockets, [], [], 0.1)[0]
            
            for sock in ready:
                # if this is a listen sock, accept the connection and map it to a replica
                if sock in listen_socks: self.__accept__(sock)
                # otherwise, this is a client socket connected to a replica
                else: self.__route_msgs__(sock)

            # check the time and fire off events
            clock = time.time()
            while len(self.events) != 0 and self.events[0][0] < clock:
                self.events.pop(0)[1]()
        
        if self.stats.total_msgs >= self.conf.max_packets:
            print "*** Simulator Error - Replicas sent too many packets (>%i), possible packet storm" % (self.conf.max_packets)
        
        self.stats.died = len(self.rids) - len(self.living_rids) - self.stats.killed
        
        # Finish out the clients. All unanswered requests are considered failures
        for client in self.clients.itervalues():
            client.finalize()
        
        # Finish calculating the statistics
        self.stats.finalize()
                                
    def shutdown(self):
        for r in self.replicas.itervalues():
            try: r.shutdown()
            except: pass
                                
    def __kill_replica__(self, r):
        if r.rid in self.living_rids:
            self.stats.killed += 1
            self.living_rids.remove(r.rid)
            r.shutdown()

    def __kill_leader__(self):
        if self.leader != 'FFFF':
            self.__kill_replica__(self.replicas[self.leader])
            self.leader = 'FFFF'
            for client in self.clients.itervalues(): client.forget()
                        
    def __kill_non_leader__(self):
        if len(self.living_rids) > 1:
            self.__kill_replica__(self.replicas[random.choice(list(self.living_rids - set([self.leader])))])
        else:
            print '*** Simulator Error - too few living replicas to kill another (%i)' % (len(self.living_rids))

    def __partition__(self, add_leader=False):
        qsize = len(self.replicas) / 2 + 1
        self.partition = set()
        r = list(self.rids)

        if add_leader and self.leader != 'FFFF':
            self.partition.add(self.leader)
            r.remove(self.leader)
            qsize -= 1
        else:
            self.leader = 'FFFF'
            for client in self.clients.itervalues(): client.forget()
                        
        for i in range(qsize):
            rid = random.choice(r)
            self.partition.add(rid)
            r.remove(rid)

    def __partition_easy__(self):
        self.__partition__(True)
                        
    def __partition_hard__(self):
        self.__partition__()

    def __partition_end__(self):
        self.partition = None

    def __check_partition__(self, rid1, rid2):
        if not self.partition: return True
        i = len(self.partition & set([rid1, rid2]))
        if i == 2 or i == 0: return True
        return False
                
    def __send_get__(self):
        client = random.choice(self.clients.values())
        msg = client.create_req(True)
        self.__replica_deliver__(self.replicas[msg['dst']], json.dumps(msg))
        
    def __send_put__(self):
        client = random.choice(self.clients.values())
        msg = client.create_req(False)
        self.__replica_deliver__(self.replicas[msg['dst']], json.dumps(msg))

    def __replica_deliver__(self, replica, raw_msg):
        if not replica.deliver(raw_msg) and replica.rid in self.living_rids:
            self.living_rids.remove(replica.rid)
                        
    def __populate_event_queue__(self, clock):
        clock += self.conf.start_wait

        # Generate get() and put() events for the event queue
        t = clock
        delta = float(self.conf.lifetime - self.conf.start_wait - self.conf.end_wait) / self.conf.requests
        for i in xrange(self.conf.requests):
            if random.random() < self.conf.mix: self.events.append((t, self.__send_get__))
            else: self.events.append((t, self.__send_put__))
            t += delta
                        
        # Add any events from the config into the event queue
        for event in self.conf.events:
            if event['type'] == 'kill_leader':
                bisect.insort(self.events, (event['time'] + clock, self.__kill_leader__))
            elif event['type'] == 'kill_non_leader':
                bisect.insort(self.events, (event['time'] + clock, self.__kill_non_leader__))
            elif event['type'] == 'part_easy':
                bisect.insort(self.events, (event['time'] + clock, self.__partition_easy__))
            elif event['type'] == 'part_hard':
                bisect.insort(self.events, (event['time'] + clock, self.__partition_hard__))
            elif event['type'] == 'part_end':
                bisect.insort(self.events, (event['time'] + clock, self.__partition_end__))

    def __validate_addr__(self, addr):
        if type(addr) not in [str, unicode] or len(addr) != 4: return False
        try:
            i = int(addr, 16)
        except:
            return False
        return True
                                
    def __route_msgs__(self, sock):
        try:
            raw_msg = sock.recv(16384)
        except: 
            print "*** Simulator Error - A replica quit unexpectedly"
            self.__close_replica__(sock)
            return

        # is this sock shutting down?
        if len(raw_msg) == 0:
            print "*** Simulator Error - Replica shut down a socket unexpectedly"
            self.__close_replica__(sock)
            return
                             
        # decode and validate the message
        try:
            msg = json.loads(raw_msg)
        except:
            print "*** Simulator Error - Unable to decode JSON message: %s" % (raw_msg)
            self.stats.incorrect += 1
            return
            
        if type(msg) is not dict:
            print "*** Simulator Error - Message is not a dictionary: %s" % (raw_msg)
            self.stats.incorrect += 1
            return
        if 'src' not in msg or 'dst' not in msg or 'leader' not in msg or 'type' not in msg:
            print "*** Simulator Error - Message is missing a required field: %s" % (raw_msg)
            self.stats.incorrect += 1
            return
        if not self.__validate_addr__(msg['leader']):
            print "*** Simulator Error - Incorrect leader format: %s" % (raw_msg)
            self.stats.incorrect += 1
            return
        if not self.__validate_addr__(msg['dst']):
            print "*** Simulator Error - Incorrect destination format: %s" % (raw_msg)
            self.stats.incorrect += 1
            return
        if not self.__validate_addr__(msg['src']):
            print "*** Simulator Error - Incorrect source format: %s" % (raw_msg)
            self.stats.incorrect += 1
            return
                        
        # record the id of the current leader
        if not self.partition or msg['src'] in self.partition:
            self.stats.add_leader(msg['leader'])
            self.leader = msg['leader']

        # is this message to a replica?
        if msg['dst'] in self.replicas:
            self.stats.total_msgs += 1
            if self.__check_partition__(msg['src'], msg['dst']) and random.random() >= self.conf.drops:
                self.__replica_deliver__(self.replicas[msg['dst']], raw_msg)
            else: self.stats.total_drops += 1
    
        # is this message a broadcast?
        elif msg['dst'] == 'FFFF':
            self.stats.total_msgs += len(self.replicas) - 1
            for rid, r in self.replicas.iteritems():
                if rid != msg['src']:
                    if self.__check_partition__(msg['src'], rid) and random.random() >= self.conf.drops:
                        self.__replica_deliver__(r, raw_msg)
                    else: self.stats.total_drops += 1

        # is this message to a client?
        elif msg['dst'] in self.clients:
            response = self.clients[msg['dst']].deliver(raw_msg, msg)
            if response:
                self.__replica_deliver__(self.replicas[response['dst']], json.dumps(response))
                
        # we have no idea who the destination is
        else:
            print "*** Simulator Error - Unknown destination: %s" % (raw_msg)
            self.stats.incorrect += 1
            
    def __accept__(self, sock):
        client = sock.accept()[0]
        for r in self.replicas.itervalues():
            if r.listen_sock == sock:
                r.client_sock = client
                break
    
    def __close_replica__(self, sock):
        for r in self.replicas.itervalues():
            if r.client_sock == sock:
                if r.rid in self.living_rids:
                    self.living_rids.remove(r.rid)
                    r.shutdown()
                break

#######################################################################################################

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print 'Usage: $ %s <config file>' % (sys.argv[0])
        sys.exit()

    sim = Simulation(sys.argv[1])

    def kill_processes():
        try: sim.shutdown()
        except: pass

    # Attempt to kill child processes regardless of how Python shuts down (e.g. via an exception or ctrl-C)
    atexit.register(kill_processes)
        
    sim.run()
    sim.stats.dump()
