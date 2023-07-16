import network
from utime import sleep_ms
from credentials import ssid,password

red = network.WLAN(network.STA_IF)
red.active(True)
red.connect(ssid,password)
while not red.isconnected():
    sleep_ms(10)
print(red.ifconfig())