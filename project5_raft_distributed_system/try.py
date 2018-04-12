
unacked_msg_for_server = set()
unacked_msg_for_server.add('1')
unacked_msg_for_server.add('2')
unacked_msg_for_server.add('3')
unacked_msg_for_server.add('4')

print(unacked_msg_for_server)
for m in list(unacked_msg_for_server):
    if m == '2' or m == '3':
        unacked_msg_for_server.remove(m)
print(unacked_msg_for_server)
