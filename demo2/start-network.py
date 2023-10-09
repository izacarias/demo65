#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.node import Host
from mininet.node import OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call
from time import sleep
import os
import math
import subprocess

# Configuration
data_rate_max = 50
data_rate_steps = 10
data_rate_interval = 1
data_rate = []
frequency = 0.05
amplitude = []
test_duration = 60

def calculate_bandwidth(time, max_bandwidth, frequency, amplitude):
    radians_per_second = 2 * math.pi * frequency
    sin_value = math.sin(radians_per_second * time)
    bandwidth = max_bandwidth * (1 + amplitude * sin_value)
    return 1 if bandwidth == 0 else bandwidth

def createVeths():
    os.system( 'ip link add root-eth type veth peer name h1-root' )
    os.system( 'ip link set root-eth up' )
    os.system( 'ip addr add 192.168.0.2/24 dev root-eth')

def myNetwork():

    info( '*** Creating the virtual ethernet pairs\n' )
    createVeths()

    net = Mininet( topo=None, build=False, ipBase='10.0.0.0/8', link=TCLink)

    info( '*** Adding controller\n' )
    c0=net.addController(name='c0', controller=RemoteController, 
                         ip='localhost',
                         protocol='tcp',
                         port=6653)

    info( '*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch, protocols="OpenFlow13")
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch, protocols="OpenFlow13")

    info( '*** Add hosts\n')
    h1 = net.addHost('h1', cls=Host, ip='10.0.0.1', defaultRoute=None)
    h2 = net.addHost('h2', cls=Host, ip='10.0.0.2', defaultRoute=None)
    
    info( '*** Add links\n')
    net.addLink(h1, s1)
    net.addLink(h2, s2)

    net.addLink( s1, s2, bw=50, delay='5ms', loss=0, jitter='0ms' )
    net.addLink( s1, s2, bw=100, delay='5ms', loss=0, jitter='0ms' )

    info( '*** Adding host interface\n')
    _intf_h1 = Intf( 'h1-root', h1)
    
    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s1').start([c0])
    net.get('s2').start([c0])

    h1.cmd( ' ip addr add 192.168.0.1/24 dev h1-root' )
    h1.cmd( ' ip route add 192.168.124.0/24 dev h1-root ' )

    info( '*** Starting iperf server on h2\n')
    h2.cmd( 'iperf -s -u &' )

    info( '*** Starting iperf client on h1\n')
    current_t = 0
    while current_t < test_duration:
        bandwidth = calculate_bandwidth(current_t, data_rate_max, frequency, 1.0)
        iperf_cmd = ["iperf", "-u", "-c", "10.0.0.2", "-t", str(data_rate_interval), "-b", f"%dm" % bandwidth]
        info( '*** Running iperf test with bandwidht of ' + bandwidth + '\n')
        subprocess.run(iperf_cmd)

        sleep(data_rate_interval)
        current_t = current_t + 1 

    # Disabling Mininet client for experiments
    # CLI(net)

    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()