#!/usr/bin/python3

from rdflib import Graph
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID as default
from configparser import ConfigParser
import os

# Reading configurations
config = ConfigParser()
config.read("config.ini")
# Fuseki configurations
FUSEKI_URL = "http://192.168.124.179:3030"
FUSEKI_DATASET = "ONOS"
FUSEKI_UPDATE_URL = f"{FUSEKI_URL}/{FUSEKI_DATASET}/update"
FUSEKI_QUERY_URL = f"{FUSEKI_URL}/{FUSEKI_DATASET}/query"

if __name__ == "__main__":
    store = SPARQLUpdateStore()
    store.open((FUSEKI_QUERY_URL, FUSEKI_UPDATE_URL))
    graph = Graph(store, identifier=default)
    rawdata = graph.serialize(format="n3")
    # Save to file
    file = open("fuseki-bkp.txt", "w")
    file.write(rawdata)
    file.close