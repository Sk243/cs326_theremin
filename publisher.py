# publisher_pi_theremin.py
import time
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import json

# Ultrasonic Sensor Configuration
TRIG1, ECHO1 = 17, 18  # First sensor (Pitch control)
TRIG2, ECHO2 = 27, 22  # Second sensor (Volume control)

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG1, GPIO.OUT)
GPIO.setup(ECHO1, GPIO.IN)
GPIO.setup(TRIG2, GPIO.OUT)
GPIO.setup(ECHO2, GPIO.IN)

# MQTT Configuration
BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "cs326/theremin"
MAX_DISTANCE = 100  # cm (for sensor sanity check)

# Initialize MQTT Client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, PORT, 60)
client.loop_start()

def measure_distance(trig, echo):
    """Measure distance using HC-SR04 ultrasonic sensor with error handling"""
    GPIO.output(trig, GPIO.LOW)
    time.sleep(0.05)
    
    # Send 10µs pulse
    GPIO.output(trig, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(trig, GPIO.LOW)

    pulse_start = time.time()
    pulse_end = time.time()
    
    timeout = 0.1  # 100ms timeout for no echo
    start_time = time.time()
    
    # Wait for echo to go low (start)
    while GPIO.input(echo) == 0:
        if time.time() - start_time > timeout:
            return None  # Timeout
        pulse_start = time.time()

    # Wait for echo to go high (end)
    start_time = time.time()
    while GPIO.input(echo) == 1:
        if time.time() - start_time > timeout:
            return None  # Timeout
        pulse_end = time.time()

    duration = pulse_end - pulse_start
    distance = (duration * 34300) / 2  # Speed of sound in cm/s
    
    # Sanity check
    if 2 < distance < MAX_DISTANCE:
        return round(distance, 2)
    return None

def main_loop():
    """Main sensor reading and publishing loop"""
    try:
        while True:
            # Read both sensors
            payload = {}
            
            # Sensor 1 (Pitch)
            dist1 = measure_distance(TRIG1, ECHO1)
            payload["pitch"] = dist1 if dist1 else 20  # Default to 20cm
            
            # Sensor 2 (Volume)
            dist2 = measure_distance(TRIG2, ECHO2)
            payload["pitch2"] = dist2 if dist2 else 20  # Default to 20cm
            
            # Publish payload
            client.publish(TOPIC, json.dumps(payload))
            print(f"Published: {payload}")
            
            time.sleep(0.1)  # 10Hz update rate

    except KeyboardInterrupt:
        print("\nCleaning up...")
        GPIO.cleanup()
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main_loop()