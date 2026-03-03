from flask import Flask, request, jsonify
import board
import neopixel

# ==========================================
# KONFIGURATION
# ==========================================

STRIP_CONFIG = {
    0: {"pin": board.D18, "count": 30},
    1: {"pin": board.D13, "count": 30},
}

BRIGHTNESS = 0.5
HOST = "0.0.0.0"
PORT = 80

# ==========================================
# LED STRIP KLASSE
# ==========================================

class LEDStrip:

    def __init__(self, pin, count, brightness):
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

    # ---------- interne Hilfsmethode ----------
    def _clamp(self, value):
        return max(0, min(255, int(value)))

    # ---------- öffentliche Methoden ----------

    def set_color(self, r, g, b):
        self.r = self._clamp(r)
        self.g = self._clamp(g)
        self.b = self._clamp(b)

        self.pixels.fill((self.r, self.g, self.b))
        self.state = "on" if (self.r or self.g or self.b) else "off"

    def turn_off(self):
        self.set_color(0, 0, 0)

    def get_status(self):
        hex_color = "#{:02X}{:02X}{:02X}".format(self.r, self.g, self.b)

        return {
            "state": self.state,
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
    for strip_id, cfg in STRIP_CONFIG.items():
        strips[strip_id] = LEDStrip(
            cfg["pin"],
            cfg["count"],
            BRIGHTNESS
        )

# ==========================================
# API
# ==========================================

@app.route("/")
def index():
    return jsonify({
        "service": "Multi-Strip API (OOP)",
        "available_strips": list(strips.keys())
    })


@app.route("/api/strip/<int:strip_id>", methods=["POST"])
def set_strip(strip_id):

    if strip_id not in strips:
        return jsonify({"error": "Invalid strip"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON"}), 400

    strip = strips[strip_id]

    if "r" in data and "g" in data and "b" in data:
        strip.set_color(data["r"], data["g"], data["b"])
        return jsonify({"success": True})

    if data.get("state") == "off":
        strip.turn_off()
        return jsonify({"success": True})

    return jsonify({"error": "Invalid request"}), 400


@app.route("/api/strip/<int:strip_id>/status", methods=["GET"])
def get_strip_status(strip_id):

    if strip_id not in strips:
        return jsonify({"error": "Invalid strip"}), 400

    return jsonify({
        "strip": strip_id,
        **strips[strip_id].get_status()
    })

# ==========================================
# START
# ==========================================

if __name__ == "__main__":
    init_strips()
    app.run(host=HOST, port=PORT)