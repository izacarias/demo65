#!/usr/bin/python

import json
import logging
import requests
from configparser import ConfigParser
from requests.auth import HTTPBasicAuth

# Reading external configuration
config = ConfigParser()
config.read("config.ini")
# ONOS Configurations
ONOS_URL = str(config.get("onos", "url"))
ONOS_USER = str(config.get("onos", "user"))
ONOS_PASS = str(config.get("onos", "password"))
ONOS_FLOWS_URL = f"{ONOS_URL}/onos/v1/intents"

def remove_rules_from_file(filename):
    logging.info( '*** Remove flow rules for monitoring hosts' )
    credentials = HTTPBasicAuth(ONOS_USER, ONOS_PASS)
    headers = {"Accept": "application/json"}
    # Load rules from monflows.json
    rules = []
    with open(filename, 'r') as openfile:
        rules = json.load(openfile)
    for rule in rules:
        url = ONOS_FLOWS_URL + "/" + rule["appId"] + "/" + rule["key"]
        response = requests.delete(url, headers=headers, auth=credentials)
        if response.status_code == 204:
            logging.info( "*** Flow rule removed. key=" + rule["key"] + "\n")
        else:
            logging.error( "*** Failed to remove flow rule key=" + rule["key"] + "\n")

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    remove_rules_from_file("monflows.json")