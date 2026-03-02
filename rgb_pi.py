from flask import Flask, request, jsonify
import RPi.GPIO as GPIO

app = Flask(__name__)

ALLOWED_PINS = []
HOST = "0.0.0.0"
PORT = 80


def init_gpio():
    GPIO.setmode(GPIO.BCM)
    for pin in ALLOWED_PINS:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)





def set_gpio_state(pin: int, state: str):
    if pin not in ALLOWED_PINS:
        return False, "Pin not allowed"
    
    if state == "on":
        GPIO.output(pin, GPIO.HIGH)
    elif state == "off":
        GPIO.output(pin, GPIO.LOW)
    else:
        return False, "State must be 'on' or 'off'"

    return True, None


def get_gpio_state(pin: int):  
    if pin not in ALLOWED_PINS:
        return None, "Pin not allowed"

    state = GPIO.input(pin)
    return ("on" if state else "off"), None


def validate_request(data):
    if not data:
        return False, "Missing JSON body"

    if "pin" not in data or "state" not in data:
        return False, "JSON must contain 'pin' and 'state'"

    return True, None






@app.route("/")
def index():
    return jsonify({
        "service": "GPIO REST API",
        "allowed_pins": ALLOWED_PINS
    })


@app.route("/api/gpio", methods=["POST"])
def api_set_gpio():

    data = request.get_json()

    valid, error = validate_request(data)
    if not valid:
        return jsonify({"error": error}), 400

    pin = data["pin"]
    state = data["state"].lower()

    success, error = set_gpio_state(pin, state)
    if not success:
        return jsonify({"error": error}), 400

    return jsonify({
        "success": True,
        "pin": pin,
        "state": state
    })


@app.route("/api/gpio/<int:pin>", methods=["GET"])
def api_get_gpio(pin):

    state, error = get_gpio_state(pin)
    if error:
        return jsonify({"error": error}), 400

    return jsonify({
        "pin": pin,
        "state": state
    })


if __name__ == "__main__":
    init_gpio()
    app.run(host=HOST, port=PORT)