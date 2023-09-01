#!/usr/bin/python

class Link:
    
    def __init__(self, id, src_port, src_device, dst_port, dst_device):
        self.id = id
        self.src_port = src_port
        self.src_device = src_device
        self.dst_port = dst_port
        self.dst_device = dst_device
        self.rate = 0

    def set_link_rate(self, rate: int):
        self.rate = rate * 15.5

    def get_link_rate(self) -> int:
        return self.rate

