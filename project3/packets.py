import json

class SendPacket:

    def __init__(self, seq_num, data, size, timeout, ack, eof):
        self.seq_num = seq_num #int
        self.data = data #str
        self.size = size #int
        self.timeout = timeout # time / long
        self.ack = ack #boolean
        self.eof = eof #boolean
    
    """
    converts this packet into a json format (presumably to be sent)
    @return String
    """
    def get_json(self):
        data_as_json = {'seq_num': self.seq_num, 'data': self.data, 'size': self.size, 'timeout_time': self.timeout, 'ack': self.ack, 'eof': self.eof}
        return json.dumps(data_as_json)
        
    """
    returns True if this packet is timed out
    @return boolean
    """
    def is_timed_out(self):
        return time.time() > self.timeout

    """
    getter for seq number
    @return Integer
    """ 
    def get_seq_num(self):
        return self.seq_num

    """
    returns True is the data has been acknowledged
    @return boolean
    """
    def is_acked(self):
    		return self.ack


class AckPacket:

    def __init__(self, ack_num):
        self.ack_num = ack_num
    
    """
    returns the ack number of this packet
    @return Integer
    """
    def get_ack_num(self):
        return self.ack_num
    
    
    def as_json(self):
        result = {'seq_num': self.ack_num, 'type': 'ack'}
        return result




