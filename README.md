# Demo65

## Installation of Apache Jena Fuseki Server
```
mkdir -p $HOME/devel
cd $HOME/devel
wget -c https://dlcdn.apache.org/jena/binaries/apache-jena-fuseki-4.9.0.zip
unzip apache-jena-fuseki-4.9.0.zip
cd apache-jena-fuseki-4.9.0
```

### Run Apache Jena Fuseki Server
```
cd $HOME/devel/apache-jena-fuseki-4.9.0
# Create database directory
mkdir onos
 ./fuseki-server --loc=onos --update /ONOS
```

### Access Apache Jena Fuseki (Web) UI
```
http://localhost:3030
```
