from flask import Flask
import logging

app = Flask(__name__)

# Disable Flask's default logging to keep the console clean
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

print("="*40)
print("  MOCK ESP8266 SERVER RUNNING")
print("  Listening at http://127.0.0.1:5000")
print("="*40)

@app.route('/<cmd>')
def handle_command(cmd):
    valid_commands = ["forward", "backward", "left", "right", "stop"]
    if cmd in valid_commands:
        print(f"[CAR ACTION]: {cmd.upper()}")
        return f"OK: {cmd}", 200
    else:
        print(f"[UNKNOWN]: {cmd}")
        return "Invalid Command", 400

if __name__ == '__main__':
    # Running on 5000 by default
    app.run(host='127.0.0.1', port=5000)
