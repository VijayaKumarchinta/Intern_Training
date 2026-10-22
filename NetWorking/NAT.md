### Computer Networking ###
- The practice of connecting two/more computing devices and helps to enable them to communicate,exchange data,sharing resource among themselves via internet
- core concepts that came when we deal with CN:---
  - Nodes:- Any devices that sends/receives/forwards the data
  - Links:- The physical channel that carries the data
  - Protocals:- a set of rules that govering how the data is formed,addressed,transmitted and acknowledged
  - Network devices:- Routers,switches and wireless access points

- Data travels:-
  - Data is broken into small packets -> then each will be tagged with it's source and ip add -> routers helps us to direct the packets along with the best path -> then switches helps us to forward them within the local segment -> When they reached the destination those packets will be reassembled into original msg

- Network Types:
    - PAN - Personal area networks
      - where it covers only few meters such as hotspot
    - LAN - Local area Networks
      - where it covers the network within the local areas
    - MAN - Metropolitan area Networks
      - where it covers whole city
    - WAN - Wide Address Networks
      - where it covers the access throughout the global
    - CAN - Controller Area Network
      - msg based serial communication protocal that allows sensors, ECUs to communicate with eachother over a shared two-wire bus

- Reference models
    - OSI Model(7 steps):
      - Physical -> datalink -> network -> Transport layer -> session -> Presentation -> Application layer
    - TCP/IP Model(4 steps): A practical model which is compressed version of OCI model and popularily used throughout the CN
      - Network access -> internet -> Transport layer -> application layer

- Architectures:
  - Client->server:
    - the servers which are being maintained dedicatedly later on client requests them
  - Peer-to-Peer:
    - Each devices acts as both client and server
  
- Topologies:
  ``` 
  Bus:-
    - Where all devices connects to a single shared cable with terminators at both the ends
    - Drawbacks is if one cable breaks whole network will collids
    - Best for legacy/Industrial usuages
  ```
  - Star:-
    - Where it connects to every device via it's own cable to a hub/central switch
    - Drawbacks this got single point of failure
    - Best for office usage
  
  - Ring:-
    - where it connects to it's neighbours which helps to form a closed loop
    - Drawbacks is that one node failure can break the entire ring
    - Best for metro fibers
  
  - Mesh:-
    - Where it connects every device with direct point to point link to every other device
    - for n nodes a full mesh requires n(n-1)/2
    - Drawbacks are Scales  poorly
    - Best for Wans


### Network models & Data Encapsulation ###
- CN replys on layered models where each layer fulfill it's own specific functions
-  TCP/IP is a practical model which is used across the internet, where it contains 4 layers
   -  Network access -> internet -> Transport layer -> application layer
  
- Encapsulation:-
  - As data travels, each layer wraps the payload with its own control header which contains both resource and protocol instructions
- Decapsulation:-
  - The receiving host strips these headers layer by layer and moves to the application


### Addressing & Network Identify ###
- The communication replys on two types of addressing system
- MAC address(Media Access control):
  - Where it is being used for local node-node deliverable within a single LAN segment
  - It contians Physical hardware address which operates at layer 2
- IP address(Internet Protocal):
  - Where it is being used for routing data packets across the different network over a WAN or the internet
  
- Subnetting:
  - Where it divides large networks into small subnets by improving the security while isolating host traffic
- CIDR(Classless Inter-Domain Routing):
  - A notation helps to seperate the network bits from the host bits.


### Transport layer Protocals ###
- Transmission Control Protocal(TCP)
  - A connection oriented protocal where it helps to provide highly reliable, ordered and error-checking delivery of data b/w application over ip
  - Connection-oriented estblish happens using a three-way handshake
    - SYN: Sender reqs a connection and sends a sequence number
    - SYN-ACK: Receiver acknowledges the req and sends its own sequence number
    - ACK: Sender confirms the receipt and establish a connection
  - It assigns sequence number to every byte, which requires the receipt acknowledgments
  - Common usecases:-
    - HTTP/HTTPS, SSH, FTP and db connection


### Domain Name System & Resoultion ###
- Domain Name System(DNS):-
  - where it helps to translates human-friendly domain name into numerical IP address
- Steps to resolute the chain:-
  - Local cache lookup -> recursive resolver -> root DNS server -> TLD server -> Authoritative name server
- Essentials DNS record types:
  - A Record:- Maps a domain to an IPv4 address
  - AAAA Record:- Maps a domain to an IPv6 address


### Infrastructure, Routing & Network Edge ###
- Switches helps us to connect device with a local network segments and forward the frames based on the mac

- Routes helps us to connect to distinct networks and making a forwarding decision based on the IP address

- Firewalls helps us to filter and control based on the incoming/outgoing traffic based on predefined security rules, destination IPs, ports and protocals



## Network Address Translation(NAT) ##
- A fundemental technology that maps IP addresses b/w private local networks and public internet

- In this we mostly deal with IPv4 networking where internal devices on LAN are assigned to Private IP addresses and these private IP addresses are non-routable on public internet

-   Outbound request -> Inbound Return delivery -> Unsolicited Inbound Traffic

# Types of NAT #
- Static NAT:(single private IP to single static public IP)
  - Where it allows an internal host to be reachable from the outside world using a public ip address while mainataining internal IP address

- Dynamic NAT:(Multiple IPs to an available pooled multiple public IPs)
  - Where a internal device reqs internet access and dynamically binds to an unassigned public IP from the pool using routers and can be used that public IP when it is returned to the pool

- Port Address Translation:(Multiple IPs to a single public IP)
   - Where this PAT is a most commonly used NAT for implementation in home wifi routers and helps to enterprise the networks 

# Use cases #
- Preserving IPv4 address from exhaustion
- Network Perimeter securityin which NAT acts a firewall to prevent it!
- Outbound-only Connectivity for distributed and embedded systems where remote devices initiate outbound connections to servers


### Port Forwarding ###
- A specific configuration of NAT known as Destination NAT(DNAT) in which it creates a static rules that directs unsolicated the traffic to a specific device inside a local network from the internet
- The main purpose is to allows the external hosts to access a specific server/service which is hosted in a private network
- Inbound request is being initiated
- This a static where we have to set rules maually in the router to remain open permenatly for specific ports and IPs
# Steps:----
- Inbound request:-
  - An external client on the internet sends an http req to packet
- Interception & lookup:-
  - The router receives the packet on its WAN interface and checks its DNAT table
- Header Rewrite:-
  - Finding a match so the router can rewrites the header
- Internal delivery:-
  - then route forwards the modified packet across the local network


### IP Address ###
- A unique numerical identifier which is assigned to each device, which is connected to internet and helps those devices to establish the communication over the internet/local network to another device
  
## Structure of IP address
- An IP address divided into two distinct parts
  - Network portion/perfix :- the network in which the decvice belongs to
  - Host Portion/identifier:- the specific device on that particular network

## Versions of IP address
# Versions type:
  - IPv4:(32bits)
     - Formatted as four decimal octets seperated by dots(.) which is widely used
       - Ex:- 192.168.1.1
  - IPv6:(128bits)
       - Formated as eight groups of hexidecimal digits
       - Ex:- 2001:0db8:85a3::8a2e:0370:7334
  
# Scope type:
  - Private :- Reserved for internal use within the local networks
    - 10.0.0.0/8 - 255.0.0.0(subnet) - 1 octet is fixed - 10.0.0.0 to 10.255.255.255(16.7M)
      - Used for large organisations
    - 172.16.0.0/12 - 255.240.0.0(subnet) - 1 octet + 4 bits are fixed from the 2nd octet - 172.16.00 to 172.31.255.255(1M)
      - Used for mid-sized networks
    - 198.168.0.0/16 - 255.255.0.0(subnet) - 2 octets are fixed - 198.168.0.0 to 198.168.255.255(65k)
      - Used for home or daily usuage networks
  
  - Loopback:- Where a device talks to itself
    - 127.0.0.0 - 127.255.255.255

  - Link-Local(APIPA):- auto-assigned when dhcp fails
    - 169.254.0.0 - 169.254.255.255

  ```Multicast:- It enables group communication
    - 224.0.0.0 - 239.255.255.255
  ```
  
  ```Reserved/Experimental:- where which is not used for normal addressing
    - 240.0.0.0 - 255.255.255.254
  ```
  - Zero:- It specifies a default network
    - 0.0.0.0 - 0.255.255.255
  
  - Broadcast:- One to all which allows limited broadcast
    - 255.255.255.255
  
  - Public:-  Globally unique addressess assigned by the ISPs
    - to communicate over the public internet

# Allocation type:
  - Static IP address:
    - Where an ip address is being configured by the network admin so it is fixed over the time and commonly used for servers where its a constant reachable endpoint
  - Dynamic IP address:
    - Where an ip address automatically assigned to device by DHCP and changes over the time 


### Port Forwarding ###

# Why it exists
  let's say we run a small web server and someone from the outside your home newtwork wants to reach it, there's a drawback where outside world don't know our latop's private IP it knows our public IP
  ```
  app.run(debug=true)
  ```
  then flask uses defult values:
  ```
  host = 127.0.0.1
  port = 5000
  debug = True
  ```
- A connection is succeed when 3 doors are fully opened
  - Application Binding:
    - we run/make the host to list to 0.0.0.0
    - means accept connections on every network interface this machine got
    - so make sure to change the host name into 0.0.0.0
  - Windows Firewall:
    - make sure you fix the firewall where firewall allows the inbound connections
    - so make sure to add new rule in inbound rules so add the listening port to it and allow the connection
  - The router port forwarding:
    - make sure internet traffic reaches our laptop
    - so make to do changes in router admin page






to the outside world our ip address is availble under public ip but as for our device ip address it is a private ip address
so when we run a small app and someone from outside the network wants to access it they can't able to access it because of three doors blockage
- Application binding:
  - by default when we run a application it runs on localhost on our laptop/computer which is accessed through our device itself no outer/access over internet
  - so to avoid it we must run the applciation on "0.0.0.0" host in which it allows us to access the server with whatever interfaces the device got 
- Windows firewall:
  - the firewall is there to always block the inbound connections and acts as a defender all the time so we have to configure to the port what ever ther server is listening
  - so it allows us to open on different device with same LAN
- the router port forwarding:
  - 