# from threading import Thread
# from time import sleep
#
# def threaded_function(arg):
#     for i in range(arg):
#         print "running"
#         sleep(1)
#
#
# if __name__ == "__main__":
#     thread = Thread(target = threaded_function, args = (10, ))
#     thread.start()
#     thread.join()
#     print "thread finished...exiting"
import json
import threading, time


def send_regular_heartbeat():
    print("cur_time %s" % time.time())
    print(time.ctime())
    threading.Timer(0.15, send_regular_heartbeat).start()
# send_regular_heartbeat()


queued_client_requests = [1, 2, 3, 4, 5, 6]

def send_queued_requests():
    for m in list(queued_client_requests):
        response_prev_requests_to_client = {'src': m, "dst": m, 'leader': 0,
                                            'type': 'redirect', 'MID': m}
        print(json.dumps(response_prev_requests_to_client))
        queued_client_requests.remove(m)
        print(len(queued_client_requests))
    print("final length %d" % len(queued_client_requests))
send_queued_requests()