#!/usr/bin/env python3

import serial
import paho.mqtt.client as paho
from time import sleep

try:
    ser = serial.Serial("/dev/ttyACM0", 115200)
    sleep(0.1)
    ser.flushInput()
    print(ser.name)

    ser.write(b"SHOW 11\n")
    ser.write(b"SHOW 22\n")
    client = paho.Client()
    client.connect("mqtt.eclipseprojects.io")


    def on_message(mosq, obj, msg):
        print(msg.payload)
        ser.write(msg.payload + b"\n")
        ser.flush()

    client.on_message = on_message
    client.subscribe("nsi/display")

    client.loop_forever()


except Exception as e:
    print("Unable to open serial port")
    raise

