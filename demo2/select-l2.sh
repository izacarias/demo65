#!/bin/bash
############################################################
#  INSTALL PATH1
############################################################

curl -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d '{ 
   "type": "PointToPointIntent", 
   "appId": "org.onosproject.ovsdb", 
   "key": "0x01",
   "priority": 100, 
   "ingressPoint": 
   { 
     "device": "of:0000000000000001", 
     "port": "1" 
   }, 
   "egressPoint": 
   { 
     "device": "of:0000000000000001", 
     "port": "7" 
   }}' -u onos:rocks 'http://localhost:8181/onos/v1/intents'
 
curl -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d '{ 
   "type": "PointToPointIntent",
   "appId": "org.onosproject.ovsdb",
   "key": "0x12",
   "priority": 100, 
   "ingressPoint": 
   {
     "device": "of:0000000000000001", 
     "port": "7"
   },
   "egressPoint": 
   {
     "device": "of:0000000000000001", 
     "port": "1"
   }
 }' -u onos:rocks 'http://localhost:8181/onos/v1/intents'

curl -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d '{ 
   "type": "PointToPointIntent",
   "appId": "org.onosproject.ovsdb",
   "key": "0x13",
   "priority": 100,
   "ingressPoint": 
   {
     "device": "of:0000000000000002", 
     "port": "7"
   },
   "egressPoint": 
   {
     "device": "of:0000000000000002", 
     "port": "1"
   }
 }' -u onos:rocks 'http://localhost:8181/onos/v1/intents'
 
 curl -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d '{ 
   "type": "PointToPointIntent",
   "appId": "org.onosproject.ovsdb",
   "key": "0x14",
   "priority": 100,
   "ingressPoint": 
   {
     "device": "of:0000000000000002", 
     "port": "1"
   },
   "egressPoint": 
   {
     "device": "of:0000000000000002", 
     "port": "7" 
   }
 }' -u onos:rocks 'http://localhost:8181/onos/v1/intents'