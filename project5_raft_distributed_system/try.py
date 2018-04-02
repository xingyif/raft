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

array = {1, 2, 3, 4, 5}
i = 1
while len(array) > 0:
    print(i)
    array.remove(i)
    print(len(array))
    i += 1
