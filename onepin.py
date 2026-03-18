from flask import Flask, request, jsonify
import board
import neopixel

# ==========================================
# KONFIGURATION
# ==========================================

LED_PIN = board.D18
BRIGHTNESS = 0.5

# Anzahl LEDs pro "logischem" Strip
STRIPS = {
    0: 2,
    1: 1
}

HOST = "0.0.0.0"
PORT = 80

# ==========================================
# BERECHNUNG DER OFFSETS
# ==========================================

strip_ranges = {}
current_index = 0

for strip_id, count in STRIPS.items():
    strip_ranges[strip_id] = (current_index, current_index + count)
    current_index += count

TOTAL_LEDS = current_index

# ==========================================
# LED INITIALISIERUNG
# ==========================================

pixels = neopixel.NeoPixel(
    LED_PIN,
    TOTAL_LEDS,
    brightness=BRIGHTNESS,
    auto_write=True,
    pixel_order=neopixel.RGB  # ggf. anpassen!
)

# ==========================================
# STATUS SPEICHER
# ==========================================

strip_states = {
    strip_id: {"r": 0, "g": 0, "b": 0, "state": "off"}
    for strip_id in STRIPS
}

# ==========================================
# HILFSMETHODEN
# ==========================================

def clamp(v):
    return max(0, min(255, int(v)))

def set_strip_color(strip_id, r, g, b):
    if strip_id not in strip_ranges:
        return False

    r, g, b = clamp(r), clamp(g), clamp(b)

    start, end = strip_ranges[strip_id]

    for i in range(start, end):
        pixels[i] = (r, g, b)

    strip_states[strip_id] = {
        "r": r,
        "g": g,
        "b": b,
        "state": "on" if (r or g or b) else "off"
    }

    return True

def turn_off(strip_id):
    return set_strip_color(strip_id, 0, 0, 0)

def get_status(strip_id):
    if strip_id not in strip_states:
        return None

    s = strip_states[strip_id]
    hex_color = "#{:02X}{:02X}{:02X}".format(s["r"], s["g"], s["b"])

    return {
        "strip": strip_id,
        "state": s["state"],
        "r": s["r"],
        "g": s["g"],
        "b": s["b"],
        "hex": hex_color
    }

# ==========================================
# FLASK API
# ==========================================

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({
        "service": "LED Strip API (Single Pin)",
        "strips": STRIPS,
        "total_leds": TOTAL_LEDS
    })

@app.route("/api/strip/<int:strip_id>", methods=["POST"])
def api_set_strip(strip_id):

    if strip_id not in STRIPS:
        return jsonify({"error": "Invalid strip"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON"}), 400

    if "r" in data and "g" in data and "b" in data:
        set_strip_color(strip_id, data["r"], data["g"], data["b"])
        return jsonify({"success": True})

    if data.get("state") == "off":
        turn_off(strip_id)
        return jsonify({"success": True})

    return jsonify({"error": "Invalid request"}), 400

@app.route("/api/strip/<int:strip_id>/status", methods=["GET"])
def api_status(strip_id):

    status = get_status(strip_id)
    if not status:
        return jsonify({"error": "Invalid strip"}), 400

    return jsonify(status)

# ==========================================
# START
# ==========================================

if __name__ == "__main__":
    app.run(host=HOST, port=PORT)