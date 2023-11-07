#!/usr/bin/python3

import sys
import re
import logging
import subprocess
import time
from configparser import ConfigParser
from urllib.error import URLError
from rdflib import Namespace, Graph, URIRef
from rdflib.namespace import RDF, RDFS, OWL
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID as default
import influxdb_client, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


# Reading configurations
config = ConfigParser()
config.read("config.ini")
# Monitoring configurations
STATS_PING_COUNT = config.getint("agent", "ping_count")
STATS_IPERF_TIME = config.getint("agent", "iperf_time")
# Fuseki configurations
FUSEKI_URL = str(config.get("fuseki", "url"))
FUSEKI_DATASET = str(config.get("fuseki", "database"))
FUSEKI_UPDATE_URL = f"{FUSEKI_URL}/{FUSEKI_DATASET}/update"
FUSEKI_QUERY_URL = f"{FUSEKI_URL}/{FUSEKI_DATASET}/query"
# Influx configurations
INFLUX_TOKEN = str(config.get("influxdb", "token"))
INFLUX_ORG = str(config.get("influxdb", "organization"))
INFLUX_URL = str(config.get("influxdb", "url"))
INFLUX_BUCKET = str(config.get("influxdb", "bucket"))
# KB Namespace
KB_NS_URL = "http://purl.org/toco/"

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
    # jitter = 0.0
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
                    avg_bw = float(stats_match.group(1))
                    # jitter = float(stats_match.group(2))
                    packet_loss = float(stats_match.group(3))
        return avg_bw, packet_loss
    except subprocess.CalledProcessError:
        logging.error("Iperf test failed. Make sure the iperf server is running and reachable.")

def update_sparqldb(link_name, latency, jitter, datarate, loss, graph: Graph):
    """
    Publishes the link statistics (data rate) to Apache Jena/Fuseki
    SPARQL database.
    """
    # Subject
    myLink = URIRef(KB_NS_URL + link_name)
    # Predicates
    hasRoundTripTime = URIRef(KB_NS_URL + "hasRoundTripTime")
    hasJitter = URIRef(KB_NS_URL + "hasJitter")
    hasDatarate = URIRef(KB_NS_URL + "hasDatarate")
    hasPacketLoss = URIRef(KB_NS_URL + "hasPacketLoss")
    # Object (Values)
    oRoundTripTime = URIRef(KB_NS_URL + "Delay_" + str(int(latency)) + "_ms")
    oJitter = URIRef(KB_NS_URL + "Jitter_" + str(int(jitter)) + "_ms")
    oDatarate = URIRef(KB_NS_URL + "Datarate_" + str(int(datarate)) + "_Mbps")
    oPacketLoss = URIRef(KB_NS_URL + "Packetloss_" + str(int(loss)) + "_percent")

    try:
        # Remove old values
        graph.remove((myLink, hasRoundTripTime, None))
        graph.remove((myLink, hasJitter, None))
        graph.remove((myLink, hasDatarate, None))
        graph.remove((myLink, hasPacketLoss, None))
        # Add new values
        graph.add((myLink, hasRoundTripTime, oRoundTripTime))
        graph.add((myLink, hasJitter, oJitter))
        graph.add((myLink, hasDatarate, oDatarate))
        graph.add((myLink, hasPacketLoss, oPacketLoss))
        logging.debug(f"Link {link_name} updated in SPARQL. Latency={latency}, Jitter={jitter}, Datarate={datarate}, Packetloss={loss}")
    except URLError:
        logging.error("Connection to SPARQL Server refused. Is SPARQL running?")


def update_influx(link_name, latency, jitter, datarate, loss, write_api):
    point = (
        Point("linkstat")
        .tag("linkName", link_name)
        .field("latency", float(latency))
        .field("jitter", float(jitter))
        .field("bandwidth", float(datarate))
        .field("loss", float(loss))
    )
    logging.debug("New InfluxDB record: Link=%s, latency=%s, jitter=%s, datarate=%s, loss=%s", 
                 str(link_name), str(latency), str(jitter), str(datarate), str(loss))
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

if __name__ == "__main__":
    # set the log level
    logging.basicConfig(level=logging.DEBUG)
    # Open InfluxDB connection
    influx_write_client = influxdb_client.InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    influx_write_api = influx_write_client.write_api(write_options=SYNCHRONOUS)
    # get dstination IP from command line, or assume 10.0.0.2
    if len( sys.argv ) > 3:
        dst_ip = sys.argv[ 1 ]
        link_name = sys.argv [ 2 ]
        link_datarate = sys.argv [ 3 ]
        # Prepare the ontology in SPARQL
        store = SPARQLUpdateStore()
        store.open((FUSEKI_QUERY_URL, FUSEKI_UPDATE_URL))
        graph = Graph(store, identifier=default)
        while True:
            try:
                latency, jitter = test_latency_jitter(dst_ip)
                datarate, loss = test_bandwidth(dst_ip, link_datarate)
                update_sparqldb(link_name, latency, jitter, datarate, loss, graph)
                update_influx(link_name, latency, jitter, datarate, loss, write_api = influx_write_api)
            except:
                logging.error("Problem reading measurements. Skipping this iteration.")
            time.sleep(1)
    else:
        logging.error("Incorrect use of script. Please provide destination IP address, link name and link data rate.")


