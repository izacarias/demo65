#!/usr/bin/python

class Link:
    
    def __init__(self, id, src_device, src_port, dst_device, dst_port, max_capacity):
        self.id = id
        self.src_port = src_port
        self.src_device = src_device
        self.dst_port = dst_port
        self.dst_device = dst_device
        self.max_capacity = max_capacity
        self.rate = 0
        self.lastBytesSent = 0
        self.lastBytesReceived = 0
        self.lastDuration = 0


    def set_data_rate(self, bytesSent, bytesReceived, duration):
        if bytesSent >= bytesReceived:
            try:
                self.rate = round((bytesSent - self.lastBytesSent) / (duration - self.lastDuration) * 8)
            except ZeroDivisionError:
                self.rate = 0
        else:
            self.rate = round((bytesReceived - self.lastBytesReceived) / (duration - self.lastDuration) * 8)
        self.lastBytesSent = bytesSent
        self.lastBytesReceived = bytesReceived
        self.lastDuration = duration

    def get_link_usage(self):
        return self.rate / self.max_capacity

    def get_data_rate(self) -> int:
        return self.rate

