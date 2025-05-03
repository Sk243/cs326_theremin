# CS326 Sensor Theremin Project
## By Danyeol Chae and Shemaiah Kamran 

This project implements a digital theremin that generates sound based on the distance from two sensors, combined with real-time adjustments through MQTT messages. Users can control the pitch, sound effects (like organ or violin), and even start a metronome—all through a simple web interface. A servo motor is used to control dual-tone audio, making the experience feel interactive and hands-free, just like a traditional theremin. The setup involves two Raspberry Pis: one reads data from the sensors, while the other handles the web interface and sends the sound to the audio system. With this system, users can play music without ever touching the device, using just their movement to control the sound.

Coding information:
Python was used for the backend code and a Flask webapp was developed for the frontend (UI)
