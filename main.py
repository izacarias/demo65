import requests
import logging
import time
from time import sleep
from requests.auth import HTTPBasicAuth
from onos import Link

from rdflib import Namespace, XSD, Graph, Literal
from rdflib.namespace import RDF
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID as default

## Configuration
ONOS_URL = "http://localhost:8181"
ONOS_USER = "onos"
ONOS_PASS = "rocks"
ONOS_LINK_URL = f"{ONOS_URL}/onos/v1/links"
ONOS_STAT_URL = f"{ONOS_URL}/onos/v1/statistics/flows/link"
ONOS_PORT_STAT_URL = f"{ONOS_URL}/onos/v1/statistics/ports"
READ_INTERVAL = 5
FUSEKI_URL = "http://localhost:3030"
FUSEKI_DATASET = "ONOS"
FUSEKI_UPDATE_URL = f"{FUSEKI_URL}/{FUSEKI_DATASET}/update"
FUSEKI_QUERY_URL = f"{FUSEKI_URL}/{FUSEKI_DATASET}/query"


def is_duplicated(list, new_link:Link) -> bool:
    """
    This function checks for duplicated links or
    when the same link is reported in the opposite
    direction by ONOS REST API.
    """
    for link in list:
        if (link.src_port == new_link.src_port and 
            link.src_device == new_link.src_device and
            link.dst_port == new_link.dst_port and
            link.dst_device == new_link.dst_device
            ) or ( link.src_port == new_link.dst_port and 
            link.src_device == new_link.dst_device and
            link.dst_port == new_link.src_port and
            link.dst_device == new_link.src_device ):
            return True
    return False


def get_links():
    """
    Get all links from ONOS REST API
    """
    return_value = []
    response = requests.get(ONOS_LINK_URL, auth=HTTPBasicAuth(ONOS_USER, ONOS_PASS))
    if response.status_code == 200:
        id = 1;
        for l in response.json()['links']:
            new_link = Link(id, l['src']['port'], l['src']['device'], l['dst']['port'], l['dst']['device'])
            if not is_duplicated(return_value, new_link):
                return_value.append(new_link)
                id  = id + 1
    else:
        logging.error("Error getting list of links: %s", response.text)
    logging.debug("Collected %s links from the topology", len(return_value))
    return return_value


def get_link_stats(l: Link) -> int:
    """ 
    This function gets the delta of bytesSent and bytesReceived as well as 
    the time passed since last readings. Based in that we can calculate
    the link rate in that moment.
    """

    url = f"{ONOS_PORT_STAT_URL}/{l.src_device}/{l.src_port}"
    response = requests.get(url, auth=HTTPBasicAuth(ONOS_USER, ONOS_PASS))
    if response.status_code == 200:
        bytesSent = int(response.json()['statistics'][0]['ports'][0]['bytesSent'])
        bytesReceived = int(response.json()['statistics'][0]['ports'][0]['bytesReceived'])
        duration = int(response.json()['statistics'][0]['ports'][0]['durationSec'])
        l.set_data_rate(bytesSent, bytesReceived, duration)
        logging.debug("Link (%s, %s): Bytes sent %s, Bytes received: %s, Duration: %s, Datarate: %s", l.src_device, l.dst_device, bytesSent, bytesReceived, duration, l.rate)
    else:
        logging.error("Error getting link statistics: %s", response.text)


def publish_rdf(timeStamp: int, link: Link, graph: Graph):
    """
    Publishes the link statistics (data rate) to Apache Jena/Fuseki
    SPARQL database.
    """

    logging.debug("Sending information to SPARQL: Link (%s, %s): %s bps", link.src_device, link.dst_device, link.get_data_rate())
    ex = Namespace("http://6g-ric.de#")
    # Link
    graph.add((ex.a, RDF.type, ex.Link))
    graph.add((ex.a, ex.hasOrigin, Literal(link.src_device)))
    graph.add((ex.a, ex.hasDestination, Literal(link.dst_device)))
    graph.add((ex.a, ex.hasDataRate, Literal(link.get_data_rate(), datatype=XSD.integer)))
    # Timestamp
    graph.add((ex.t, RDF.type, ex.Timestamp))
    graph.add((ex.t, ex.hasTime, Literal(timeStamp, datatype=XSD.integer)))
    # Measurement
    graph.add((ex.measurement, RDF.type, ex.Measurement))
    graph.add((ex.measurement, ex.MeasuresLink, ex.a))
    graph.add((ex.measurement, ex.hasTimeStamp, ex.t))
    logging.info("Graph sent to SPARQL server with lenght %s", len(graph))


def main():
    """
    Main program function. It loops every READ_INTERVAL seconds
    getting statistics about links and send them to the SPARQL
    database.
    """
    try:
        links = []
        while not len(links) > 0:
            links = get_links()
            sleep(READ_INTERVAL)
        logging.debug("Detected %s links in the topology. Starting polling link stats.", len(links))
        store = SPARQLUpdateStore()
        store.open((FUSEKI_QUERY_URL, FUSEKI_UPDATE_URL))
        graph = Graph(store, identifier=default)
        while True:
            currentTime =  round(time.time())
            for l in links:
                # get stats 
                get_link_stats(l)
                publish_rdf(currentTime, l, graph)
            sleep(READ_INTERVAL)
    except KeyboardInterrupt:
        graph.close()
        print("Script finished by CTRL+C command")

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    main()