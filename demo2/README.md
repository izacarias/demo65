# README for Demo2
1. Open SSH connection to the server and change to the demo2 directory:
   ```
   USER=your_ssh_user
   ssh -A -L 3030:localhost:3030 -L 8181:localhost:8181 -L 8086:localhost:8086 -L 3000:localhost:3000 -J $USER@ngni-jumphost.fokus.fraunhofer.de $USER@6g-ric-ibn-1
   cd /home/demo2
   ```
   
2. Start the Mininet simulation:
   ```
   sudo ./start-network.py
   ```
   **PS:** Link1 will be selected by default ((bw=25Mbps, latency=7ms, loss=1%, jitter=1ms))

3. At the mininet prompt (`mininet>`), isse the iperf3 command to generate traffic (adjust -t and -i accordingly):
   ```
   mininet> h1 iperf3 -c 10.0.0.2 -t 60 -i 1
   ```

4. Start a new SSH session (to interact with the link selection)
   ```
   USER=your_ssh_user
   ssh -A -J $USER@ngni-jumphost.fokus.fraunhofer.de $USER@6g-ric-ibn-1
   cd /home/demo2
   ```

4.1. Select a different path to connect h1 to h2 by running the following script:
     ```
     ./select-l1.sh
     ```

4.2. Replace l1 by l2, l3 or l4 to select different links
     ```
     ./select-l2.sh
     ./select-l3.sh
     ./select-l4.sh
     ```

5. The monitoring data should be availible on InfluxDB and on Apache Fuseki Knowledge Base

   5.1 InfluxDB
   ```
   http://localhost:8086
   User: influxdb
   Password: influxdb
   Bucket: demo2
   ```
   5.2 Apache Jena Fuseki:
   ```
   http://localhost:3030/
   Dataset: ONOS (/ONOS)
   ```
