from flask import Flask, request, jsonify
import board
import neopixel
import threading
import time

# ==========================================
# KONFIGURATION
# ==========================================

LED_PIN = board.D18
BRIGHTNESS = 0.5

STRIPS = {
    0: 2,
    1: 1
}

HOST = "0.0.0.0"
PORT = 80

# ==========================================
# STRIP BERECHNUNG
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
    pixel_order=neopixel.GRB
)

# ==========================================
# STATUS + ANIMATION
# ==========================================

strip_states = {
    strip_id: {
        "r": 0,
        "g": 0,
        "b": 0,
        "state": "off",
        "animation": None
    }
    for strip_id in STRIPS
}

animation_threads = {}

# ==========================================
# HILFSMETHODEN
# ==========================================

def clamp(v):
    return max(0, min(255, int(v)))

def wheel(pos):
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)

# ==========================================
# LED STEUERUNG
# ==========================================

def set_strip_color(strip_id, r, g, b):
    if strip_id not in strip_ranges:
        return False

    stop_animation(strip_id)

    r, g, b = clamp(r), clamp(g), clamp(b)
    start, end = strip_ranges[strip_id]

    for i in range(start, end):
        pixels[i] = (r, g, b)

    strip_states[strip_id] = {
        "r": r,
        "g": g,
        "b": b,
        "state": "on" if (r or g or b) else "off",
        "animation": None
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
        "hex": hex_color,
        "animation": s["animation"]
    }

# ==========================================
# ANIMATION PRO STRIP
# ==========================================

def rainbow_cycle_strip(strip_id):
    start, end = strip_ranges[strip_id]

    while strip_states[strip_id]["animation"] == "rainbow":
        for j in range(255):
            if strip_states[strip_id]["animation"] != "rainbow":
                break

            for i in range(start, end):
                pixels[i] = wheel((i + j) & 255)

            time.sleep(0.02)

def start_animation(strip_id, mode="rainbow"):

    if strip_id not in STRIPS:
        return False

    stop_animation(strip_id)

    strip_states[strip_id]["animation"] = mode

    thread = threading.Thread(
        target=rainbow_cycle_strip,
        args=(strip_id,)
    )

    animation_threads[strip_id] = thread
    thread.start()

    return True

def stop_animation(strip_id):
    if strip_id in strip_states:
        strip_states[strip_id]["animation"] = None

# ==========================================
# FLASK API
# ==========================================

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({
        "service": "LED API (per-strip animation)",
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

@app.route("/api/strip/<int:strip_id>/animation", methods=["POST"])
def api_animation(strip_id):

    data = request.get_json()
    mode = data.get("mode", "rainbow")

    if start_animation(strip_id, mode):
        return jsonify({"status": "started", "mode": mode})

    return jsonify({"error": "Invalid strip"}), 400

@app.route("/api/strip/<int:strip_id>/animation/stop", methods=["POST"])
def api_stop_animation(strip_id):

    stop_animation(strip_id)
    return jsonify({"status": "stopped"})

# ==========================================
# START
# ==========================================

if __name__ == "__main__":
    app.run(host=HOST, port=PORT)