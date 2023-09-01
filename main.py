import requests
import logging
from time import sleep
from requests.auth import HTTPBasicAuth
from onos import Link

from rdflib import Namespace, Graph, Literal
from rdflib.namespace import RDF, FOAF
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID as default

## Configuration
ONOS_URL = "http://localhost:8181"
ONOS_USER = "onos"
ONOS_PASS = "rocks"
ONOS_LINK_URL = f"{ONOS_URL}/onos/v1/links"
ONOS_STAT_URL = f"{ONOS_URL}/onos/v1/statistics/flows/link"
READ_INTERVAL = 5
FUSEKI_URL = "http://localhost:3030"
FUSEKI_DATASET = "ONOS"
FUSEKI_UPDATE_URL = f"{FUSEKI_URL}/{FUSEKI_DATASET}/update"
FUSEKI_QUERY_URL = f"{FUSEKI_URL}/{FUSEKI_DATASET}/query"

# def print_link_stats(link_id, throughput):
#     print(f"Link ID: {link_id}")
#     print(f"Link bandwidth: {throughput} bps")
#     print("-" * 40)

## Program logic
'''
    This function checks for duplicated links or
    when the same link is reported in the opposite
    direction by ONOS REST API.
'''
def is_duplicated(list, new_link:Link) -> bool:
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

'''
    Get all links from ONOS REST API
'''
def get_links():
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
    return return_value

'''
    This function gets the rate of each link
'''
def get_link_stats(l: Link) -> int:
    return_value = 0
    payload = {'device': l.src_device, 'port': l.src_port}
    response = requests.get(ONOS_STAT_URL, auth=HTTPBasicAuth(ONOS_USER, ONOS_PASS), params=payload)
    if response.status_code == 200:
        return response.json()['loads'][0]['rate']
    else:
        logging.error("Error getting link statistics: %s", response.text)
    pass

'''
    Publish data to SPARQL / FUSEKI
'''
def publish_rdf():
    store = SPARQLUpdateStore()
    update_endpoint = FUSEKI_UPDATE_URL
    store.open((FUSEKI_QUERY_URL, FUSEKI_UPDATE_URL))
    graph = Graph(store, identifier=default)
    ex = Namespace("http://example.org")
    node = (ex.measurement, RDF.type, ex.Measurement)
    node2 = (ex.a, RDF.type, ex.Link)
    node3 = (ex.a, ex.hasDataRate, Literal(5000000))
    graph.add(node)
    graph.add(node2)
    graph.add(node3)

'''
    Main program function
'''
def main():
    links = get_links()
    # while True:
    for l in links:
        # get stats 
        l.set_link_rate(get_link_stats(l))
        
    # publish to Apache Jena Fuseki
    publish_rdf()

        # sleep(READ_INTERVAL)

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    main()