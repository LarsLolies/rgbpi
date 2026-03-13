from flask import Flask, request, jsonify
import board
import neopixel

# ==========================================
# KONFIGURATION
# ==========================================

STRIP_CONFIG = {
    18: {"board_pin": board.D18, "count": 1},
}

BRIGHTNESS = 0.5
HOST = "0.0.0.0"
PORT = 80

# ==========================================
# LED STRIP KLASSE
# ==========================================

class LEDStrip:

    def __init__(self, pin, gpio, count, brightness):
        self.pin = pin          # board.D18 für neopixel
        self.gpio = gpio        # 18 für API

        self.pixels = neopixel.NeoPixel(
            pin,
            count,
            brightness=brightness,
            auto_write=True
        )

        self.count = count
        self.r = 0
        self.g = 0
        self.b = 0
        self.state = "off"

    def _clamp(self, value):
        return max(0, min(255, int(value)))

    def set_color(self, r, g, b):
        self.r = self._clamp(r)
        self.g = self._clamp(g)
        self.b = self._clamp(b)

        self.pixels.fill((self.g, self.r, self.b))
        self.state = "on" if (self.r or self.g or self.b) else "off"

    def turn_off(self):
        self.set_color(0, 0, 0)

    def get_status(self):
        hex_color = "#{:02X}{:02X}{:02X}".format(self.r, self.g, self.b)

        return {
            "state": self.state,
            "pin": self.gpio,
            "r": self.r,
            "g": self.g,
            "b": self.b,
            "hex": hex_color
        }

# ==========================================
# INITIALISIERUNG
# ==========================================

app = Flask(__name__)
strips = {}

def init_strips():
    for gpio, cfg in STRIP_CONFIG.items():
        strips[gpio] = LEDStrip(
            cfg["board_pin"],
            gpio,
            cfg["count"],
            BRIGHTNESS
        )

# ==========================================
# API
# ==========================================

@app.route("/")
def index():
    return jsonify({
        "service": "Multi-Strip API",
        "available_pins": list(strips.keys())
    })


@app.route("/api/strip/<int:pin>", methods=["POST"])
def set_strip(pin):

    if pin not in strips:
        return jsonify({"error": "Invalid GPIO pin"}), 400

    data = request.get_json()

    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    strip = strips[pin]

    state = data.get("state")

    # LED ausschalten
    if state == "off":
        strip.turn_off()
        return jsonify({"success": True})

    # LED einschalten mit Farbe
    if state == "on":

        r = data.get("r", strip.r)
        g = data.get("g", strip.g)
        b = data.get("b", strip.b)

        strip.set_color(r, g, b)

        return jsonify({
            "success": True,
            "pin": pin,
            "state": "on",
            "r": r,
            "g": g,
            "b": b
        })

    return jsonify({"error": "Invalid state"}), 400


@app.route("/api/strip/<int:pin>/status", methods=["GET"])
def get_strip_status(pin):

    if pin not in strips:
        return jsonify({"error": "Invalid GPIO pin"}), 400

    return jsonify({
        "pin": pin,
        **strips[pin].get_status()
    })

# ==========================================
# START
# ==========================================

if __name__ == "__main__":
    init_strips()
    app.run(host=HOST, port=PORT)