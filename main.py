import machine
import utime
import dht
from umqtt.simple import MQTTClient
import network
from credentials import ssid, password
from hcsr04 import HCSR04

mqtt_server = "broker.hivemq.com"
mqtt_topic = "iot/eoi"

dht_pin = machine.Pin(27)
dht_sensor = dht.DHT22(dht_pin)

sonar = HCSR04(trigger_pin=13, echo_pin=12)

led_pin = machine.Pin(25, machine.Pin.OUT)
led_state = False

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect(ssid, password)

while not sta_if.isconnected():
    pass

def publish_mqtt_message(topic, message):
    try:
        client = MQTTClient("esp32", mqtt_server)
        client.connect()
        client.publish(topic, str(message))
        client.disconnect()
    except Exception as e:
        print("Error al publicar mensaje MQTT:", e)

def alert_movement():
    global led_state
    led_state = True
    led_pin.on()
    utime.sleep(5)
    led_state = False
    led_pin.off()

def mqtt_callback(topic, msg):
    global distance

    msg = msg.decode()
    topic = topic.decode()

    if topic == mqtt_topic:
        if msg.startswith("Distancia:"):
            distance_str = msg.split(":")[1].strip().split(" ")[0]
            distance = float(distance_str)
            if distance is not None and distance <= 10:
                alert_movement()
                publish_mqtt_message(mqtt_topic, "Alerta, distancia inferior o igual a 10cm.")

def connect_mqtt():
    global client
    client = MQTTClient("esp32", mqtt_server)
    client.set_callback(mqtt_callback)
    client.connect()
    client.subscribe(mqtt_topic)

def check_mqtt_messages():
    try:
        client.check_msg()
    except OSError as e:
        print("Error al verificar mensajes MQTT:", e)

connect_mqtt()

distance = 0  

while True:
    try:
        check_mqtt_messages()
        dht_sensor.measure()
        temperature = dht_sensor.temperature()
        humidity = dht_sensor.humidity()
        distance = sonar.distance_cm()

        if temperature is not None:
            publish_mqtt_message(mqtt_topic, "Temperatura: {}°C".format(temperature))
        else:
            publish_mqtt_message(mqtt_topic, "Error al leer la temperatura")

        if humidity is not None:
            publish_mqtt_message(mqtt_topic, "Humedad: {}%".format(humidity))
        else:
            publish_mqtt_message(mqtt_topic, "Error al leer la humedad")

        if distance is not None:
            publish_mqtt_message(mqtt_topic, "Distancia: {} cm".format(distance))
        else:
            publish_mqtt_message(mqtt_topic, "Error al leer la distancia")

        utime.sleep(1)  # Esperar 1 segundo antes de la siguiente iteración
    except OSError as e:
        print("Error:", e)


