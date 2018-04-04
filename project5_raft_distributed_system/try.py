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
import threading, time


def send_regular_heartbeat():
    print("cur_time %s" % time.time())
    print(time.ctime())
    threading.Timer(0.15, send_regular_heartbeat).start()


send_regular_heartbeat()
