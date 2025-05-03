#
# By: Danyeol Chae and Shemaiah Kamran
# Date: April 20, 2025
# 
#
#################################################
import alsaaudio
import struct
import numpy as np
import json
import threading
import time
import paho.mqtt.client as mqtt
from gpiozero import Servo


# MQTT Setup
BROKER = "test.mosquitto.org"
PORT = 1883

TOPIC_theremin_pitch =  "cs326/theremin",
TOPIC_theremin_volume =  "cs326/theremin/volume",
TOPIC_theremin_octave =  "cs326/theremin/octave",
TOPIC_theremin_effect =   "cs326/theremin/effect",
TOPIC_theremin_metronome =   "cs326/theremin/metronome"


# Audio setup
sample_rate = 48000
audio_out = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK, alsaaudio.PCM_NORMAL, device="default")
audio_out.setchannels(1)
audio_out.setrate(sample_rate)
audio_out.setformat(alsaaudio.PCM_FORMAT_S16_LE)
audio_out.setperiodsize(1024)


# Default values for used variables 
frequency = 440.0
frequency2 = 440.0
volume = 0.1
current_phase = 0.0
current_phase2 = 0.0
effect_type = "sine" # for sound effect 
attack_gain = 0.0 # for sound effect
tremolo_phase = 0.0 # for sound effect
vibrato_phase = 0.0 # for sound effect 
amplifier1 = 1 # amplifier for octave control
amplifier2 = 1 # amplifier for ocatve control 
metronome_running = False
servo = None
metronome_thread = None
lock = threading.Lock()


# mapped frequencies from distance for sensor/ frequency 1
def distance_to_note_frequency(cm):
   if cm <= 7:    return 261.63
   elif cm <= 11: return 293.66
   elif cm <= 15: return 329.63
   elif cm <= 19: return 349.23
   elif cm <= 23: return 392.00
   elif cm <= 27: return 440.00
   elif cm <= 31: return 493.88
   else:          return 523.25






# mapped frequencies from distance for sensor/ frequency 2, start at lower frequenct/ octave 
def distance_to_note_frequency_2(cm):
   if cm <= 7:    return 130.8
   elif cm <= 11: return 146.8
   elif cm <= 15: return 164.8
   elif cm <= 19: return 174.6
   elif cm <= 23: return 196.0
   elif cm <= 27: return 220.0
   elif cm <= 31: return 246.9
   else:          return 261.63


def audio_loop():
   global current_phase, current_phase2, tremolo_phase, vibrato_phase, attack_gain
  
   duration = 0.05  # 50ms buffer
   samples = int(sample_rate * duration)


   while True:
       with lock:
           freq1 = frequency
           freq2 = frequency2
           vol = volume
           effect = effect_type

	# Code for effects provided by ChatGPT as we could not find anything on sound effects anywhere else 
	# the code wasn't copied directly but read through and reframed according to understanding however 
	# basic understanding was achieved through AI
       # Calculate phase increments
       step1 = 2 * np.pi * freq1 / sample_rate
       step2 = 2 * np.pi * freq2 / sample_rate


       # Generate phase arrays
       phases1 = (current_phase + np.arange(samples) * step1) % (2 * np.pi)
       phases2 = (current_phase2 + np.arange(samples) * step2) % (2 * np.pi)


       # Initialize signals
       s1, s2 = np.zeros(samples), np.zeros(samples)


       # Apply selected effect by using variance in the frequencies
       if effect == "organ":
           s1 = 1.0 * np.sin(phases1) + 0.6 * np.sin(3*phases1) + 0.3 * np.sin(5*phases1)
           s2 = 1.0 * np.sin(phases2) + 0.6 * np.sin(3*phases2) + 0.3 * np.sin(5*phases2)
           s1 /= 1.9
           s2 /= 1.9


       elif effect == "violin":
           vibrato = 0.5 * np.sin(2 * np.pi * 5 * (vibrato_phase + np.arange(samples)/sample_rate))
           s1 = 0.5 * np.sin(phases1 + vibrato) + 0.3 * np.sin(2*phases1) + 0.2 * np.sin(3*phases1)
           s2 = 0.5 * np.sin(phases2 + vibrato) + 0.3 * np.sin(2*phases2) + 0.2 * np.sin(3*phases2)
           attack_gain = min(1.0, attack_gain + (1.0 / (0.5 * sample_rate / samples)))
           s1 *= attack_gain
           s2 *= attack_gain
           vibrato_phase += samples/sample_rate * 5


       elif effect == "harmonium":
           tremolo = 1.0 + 0.3 * np.sin(2 * np.pi * 6 * (tremolo_phase + np.arange(samples)/sample_rate))
           s1 = (1.0 * np.sin(phases1) + 0.4 * np.sin(3*phases1)) * tremolo
           s2 = (1.0 * np.sin(phases2) + 0.4 * np.sin(3*phases2)) * tremolo
           s1 /= 1.4
           s2 /= 1.4
           tremolo_phase += samples/sample_rate * 6


       else:  # Sine wave
           s1 = np.sin(phases1)
           s2 = np.sin(phases2)


       # Mix and apply volume
       mixed = (s1 + s2) / 2 * vol


       # write to audio
       buffer = (mixed * 32767).astype(np.int16)
       wave_data = struct.pack('<' + ('h' * len(buffer)), *buffer)
       audio_out.write(wave_data)


       # Update phases
       current_phase = phases1[-1] + step1
       current_phase2 = phases2[-1] + step2


def metronome_loop(bpm):
   global metronome_running, servo
   interval = 60 / bpm / 2
  
   try:
       servo = Servo(18, min_pulse_width=0.0005, max_pulse_width=0.0025)
       while metronome_running:
           servo.min()
           time.sleep(interval)
           servo.max()
           time.sleep(interval)
   except Exception as e:
       print(f"Metronome error: {str(e)}")
   finally:
       if servo:
           servo.close()
       metronome_running = False


def on_message(client, userdata, msg):
   global frequency, frequency2, volume, amplifier1, amplifier2, effect_type, attack_gain
   global metronome_running, servo, metronome_thread
  
   try:
       payload = json.loads(msg.payload.decode())
   except:
       payload = msg.payload.decode()




   with lock:
       if msg.topic == "cs326/theremin":
	# message from sonic sensors
           pitch_cm = payload.get("pitch", 20)
           pitch2_cm = payload.get("pitch2", 20)
	# Use amplifier to change octaves, going up one octave means multiplying octave by 2, going down an octave means dividing by 2


           frequency = amplifier1 * distance_to_note_frequency(pitch_cm)
           frequency2 = amplifier2 * distance_to_note_frequency_2(pitch2_cm)
	# message from webpage for volume control 
       elif msg.topic == "cs326/theremin/volume":
           volume = max(0.0, min(1.0, payload.get("volume", 50) / 100.0))


	# message from webpage for octave control
       elif msg.topic == "cs326/theremin/octave":
           amplifier1 = payload.get("octave1", 1)
           amplifier2 = payload.get("octave2", 1)


	# message from webpage for sound effect control 
       elif msg.topic == "cs326/theremin/effect":
           if payload in ["sine", "organ", "violin", "harmonium"]:
               effect_type = payload
               attack_gain = 0.0


	# message from webpage for metronome control 
       elif msg.topic == "cs326/theremin/metronome":
           command = payload.get("command")
           if command == "start":
               bpm = payload.get("bpm", 120)
               if not metronome_running:
                   metronome_running = True
                   if metronome_thread and metronome_thread.is_alive():
                       metronome_thread.join()
                   metronome_thread = threading.Thread(target=metronome_loop, args=(bpm,))
                   metronome_thread.start()
           elif command == "stop":
               metronome_running = False


# MQTT Client setup
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(BROKER, PORT, 60)

# Subscribe to all topics
client.subscribe(TOPIC_theremin_pitch)
client.subscribe(TOPIC_theremin_volume)
client.subscribe(TOPIC_theremin_octave)
client.subscribe(TOPIC_theremin_effect)
client.subscribe(TOPIC_theremin_metronome)

try:
   audio_loop()
except KeyboardInterrupt:
   metronome_running = False
   if servo:
       servo.close()
   client.loop_stop()
   client.disconnect()
   print("\nStopped")
