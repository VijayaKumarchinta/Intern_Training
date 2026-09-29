# till the relese of 3.0x the callbackapiversion is assigned to version 1 after recent updates we have to update it by ourselves and assign it to version 2

# TLS/SSL will always runs on 8883 port number because by default it is assigned to the it and we can change it in the conf file, when we dealing with TLS/SSL make sure to use the same port while connecting

# unlike terminal cmd we have to give paths in two sides
- server side(mosquitto.conf) because before starting the python code we have to start the mosquitto service
- client side(.py) because we will run and handle all the pub/subs in the python script which uses paho effectively

# we can assign the TLS/SSL config file to a setter(tls_set) in that we can create the config something like this in __init__ function:
  - self.client.tls_set(
        ca_certs="C:/Program Files/Mosquitto/ca.crt",
        certfile="C:/Program Files/Mosquitto/client.crt",
        keyfile="C:/Program Files/Mosquitto/client.key"       
      )
### when we pass expired/unmatched cert,key files, it will throw an sslcertverification error

# unlike terminal cmd we can directly set the username and password using 
 -  self.client.username_pw_set

# callback function in paho are predefined functions where we have to register them and paho will check for the code in the python script and run the snippet which was present by default, these callback functions expect to use all the parameters which are required and can be ignored sometimes
- on_connect() - automatically runs the code that present in the function whenever the mosquitto is conntecting
  - client - refers to the clientID which was passed
  - userdata - optional user data which is going to be enter by the user
  - flags - Connection information
  - reason_code - can able to know about the connection is successed or not
  - properties - MQTT 5 connection properties

- on_message() - automatically runs the code that present in the function whenever the mosquitto is receiving the message
  - client - refers to the clientID
  - userdata - refers to the data which was entered/printed optionally
  - message - the messages which are going to be send/recevied by the server/broker

# run function where the actual connection takes place
  - opens the tcp connection
  - then the loop will start and keep it alive while running in background
  - we can able to block the main thread by using the placeholder to keep the main thread alive
  - with/without the placeholder the msg 

# the loops helps us to run the mqtt communication in the background
  - we use loop_forever() when we want to reconnect automatically and will ahve to do pub/sub only
  - we use loop_start() when we manage multiple clients



::::: Types of errors we happend to encounter :::::
# Connection errors - ConnectionRefusedError

# TLS/SSL errors - ssl.SSLCertVerificationError

# Authentication errors 
  - reason_code == 0 = Connection is success
  - 1 - unacceptable protocal version = broker doesn't support mqtt ver
  - 2 - Identified rejected = Client_ID is already in use
  - 3 - server unavailble = Refusing connection
  - 4 - Bad_username/password = invalid/wrong credentials
  - 5 - not authorized = not allowed
  - 6/13 - server is moved = directs to another server
  - 7 - Alternative authentication required = wants a different auth method
  - 8 - Flow control = sending the messages too fast
  - 9 - Quota exceeded = Too many connections are there
  - 10 - Payload format invalid
  - 11 - Retain not supported = broker won't allow retained messages
  - 12 - QOS error = broker won't allow Qos levels 
  - 14 - server error = internal error

# protocal errors - MQTT_ERR_NO_CONN,MQTT_ERR_PROTOCAL
# network errors - timeout,socket
# Sub/pub errors - MQTT_ERR_SUCCESS
# Decoding errors - UnicodeDecodeError



--------------------------------------------------------------------------------------------------------------------------------

# Enabling logs helps us check the logs in the terminal in debug way.

# initilaizing the requried parameters like hostname,port,topic, msg,client_id, tls certs, call rollbacks by reduce the usuage of parameters in the methods

# we can use the inbuilt paho methods directly by using .client.connect/.client.publishe/.client.subscribe and by passing reuquired parameters into it we can directly able to use the inbuilt methods

# so when we use them it will look for call back functions and do the operations

# we use loop_forever so that we can run the loop in background while pub/sub doing there things being online

# we will pass our own subscriber method in on_connect callback and pass our own publisher method on on_sbscriber callback so that the subscriber will recive an ack from the server instead of calling pub instantly



