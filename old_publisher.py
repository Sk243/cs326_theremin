# publisher_pi_theremin.py
import time
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import json

# Pin setup
TRIG1, ECHO1 = 17, 18  # Pitch
TRIG2, ECHO2 = 27, 22  # Volume

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG1, GPIO.OUT)
GPIO.setup(ECHO1, GPIO.IN)
GPIO.setup(TRIG2, GPIO.OUT)
GPIO.setup(ECHO2, GPIO.IN)

# MQTT Setup
BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "cs326/theremin"
#USERNAME = "cs326"
#PASSWORD = "piot"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
#client.username_pw_set(USERNAME, PASSWORD)
client.connect(BROKER, PORT, 60)
client.loop_start()

# Distance measurement function
def measure_distance(trig, echo):
    GPIO.output(trig, GPIO.LOW)
    time.sleep(0.05)
    GPIO.output(trig, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(trig, GPIO.LOW)

    while GPIO.input(echo) == 0:
        pulse_start = time.time()
    while GPIO.input(echo) == 1:
        pulse_end = time.time()

    duration = pulse_end - pulse_start
    distance = duration * 17150  # in cm
    return round(distance, 2)

try:
    while True:
        pitch_cm = measure_distance(TRIG1, ECHO1)
        pitch2_cm = measure_distance(TRIG2, ECHO2)

        payload = {
            "pitch": pitch_cm,
            "pitch2": pitch2_cm
        }

        client.publish(TOPIC, json.dumps(payload))
        print(f"Published: {payload}")
        time.sleep(0.1)

except KeyboardInterrupt:
    GPIO.cleanup()
    client.loop_stop()
    client.disconnect()
