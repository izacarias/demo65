#!/usr/bin/python3

import sys
import re
import logging
import subprocess
import time
from urllib.error import URLError
from rdflib import Namespace, XSD, Graph, Literal
from rdflib.namespace import RDF, RDFS, OWL
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID as default

STATS_PING_COUNT = 5
STATS_IPERF_TIME = 5
FUSEKI_URL = "http://localhost:3030"
FUSEKI_DATASET = "ONOS"
FUSEKI_UPDATE_URL = f"{FUSEKI_URL}/{FUSEKI_DATASET}/update"
FUSEKI_QUERY_URL = f"{FUSEKI_URL}/{FUSEKI_DATASET}/query"


def test_latency_jitter(target_ip):
    try:
        # Run ping command to measure latency and jitter
        ping_output = subprocess.check_output(["ping", "-c", str(STATS_PING_COUNT), target_ip])

        # Parse ping output to extract relevant statistics
        ping_lines = ping_output.decode().split('\n')
        ping_lines = list(filter(None, ping_lines[1:-4]))
        if len(ping_lines) > 2:
            latency_values = [float(line.split()[-2].split('=')[-1]) for line in ping_lines[1:-1]]
            avg_latency = sum(latency_values) / len(latency_values)
            jitter = max(latency_values) - min(latency_values)
            logging.debug(f"Average Latency: {avg_latency} ms")
            logging.debug(f"Jitter: {jitter} ms")
            return avg_latency, jitter
        else:
            logging.error("Not enough data for latency and jitter measurements.")
    except subprocess.CalledProcessError:
        logging.error("Ping failed. Check the target IP or hostname.")

def test_bandwidth(iperf_server_ip, link_data_rate):
    avg_bw = 0.0
    packet_loss = 0.0
    jitter = 0.0
    packet_loss = 0
    line_regexp = r"^\[.*\].*receiver$"
    stats_regexp = r"^\[\s*\d+\].*\s+([\d.]+)\sMbits/sec\s*([\d.]+).+\(([\d.]+)%\)\s*receiver"
    try:
        # Run iperf command to measure bandwidth
        iperf_output = subprocess.check_output(["iperf3", "-u", "-c", iperf_server_ip, "-t", str(STATS_IPERF_TIME), "-f", "m", "-b", link_data_rate + "m"])
        iperf_lines = list(filter(None, iperf_output.decode().split('\n')))
        for line in iperf_lines:
            if re.match(line_regexp, line):
                stats_match = re.match(stats_regexp, line)
                if (stats_match):
                    print("Weee2")
                    avg_bw = stats_match.group(1)
                    jitter = stats_match.group(2)
                    packet_loss = stats_match.group(3)
        return avg_bw, packet_loss
    except subprocess.CalledProcessError:
        logging.error("iperf test failed. Make sure the iperf server is running and reachable.")

def update_sparqldb(link_name, latency, jitter, datarate, loss, graph: Graph, ns: Namespace):
    """
    Publishes the link statistics (data rate) to Apache Jena/Fuseki
    SPARQL database.
    """
    # Do some cool checking here
    try:
        # # remove old values
        # graph.remove((link_to_update, ns.hasBWMeasurement, None))
        # graph.remove((link_to_update, RDF.type, ns.BWMeasurement))
        # # add new values 
        # graph.add((link_to_update, RDF.type, ns.BWMeasurement))
        # graph.add((link_to_update, ns.hasBWMeasurement, usageObject))
        logging.info(f"Link {link_name} updated in SPARQL. Latency={latency}, Jitter={jitter}, Datarate={datarate}, Packetloss={loss}")
    except URLError:
        logging.error("Connection to SPARQL Server refused. Is SPARQL running?")

if __name__ == "__main__":
    # set the log level
    logging.basicConfig(level=logging.DEBUG)
    # get dstination IP from command line, or assume 10.0.0.2
    if len( sys.argv ) > 3:
        dst_ip = sys.argv[ 1 ]
        link_name = sys.argv [ 2 ]
        link_datarate = sys.argv [ 3 ]
        # Prepare the ontology in SPARQL
        store = SPARQLUpdateStore()
        store.open((FUSEKI_QUERY_URL, FUSEKI_UPDATE_URL))
        ns = Namespace("http://6g-ric.de#")
        graph = Graph(store, identifier=default)
        while True:    
            logging.info(f"Testing network link to {dst_ip}...")
            latency, jitter = test_latency_jitter(dst_ip)
            logging.info(f"Testing bandwidth to {dst_ip}")
            datarate, loss = test_bandwidth(dst_ip, link_datarate)
            update_sparqldb(link_name, latency, jitter, datarate, loss, graph, ns)
            time.sleep(1)
    else:
        logging.error("Incorrect use of script. Please provide destination IP address, link name and link data rate.")


