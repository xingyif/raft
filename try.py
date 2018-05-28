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
import random
import threading, time


a = [0, 1, 2]

def send_regular_heartbeat(a):
    print("started sending again, a %s" % str(a))

    a1 = a
    t = threading.Timer(0.15, send_regular_heartbeat, [a1])
    if len(a1) == 0:
        t.cancel()
        print("should cancel thread")
    else:
        for i in a:
            print("cur_time %s" % time.time())
            print(time.ctime())
            d = random.randint(1, 10)
            if (d == 2):
                a1.pop()
                print(len(a1))
                print("popped something, d %d" % d)
    t.start()



send_regular_heartbeat(a)
print("didn't wait for this to finish")

