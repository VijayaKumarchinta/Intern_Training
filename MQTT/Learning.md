MQTT is a lightweight, low bandwidth message queuing transport where it uses pub/sub to delivery the messages
- Client - a device that connects the server(broker) either pub or sub
- Broker - a server where it sends/receives the msgs from/to the clients
- pub - sends a msg / sub - receives a msg

# [Basic cmds to start]
net start mosquitto or mosquitto 

# [when we use conf file, if we want to make sure to run through service we have to add the path along with conf file then it will run]
net start mosquitto or mosquitto -c mosquitto.conf 

# [to stop the broker]
net stop mosquitto or Ctrl + c 

# [To restart the server]
net stop mosquitto && net start mosquitto or Ctrl + c and mosquitto / mosquitto -c mosquitto.conf 

# [when we install there will be default files so do changes in those through admin cmd and save it and run it]
avoid using echo instead of that make using the default config file and do changes accordingly 

# max_connections 10(total connection per listener)
we can include in the conf file so we can restrict how many devices can be connected using the port in that broker(server)

# global_max_connections(total connections per broker)
we can restrict no.of devices that can connect to the broker(server)

# global_max_clients(total no.of devices that can connect)
can restrict no.of devices that can remember by the broker

### TLS/SSL conf files (certificates: ca.key, ca.crt, server.*, client.*)

# first create a key with encryption(self-signed)
[ openssl genrsa -des3 -out ca.key 2048 ]

# then create the ca cert using the ca.key and pass which was provided earlier
[ openssl req -new -x509 -out ca.crt -key ca.key -days 365 ]

# create a server key for the broker
[ openssl genrsa -out server.key 2048 ]

# create server CSR with CN=your_ip (required for matching)

- [ openssl req -new -out server.csr -key server.key -subj "/CN=domain"] - this is good practice because even though we are using different wifi router we simply have to update in SAN and just need to regenrate the server.crt

Always take domainname/hostname when we dealing with creating server certificate
# server certificate using CA with SAN and creating a srl is a way of openssl so that it can able to track our CAcd 
[ openssl x509 -req -out server.crt -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days 365 -extfile san.cnf -extensions v3_req ]

# create a client key  for the clients 
[openssl genrsa -out client.key 2048]

# create client CSR with CN=client_name (skips interactive prompts)
# CN becomes the username when use_identity_as_username=true so the username is client1
[openssl req -new -out client.csr -key client.key -subj "/CN=client1"]

# creating the client certificate using client.csr, ca.crt, ca.key in client.crt with expiry
[openssl x509 -req -out client.crt -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days 360]

and in conf file include
# cafile - certificate of the CA file(helps to verify both server and client)
# certfile - certificate of the server file(helps to find the broker identity)
# keyfile - key of the server

# require_certificate and use_identity_as_username - always true when it check for the correct users

# -subj flag: useful for BOTH server and client CSR creation
# - Skips interactive prompts (Country, State, Org, CN, etc.)
# - For server: CN should match the IP/domain used to connect
# - For client: CN becomes the username (used with use_identity_as_username)
# - Essential for scripting/automation (generate certs for multiple clients)
# - Format: -subj "/C=IN/ST=State/L=City/O=Org/CN=identity" CN is must atleast
# always send msg through --cafile,--certfile,--keyfile


net stop mosquitto && net start mosquitto

[mosquitto_sub --cafile ca.crt --cert client.crt --key client.key -h 10.58.166.132 -p 8883 -t test]

[mosquitto_pub --cafile ca.crt --cert client.crt --key client.key -h 10.58.166.132 -p 8883 -t test -m "hello there"]


# if we connected to other wifi routers the ip address gonna change to configure that we use san.conf file so that we can connect to different ip address's by simply adding in the conf files it is an easy process instead of creating again

### SAN (Subject Alternative Name) - Detailed Explanation (san.cnf)

# What is SAN?
- SAN is an extra field in the server certificate that lists all valid
- IP addresses and domain names the server can accept connections from.
- OpenSSL 3.x REQUIRES SAN - without it, certificate verify fails!

# SAN Config File (my-san.cnf): stored alongside the certs at C:/Program Files/Mosquitto/san.cnf

[v3_req]
subjectAltName = @alt_names
[alt_names]
IP.1 = 10.58.166.132 
IP.2 = 127.0.0.1     
DNS.1 = localhost

# Explaining the terms:
    [v3_req]         = Section for X.509 v3 certificate extensions
    subjectAltName   = Field that adds extra identities to certificate
    @alt_names       = Reference to [alt_names] section below
    [alt_names]      = Section listing all valid IPs and DNS names
    IP.1             = First IP address (numbered from 1)
    IP.2             = Second IP address
    DNS.1            = First domain name (numbered from 1)

### Mosquitto Configuration File (mosquitto.conf → C:/Program Files/Mosquitto/mosquitto.conf)

# my real config: default file at C:/Program Files/Mosquitto/mosquitto.conf
# edited as admin and saved. The certificates (ca.crt, server.crt, server.key)
# are also stored inside the install folder: C:/Program Files/Mosquitto/

# listener port - which port the broker listens on
# allow_anonymous - whether unauthenticated clients can connect
# cafile - path to CA certificate (verifies server and client)
# certfile - path to server certificate (broker identity)
# keyfile - path to server private key
# require_certificate - must be true to force client cert authentication
# use_identity_as_username - uses CN from client cert as username
# password_file - NOT needed when using require_certificate

listener 8883
certfile C:/Program Files/Mosquitto/server.crt
keyfile C:/Program Files/Mosquitto/server.key
require_certificate true
cafile C:/Program Files/Mosquitto/ca.crt
use_identity_as_username true
allow_anonymous false

# Explaining the terms:
    listener 8883                   = Broker listens on port 8883 (TLS port)
    allow_anonymous false           = Rejects clients without valid cert
    cafile                          = CA cert path to verify both sides
    certfile                        = Server cert path for broker identity
    keyfile                         = Server private key for TLS handshake
    require_certificate true        = Forces client to provide a cert
    use_identity_as_username true   = Uses CN field from client cert as username



### so when we use IP address we have to regenerate new server.csr,crt files and when we use domain/localhost we can simply update the san file and regenerate the crt file again

### Don't ever use echo for creating files always do changes manually so it will prevent erasing the new lines

### max_connections - will tell exactly how many devices can stay online at the same time
### global_max_connections - will tell how many devices can connect at the same time
### global_max_clients - will tell exactly how many can save 


# CA files (ca.crt → C:/Program Files/Mosquitto/ca.crt) has to be installed and placed in Trusted root certification Authorities