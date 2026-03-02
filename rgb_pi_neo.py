from flask import Flask, request, jsonify
import board
import neopixel

# ==========================================
# KONFIGURATION
# ==========================================

STRIP_CONFIG = {
    0: {"pin": board.D18, "count": 30},
    1: {"pin": board.D13, "count": 30},
    2: {"pin": board.D12, "count": 15},
}

BRIGHTNESS = 0.5
HOST = "0.0.0.0"
PORT = 80

# ==========================================
# INITIALISIERUNG
# ==========================================

app = Flask(__name__)
strips = {}


def init_strips():
    global strips
    for strip_id, cfg in STRIP_CONFIG.items():
        strips[strip_id] = neopixel.NeoPixel(
            cfg["pin"],
            cfg["count"],
            brightness=BRIGHTNESS,
            auto_write=True
        )

# ==========================================
# HILFSMETHODEN
# ==========================================

def clamp(v):
    return max(0, min(255, int(v)))


def set_strip_color(strip_id, r, g, b):
    if strip_id not in strips:
        return False

    strips[strip_id].fill((clamp(r), clamp(g), clamp(b)))
    return True


def turn_off(strip_id):
    return set_strip_color(strip_id, 0, 0, 0)

# ==========================================
# API
# ==========================================

@app.route("/")
def index():
    return jsonify({
        "service": "Multi-Strip API",
        "available_strips": list(strips.keys())
    })


@app.route("/api/strip/<int:strip_id>", methods=["POST"])
def api_set_strip(strip_id):

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON"}), 400

    if "r" in data and "g" in data and "b" in data:
        if not set_strip_color(strip_id, data["r"], data["g"], data["b"]):
            return jsonify({"error": "Invalid strip"}), 400

        return jsonify({
            "success": True,
            "strip": strip_id
        })

    if data.get("state") == "off":
        turn_off(strip_id)
        return jsonify({"success": True, "state": "off"})

    return jsonify({"error": "Invalid request"}), 400


# ==========================================
# START
# ==========================================

if __name__ == "__main__":
    init_strips()
    app.run(host=HOST, port=PORT)