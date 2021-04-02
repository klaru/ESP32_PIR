from machine import Pin, reset, freq, unique_id
from sys import platform
from time import sleep
from ubinascii import hexlify
from boot import load_config
from umqttsimple import MQTTClient

# LED is active HIGH on ESP32 and active LOW on ESP8266
if platform == "esp32":               
    ledon = 1
    ledoff = 0
    pirpin = 17
elif platform == "esp8266":                              
    ledon = 0
    ledoff = 1
    pirpin = 0
    
led = Pin(2, Pin.OUT)       # Pin number for the board's built-in LED
pir = Pin(pirpin, Pin.IN)   # Pin number connected to PIR sensor output
topic = b'PIR'

client_id = hexlify(unique_id())

def connect_to_mqtt(config):
    client = MQTTClient(client_id, config['mqtt']['broker'])
    client.connect()
    print('Connected to %s MQTT broker' % (config['mqtt']['broker']))
    return client

def restart_and_reconnect():
    print('Failed to connect to MQTT broker. Restarting and reconnecting...')
    sleep(10)
    reset()
 
def reconnect_and_retry(client, var_topic, payload, config):
    print('Failed to publish to MQTT broker. Reconnecting...')
    try:
        client.connect()
        print('Reconnected to %s MQTT broker' % (config['mqtt']['broker']))
        client.publish(var_topic, payload, qos=1)
    except OSError:
        restart_and_reconnect()
        
def mqtt_publish(client, var_topic, payload, config):
    try:      
        client.publish(var_topic, payload, qos=1)
    except OSError:
        reconnect_and_retry(client, var_topic, payload, config)
    
# Main loop that will run forever:
def main(config):

    try:
        client = connect_to_mqtt(config)
    except OSError:
        sleep(10)
        restart_and_reconnect()
  
    print('Active')
    led.value(ledoff)    
    print('No motion')
    mqtt_publish(client, topic, b'nomotion', config)
    OLD_VALUE = 0
    while True:
        PIR_VALUE = pir.value()
        if PIR_VALUE:
        # PIR is detecting movement
            led.value(ledon)
            print ('Motion Detected!')
            mqtt_publish(client, topic, b'motion', config)
            sleep(300)
        else:
            # PIR is not detecting movement
            # Again check if this is the first time movement
            # stopped and print a message!      
            if OLD_VALUE:
                led.value(ledoff)
                print('No motion')
                mqtt_publish(client, topic, b'nomotion', config)
            sleep(1)
        OLD_VALUE = PIR_VALUE

        
if __name__ == "__main__":
    main(load_config())
