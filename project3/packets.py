import json

class SendPacket:

    def __init__(self, size, timeout, seq_num, data, eof):
        self.size = size # int
        self.timeout = timeout # time / long
        self.seq_num = seq_num #int
        self.data = data #str
        self.eof = eof #boolean
    
    """
    converts this packet into a json format (presumably to be sent)
    @return String
    """
    def get_json():
        data_as_json = {'eof': eof, 'data': self.data, 'seq': self.seq, 'size': self.size}
        return json.dumps(data_as_json)
        
    """
    returns True if this packet is timed out
    @return boolean
    """
    def is_timed_out():
        return time.time() > self.timeout

    """
    getter for seq number
    @return Integer
    """ 
    def get_seq_num():
        return self.seq_num



class AckPacket:

    def __init__(self, ack_num):
        self.ack_num = ack_num
    
    """
    returns the ack number of this packet
    @return Integer
    """
    def get_ack_num():
        return self.ack_num





