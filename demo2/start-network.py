#!/usr/bin/env python3

import os
import math
import subprocess
import requests
import json
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.node import Host
from mininet.node import OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info, error
from mininet.link import TCLink, Intf
from subprocess import call
from requests.auth import HTTPBasicAuth
from time import sleep
from configparser import ConfigParser


# Reading external configuration
config = ConfigParser()
config.read("config.ini")
# ONOS Configurations
ONOS_URL = str(config.get("onos", "url"))
ONOS_USER = str(config.get("onos", "user"))
ONOS_PASS = str(config.get("onos", "password"))
ONOS_FLOWS_URL = f"{ONOS_URL}/onos/v1/intents"

# # Traffic generator configurations
# data_rate_max = config.getint("trafficgen", "data_rate_max")
# data_rate_steps = config.getint("trafficgen", "data_rate_steps")
# data_rate_interval = config.getint("trafficgen", "data_rate_interval")
# frequency = config.getfloat("trafficgen", "frequency")
# test_duration = config.getint("trafficgen", "test_duration")

# def calculate_bandwidth(time, max_bandwidth, frequency, amplitude):
#     radians_per_second = 2 * math.pi * frequency
#     sin_value = math.sin(radians_per_second * time)
#     bandwidth = max_bandwidth * (1 + amplitude * sin_value)
#     return 1 if bandwidth == 0 else bandwidth

def install_rules_from_file(filename):
    info( '*** Install flow rules for monitoring hosts' )
    credentials = HTTPBasicAuth(ONOS_USER, ONOS_PASS)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    # Load rules from monflows.json
    rules = []
    with open(filename, 'r') as openfile:
        rules = json.load(openfile)
    for rule in rules:
        response = requests.post(ONOS_FLOWS_URL, data=json.dumps(rule), headers=headers, auth=credentials)
        if response.status_code == 201:
            info( "*** Flow rule installed. key=" + rule["key"] + "\n")
        else:
            error( "*** Got wrong answer from ONOS. Flow rule not installed. key=" + rule["key"] + "\n")

def deleteVeths():
    os.system( 'ip link delete root-m1' )
    os.system( 'ip link delete root-m2' )
    os.system( 'ip link delete root-m3' )
    os.system( 'ip link delete root-m4' )

def createVeths():
    # m1
    os.system( 'ip link add root-m1 type veth peer name m1-root' )
    os.system( 'ip link set root-m1 up' )
    os.system( 'ip addr add 192.168.0.2/24 dev root-m1')
    os.system( 'ip route add 192.168.0.101/32 dev root-m1' )
    # m2
    os.system( 'ip link add root-m2 type veth peer name m2-root' )
    os.system( 'ip link set root-m2 up' )
    os.system( 'ip addr add 192.168.0.2/24 dev root-m2')
    os.system( 'ip route add 192.168.0.102/32 dev root-m2' )
    # m3
    os.system( 'ip link add root-m3 type veth peer name m3-root' )
    os.system( 'ip link set root-m3 up' )
    os.system( 'ip addr add 192.168.0.2/24 dev root-m3')
    os.system( 'ip route add 192.168.0.103/32 dev root-m3' )
    # m4
    os.system( 'ip link add root-m4 type veth peer name m4-root' )
    os.system( 'ip link set root-m4 up' )
    os.system( 'ip addr add 192.168.0.2/24 dev root-m4')
    os.system( 'ip route add 192.168.0.104/32 dev root-m4' )


def myNetwork():

    info( '*** Creating the virtual ethernet pairs\n' )
    deleteVeths()
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
    net.addLink(h1, s1, bw=1000)
    net.addLink(h2, s2, bw=1000)

    info( '*** Add monitoring hosts\n')
    m1 = net.addHost('m1', cls=Host, ip='10.0.0.101', defaultRoute=None)
    m2 = net.addHost('m2', cls=Host, ip='10.0.0.102', defaultRoute=None)
    m3 = net.addHost('m3', cls=Host, ip='10.0.0.103', defaultRoute=None)
    m4 = net.addHost('m4', cls=Host, ip='10.0.0.104', defaultRoute=None)
    m5 = net.addHost('m5', cls=Host, ip='10.0.0.105', defaultRoute=None)
    m6 = net.addHost('m6', cls=Host, ip='10.0.0.106', defaultRoute=None)
    m7 = net.addHost('m7', cls=Host, ip='10.0.0.107', defaultRoute=None)
    m8 = net.addHost('m8', cls=Host, ip='10.0.0.108', defaultRoute=None)

    info( '*** Add links for monitoring hosts\n')
    net.addLink(m1, s1, bw=1000)
    net.addLink(m2, s1, bw=1000)
    net.addLink(m3, s1, bw=1000)
    net.addLink(m4, s1, bw=1000)
    net.addLink(m5, s2, bw=1000)
    net.addLink(m6, s2, bw=1000)
    net.addLink(m7, s2, bw=1000)
    net.addLink(m8, s2, bw=1000)

    info( '*** Add transport links\n')
    net.addLink( s1, s2, bw=25, delay='7ms',   loss=1, jitter='1ms' )   # Fiber
    net.addLink( s1, s2, bw=5,  delay='17ms',  loss=2, jitter='2ms' )   # Mobile 5G
    net.addLink( s1, s2, bw=3,  delay='290ms', loss=5, jitter='10ms' )  # Stellite
    net.addLink( s1, s2, bw=25, delay='120ms', loss=1, jitter='20ms' )  # Stellite

    info( '*** Adding interface to root namespace\n')
    _intf_m1 = Intf( 'm1-root', m1)
    _intf_m2 = Intf( 'm2-root', m2)
    _intf_m3 = Intf( 'm3-root', m3)
    _intf_m4 = Intf( 'm4-root', m4)
    
    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s1').start([c0])
    net.get('s2').start([c0])

    info( '*** Adding IP address to root-namespace interfaces\n' )
    # m1
    m1.cmd( ' ip addr add 192.168.0.101/24 dev m1-root' )
    m1.cmd( ' ip route add 192.168.124.0/24 dev m1-root ' )
    # m2
    m2.cmd( ' ip addr add 192.168.0.102/24 dev m2-root' )
    m2.cmd( ' ip route add 192.168.124.0/24 dev m2-root ' )
    # m3
    m3.cmd( ' ip addr add 192.168.0.103/24 dev m3-root' )
    m3.cmd( ' ip route add 192.168.124.0/24 dev m3-root ' )
    # m4
    m4.cmd( ' ip addr add 192.168.0.104/24 dev m4-root' )
    m4.cmd( ' ip route add 192.168.124.0/24 dev m4-root ' )

    info( '*** Starting iperf server on h2\n')
    h2.cmd( 'iperf3 -s &' )


    info( '*** Waiting 2 seconds to update topology in ONOS\n')
    sleep(2)
    info( '*** Installing monitoring flow rules from monflows.json\n')
    install_rules_from_file("monflows.json")
    info( '*** Selecting Link 1 (bw=25Mbps, latency=7ms, loss=1%, jitter=1ms)\n')
    install_rules_from_file("select-l1.json")
    info( '*** Running iperf3 servers on hosts m5 .. m8\n')
    m5.cmd( 'iperf3 -s -D' )
    m6.cmd( 'iperf3 -s -D' )
    m7.cmd( 'iperf3 -s -D' )
    m8.cmd( 'iperf3 -s -D' )
    
    info( '*** Waiting for Iperf Server processes to start\n')
    sleep(2)

    info ( '*** Starting monitoring agents in hosts h1 .. h4\n' )
    m1.cmd( './monitoring.py 10.0.0.105 MyFiberLink 25 > MyFiberLink.log 2>&1 &' )
    m2.cmd( './monitoring.py 10.0.0.106 MyWirelessLink 5 > MyWirelessLink.log  2>&1 &' )
    m3.cmd( './monitoring.py 10.0.0.107 MyNTNLink1 3 > MyNTNLink1.log  2>&1 &')
    m4.cmd( './monitoring.py 10.0.0.108 MyNTNLink2 25 > MyNTNLink2.log  2>&1 &')

    CLI(net)
    # info( '*** Starting iperf client on h1\n')
    # current_t = 0
    # while current_t < test_duration:
    #     bandwidth = calculate_bandwidth(current_t, data_rate_max, frequency, 1.0)
    #     iperf_cmd = ["iperf3", "-u", "-c", "10.0.0.2", "-t", str(data_rate_interval), "-b", f"%dm" % bandwidth]
    #     info( '*** Running iperf test with bandwidht of ' + str(bandwidth) + '\n')
    #     info( '*** Command: ' + ' '.join(iperf_cmd))
    #     subprocess.run(iperf_cmd)

    #     sleep(data_rate_interval)
    #     current_t = current_t + 1 

    # Disabling Mininet client shell for experiments

    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()
