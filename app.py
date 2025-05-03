from flask import Flask, render_template
import subprocess
import threading

app = Flask(__name__)

# Function to run subscriber in background
def start_subscriber():
    subprocess.run(["python3", "subscriber-theremin.py"])

@app.route('/')
def index():
    return render_template("index.html")

if __name__ == "__main__":
    # Start the subscriber code in a thread
    t = threading.Thread(target=start_subscriber)
    t.daemon = True
    t.start()

    # Start the Flask web server
    app.run(host='153.106.96.33', port=5000, debug=False)
