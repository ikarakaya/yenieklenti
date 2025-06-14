import os
import time
from umqttsimple import MQTTClient
import ubinascii
import machine
import micropython
import network
import esp
import random
from machine import Pin, I2C
import ssd1306
import re
from WIFI_CONFIG import SSID, PASSWORD


esp.osdebug(None)
import gc
gc.collect()

mqtt_server = '192.168.1.111'

client_id = ubinascii.hexlify(machine.unique_id())

#PUB/SUB topics
topic_pub_temp = b'esp32/temperature'
topic_pub_hum = b'esp32/humidity'
topic_pub_pres = b'esp32/pressure'
topic_sub_led = b'esp32/output'
topic_sub_oled = b'esp32/oled'


last_message = 0
message_interval = 30

led = machine.Pin(2, machine.Pin.OUT)

station = network.WLAN(network.STA_IF)

station.active(True)
station.connect(SSID, PASSWORD)

while station.isconnected() == False:
  pass

print('Connection successful')

print(os.listdir())


i2c = I2C(sda=Pin(21), scl=Pin(22))
display = ssd1306.SSD1306_I2C(128, 64, i2c)



def sub_cb(topic, msg):

  if topic == b'esp32/output' and msg == b'on':
    print('Turning LED oN!')
    led.value(0)
  elif topic == b'esp32/output' and msg == b'off':
    print('Turning LED oFF!')
    led.value(1)

  if topic == b'esp32/oled':
     display.fill(0)
     display.show()
     ilk=re.findall('.{1,8}',msg)
     oled_text_scaled(display, ilk[0], 0, 0, 2)
     oled_text_scaled(display, ilk[1], 0, 16, 2)
     display.show()
   
 

def connect_mqtt():
  global client_id, mqtt_server, topic_sub_led, topic_sub_oled
  client = MQTTClient(client_id, mqtt_server, user='mqtt_icin_kullanici', password='mqtt11',keepalive=60)
  client.connect()
  client.set_callback(sub_cb)
  client.subscribe(topic_sub_led)
  client.subscribe(topic_sub_oled)
  

  print('Connected to %s MQTT broker, subscribed to %s topic' % (mqtt_server, topic_sub_led))
  return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(10)
  machine.reset()

def oled_text_scaled(oled, text, x, y, scale, character_width=8, character_height=8):
    # temporary buffer for the text
    width = character_width * len(text)
    height = character_height
    temp_buf = bytearray(width * height)
    temp_fb = ssd1306.framebuf.FrameBuffer(temp_buf, width, height, ssd1306.framebuf.MONO_VLSB)

    # write text to the temporary framebuffer
    temp_fb.text(text, 0, 0, 1)

    # scale and write to the display
    for i in range(width):
        for j in range(height):
            pixel = temp_fb.pixel(i, j)
            if pixel:  # If the pixel is set, draw a larger rectangle
                oled.fill_rect(x + i * scale, y + j * scale, scale, scale, 1)



try:
  client = connect_mqtt()
  display.fill(0)
  oled_text_scaled(display, "ABCDEFGH", 0, 0, 2)
  oled_text_scaled(display, "abcdefgh", 0, 16, 2)
  display.show()
  time.sleep(3)
except OSError as e:
  restart_and_reconnect()

while True:
  try:
    client.check_msg()
    if (time.time() - last_message) > message_interval:
      temp = str(random.randrange(0,40))
      hum = str(random.randrange(10,90))
      pres = str(random.randrange(1000,4500))
      print(temp)
      print(hum)
      print(pres)
      client.publish(topic_pub_temp, temp)
      client.publish(topic_pub_hum, hum)
      client.publish(topic_pub_pres, pres)

      last_message = time.time()
  except OSError as e:
    restart_and_reconnect()
