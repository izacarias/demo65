# Demo65

## Steps for demonstration

1. Open SSH connection to the server:
```
ssh -A -L 3030:localhost:3030 -L 8181:localhost:8181 -L 8086:localhost:8086 -L 3000:localhost:3000 -J user@ngni-jumphost.fokus.fraunhofer.de user@6g-ric-ibn-1
```
2. Go to the Demo directory and start the simulated network
```
cd /home/demo
sudo ./start-network.py
```

3. Open a second SSH connection to the server and run the sync script
```
ssh -A -J user@ngni-jumphost.fokus.fraunhofer.de user@6g-ric-ibn-1
cd /home/demo/sync
source .venv/bin/activate
./main.py 
```

4. Run Iperf to generate traffic between hosts H1 and H3
In the first SSH connection (Where you seen the prompt "mininet>")
```
h1 iperf -u -c 10.0.0.3 -i 2 -t 20 -b 40m
```
Adjust -t to the time and -b to bandwidth (-b 40m to 40 Mbps, -b 100m to 100 Mbps)

## Install the required software

### Apache Jena Fuseki Server
```
sudo adduser fuseki --system --group
sudo mkdir -p /opt/fuseki
sudo mkdir -p /etc/fuseki
sudo chown -R root:fuseki /etc/fuseki
sudo chmod 775 /etc/fuseki
# Download Fuseki
mkdir -p $HOME/devel
cd $HOME/devel
wget -c https://dlcdn.apache.org/jena/binaries/apache-jena-fuseki-4.9.0.zip
unzip apache-jena-fuseki-4.9.0.zip
cd apache-jena-fuseki-4.9.0
# Copy files to destination
sudo cp fuseki.service /etc/systemd/system/
sudo mv * /opt/fuseki/
sudo systemctl daemon-reload

sudo systemctl start fuseki
sudo systemctl enable fuseki
```
#### Access Apache Jena Fuseki (Web) UI
```
http://localhost:3030
```

### InfluxDB
```
mkdir -p ~/devel && cd ~/devel
wget -q https://repos.influxdata.com/influxdata-archive_compat.key
echo '393e8779c89ac8d958f81f942f9ad7fb82a25e133faddaf92e15b16e6ac9ce4c influxdata-archive_compat.key' | sha256sum -c && cat influxdata-archive_compat.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg > /dev/null
echo 'deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg] https://repos.influxdata.com/debian stable main' | sudo tee /etc/apt/sources.list.d/influxdata.list

sudo apt-get update && sudo apt-get install -y influxdb2

# Start the service
sudo systemctl start influxdb
sudo systemctl enable influxdb
```
#### Check the installation
```
influx version
```
#### Configure InfluxDB 
```
Acess: http://localhost:8086
# Enter the following configuration
Username: influxdb
Password: influxdb
Oranization name: influxdb
Initial bucket name: mininet
```
> Do not forget to copy the API Token
Ex:
`kc-Uh3u0TR00zqsXu0lIKMg6bi_Q8OcVwzi3nbRRrXVkAFyC6Azi-c0BMGMRj5uoQelxOKENshjUoZjrZGxWNw==`


### Install Grafana
```
sudo apt-get install -y apt-transport-https software-properties-common wget
sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null

echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
sudo apt-get update

sudo apt-get install grafana

sudo systemctl daemon-reload
sudo systemctl start grafana-server
sudo systemctl status grafana-server
sudo systemctl enable grafana-server
```
> Grafana will be available on port 3000
> Initial user and password is admin/admin

#### Run the Synch python script to send some data to InfluxDB/Grafana
```
cd ~/sync/
source .venv/bin/activate
python main.py
```

## Workaround to start ONOS with different IP (not tested)
```
sudo rm /opt/onos/apache-karaf-4.2.9/data/db/partitions/data/partitions/1/raft-partition-1.{conf,meta}
sudo rm /opt/onos/apache-karaf-4.2.9/data/db/partitions/system/partitions/1/system-partition-1.{conf,meta}
```


Connect Grafana to InfluxDB
Go to Menu -> Connections -> Data Source
Under HTTP, use the following values
URL: http://localhost:8086
Organization:influxdb
Token: <GENERATE A NEW ONE>

### Create Dashboard
Go to Dashboards
Click on New -> New Dashboard

In the Query Panel, use the following query
```
from(bucket: "mininet")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "linkstats")
  |> filter(fn: (r) => r["path1"] == "linkusage")
  |> aggregateWindow(every: v.windowPeriod, fn: last, createEmpty: false)
  |> yield(name: "last")
```

### Use of venv to run python scripts
#### Create the environment
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
