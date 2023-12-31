import requests
import logging
import os
import time
import influxdb_client
from requests.auth import HTTPBasicAuth
from urllib.error import URLError
from onos import Link
from rdflib import Namespace, XSD, Graph, Literal
from rdflib.namespace import RDF, RDFS, OWL
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID as default
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

## Configuration
# General 
READ_INTERVAL = 5
# ONOS
ONOS_URL = "http://localhost:8181"
ONOS_USER = "onos"
ONOS_PASS = "rocks"
ONOS_LINK_URL = f"{ONOS_URL}/onos/v1/links"
ONOS_STAT_URL = f"{ONOS_URL}/onos/v1/statistics/flows/link"
ONOS_PORT_STAT_URL = f"{ONOS_URL}/onos/v1/statistics/ports"
# Apache Jena FUSEKI (SPARQL)
FUSEKI_URL = "http://localhost:3030"
FUSEKI_DATASET = "ONOS"
FUSEKI_UPDATE_URL = f"{FUSEKI_URL}/{FUSEKI_DATASET}/update"
FUSEKI_QUERY_URL = f"{FUSEKI_URL}/{FUSEKI_DATASET}/query"
# InlfuxDB
INFLUX_TOKEN = "h5qh4-C5BJxsnRrvw3wcCERvcBgLekZC63kDPECeg-FiundQzMvpApBbbRd2-hzNslVhCiOixhKPWMaL7hZbdw=="
INFLUX_ORG = "influxdb"
INFLUX_URL = "http://localhost:8086"
INFLUX_BUCKET = "mininet"


LINKS_DICTIONARY = {
    'path1': 
        {
            'src_device': 'of:0000000000000001', 
            'src_port': '2', 
            'dst_device': 'of:0000000000000003', 
            'dst_port': '2', 
            'max_cap': 50000000
        },
    'path2': 
        {
            'src_device': 'of:0000000000000001', 
            'src_port': '3', 
            'dst_device': 
            'of:0000000000000002', 
            'dst_port': '1', 
            'max_cap': 100000000
        },
}

def update_influx(link:Link, wirte_api):
    point = (
        Point("linkstats")
        .tag(link.id, "linkusage")
        .field("traffic", link.get_data_rate())
    )
    logging.info("Sending data to InfluxDB for link: %s", link.id)
    wirte_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

def create_ontology(graph: Graph, ns: Namespace):
    """
    Creates the RDF Structure and send ontology in the SPARQL Server
    """
    try:
        graph.add((ns.LinkA, RDF.type, ns.Link))
        graph.add((ns.LinkB, RDF.type, ns.Link))
        graph.add((ns.DataRate, RDF.type, ns.Measurement))
        graph.add((ns.DataRateBWMeasurement, RDF.type, ns.BWMeasurement))
        graph.add((ns.hasBWMeasurement, RDF.type, OWL.ObjectProperty))
        graph.add((ns.hasBWMeasurement, RDFS.domain, ns.Measurement))
        graph.add((ns.hasBWMeasurement, RDFS.range, ns.BWMeasurement))
        graph.add((ns.Usage5Percent, RDF.type, ns.BWMeasurement))
        graph.add((ns.Usage10Percent, RDF.type, ns.BWMeasurement))
        graph.add((ns.Usage15Percent, RDF.type, ns.BWMeasurement))
        graph.add((ns.Usage20Percent, RDF.type, ns.BWMeasurement))
        graph.add((ns.Usage25Percent, RDF.type, ns.BWMeasurement))
        graph.add((ns.Usage30Percent, RDF.type, ns.BWMeasurement))
        graph.add((ns.Usage35Percent, RDF.type, ns.BWMeasurement))
        graph.add((ns.Usage40Percent, RDF.type, ns.BWMeasurement))
        graph.add((ns.Usage45Percent, RDF.type, ns.BWMeasurement))
        graph.add((ns.Usage50Percent, RDF.type, ns.BWMeasurement))
        graph.add((ns.Usage55Percent, RDF.type, ns.BWMeasurement))
        graph.add((ns.Usage60Percent, RDF.type, ns.BWMeasurement))
        graph.add((ns.Usage65Percent, RDF.type, ns.BWMeasurement))
        graph.add((ns.Usage70Percent, RDF.type, ns.BWMeasurement))
        graph.add((ns.Usage75Percent, RDF.type, ns.BWMeasurement))
        graph.add((ns.Usage80Percent, RDF.type, ns.BWMeasurement))
        graph.add((ns.Usage85Percent, RDF.type, ns.BWMeasurement))
        graph.add((ns.Usage90Percent, RDF.type, ns.BWMeasurement))
        graph.add((ns.Usage95Percent, RDF.type, ns.BWMeasurement))
        graph.add((ns.Usage100Percent, RDF.type, ns.BWMeasurement))
        logging.info("Ontology sent to SPARQL Server. Graph has a lenght of %s", len(graph))
    except URLError:
        logging.error("Connection to SPARQL Server refused. Is SPARQL running?")



def update_sparqldb(link: Link, graph: Graph, ns: Namespace):
    """
    Publishes the link statistics (data rate) to Apache Jena/Fuseki
    SPARQL database.
    """
    usage = link.get_link_usage()
    usageObject = None
    if usage <= 0.05:
        usageObject = ns.Usage5Percent
    elif usage <= 0.10:
        usageObject = ns.Usage10Percent
    elif usage <= 0.15:
        usageObject = ns.Usage15Percent
    elif usage <= 0.20:
        usageObject = ns.Usage20Percent
    elif usage <= 0.25:
        usageObject = ns.Usage25Percent
    elif usage <= 0.30:
        usageObject = ns.Usage30Percent
    elif usage <= 0.35:
        usageObject = ns.Usage35Percent
    elif usage <= 0.40:
        usageObject = ns.Usage40Percent
    elif usage <= 0.45:
        usageObject = ns.Usage45Percent
    elif usage <= 0.50:
        usageObject = ns.Usage50Percent
    elif usage <= 0.55:
        usageObject = ns.Usage55Percent
    elif usage <= 0.60:
        usageObject = ns.Usage60Percent
    elif usage <= 0.65:
        usageObject = ns.Usage65Percent
    elif usage <= 0.70:
        usageObject = ns.Usage70Percent
    elif usage <= 0.75:
        usageObject = ns.Usage75Percent
    elif usage <= 0.80:
        usageObject = ns.Usage80Percent
    elif usage <= 0.85:
        usageObject = ns.Usage85Percent
    elif usage <= 0.90:
        usageObject = ns.Usage90Percent
    elif usage <= 0.95:
        usageObject = ns.Usage95Percent
    elif usage > 0.95:
        usageObject = ns.Usage100Percent
    else:
        logging.error('Error creating the link usage object')
    # Link to update
    if link.id == "path1":
        link_to_update = ns.LinkA
    elif link.id == "path2":
        link_to_update = ns.LinkB

    try:
        # remove old values
        graph.remove((link_to_update, ns.hasBWMeasurement, None))
        graph.remove((link_to_update, RDF.type, ns.BWMeasurement))
        # add new values 
        graph.add((link_to_update, RDF.type, ns.BWMeasurement))
        graph.add((link_to_update, ns.hasBWMeasurement, usageObject))
        logging.info("Updating BWMeasurement for link %s", link.id)
    except URLError:
        logging.error("Connection to SPARQL Server refused. Is SPARQL running?")

def get_link_stats(link: Link) -> int:
    """ 
    This function gets the delta of bytesSent and bytesReceived as well as 
    the time passed since last readings. Based in that we can calculate
    the link rate in that moment.
    """
    url = f"{ONOS_PORT_STAT_URL}/{link.src_device}/{link.src_port}"
    response = requests.get(url, auth=HTTPBasicAuth(ONOS_USER, ONOS_PASS))
    if response.status_code == 200:
        bytesSent = int(response.json()['statistics'][0]['ports'][0]['bytesSent'])
        bytesReceived = int(response.json()['statistics'][0]['ports'][0]['bytesReceived'])
        duration = int(response.json()['statistics'][0]['ports'][0]['durationSec'])
        link.set_data_rate(bytesSent, bytesReceived, duration)
        logging.debug("Link (%s, %s): Bytes sent %s, Bytes received: %s, Duration: %s, Datarate: %s, Usage: %.2f", 
                      link.src_device, link.dst_device, bytesSent, bytesReceived, duration, link.rate, link.get_link_usage() * 100)
    else:
        logging.error("Error getting link statistics: %s", response.text)

def main():
    """
    Main program function. It loops every READ_INTERVAL seconds
    getting statistics about links and send them to the SPARQL
    database.
    """
    # Prepare the ontology in SPARQL
    store = SPARQLUpdateStore()
    store.open((FUSEKI_QUERY_URL, FUSEKI_UPDATE_URL))
    ns = Namespace("http://6g-ric.de#")
    graph = Graph(store, identifier=default)
    create_ontology(graph, ns)
    # Create Influx wirte client
    influx_write_client = influxdb_client.InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    influx_write_api = influx_write_client.write_api(write_options=SYNCHRONOUS)

    # Collect all linkst to monitor (static configuration)
    links = []
    for p in LINKS_DICTIONARY:
        links.append(Link(
            p,
            LINKS_DICTIONARY[p]["src_device"],
            LINKS_DICTIONARY[p]["src_port"],
            LINKS_DICTIONARY[p]["dst_device"],
            LINKS_DICTIONARY[p]["dst_port"],
            LINKS_DICTIONARY[p]["max_cap"]
        ))
    try:
        while True:
            # Get link stats
            for l in links:
                logging.debug("Getting link statistics for link %s", l.id)
                get_link_stats(l)
                logging.debug("Updating SPARQL database for link %s", l.id)
                update_sparqldb(link=l, graph=graph, ns=ns)
                logging.debug("Updating influxDB statistics for link %s", l.id)
                update_influx(link=l, wirte_api=influx_write_api)
            # Wait for the next iteration
            time.sleep(READ_INTERVAL)

    except KeyboardInterrupt:
        try:
            graph.close()
        except:
            logging.info("SPARQL graph was not open. Impossible to close the connection.")
        print("Script finished by CTRL+C command")

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    main()
