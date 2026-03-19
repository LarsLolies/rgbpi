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
# STATUS
# ==========================================

strip_states = {
    strip_id: {
        "r": 0,
        "g": 0,
        "b": 0,
        "state": "off",
        "animations": []
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
# ANIMATION LOOP (pro Strip!)
# ==========================================

def animation_loop(strip_id):

    start, end = strip_ranges[strip_id]
    t = 0

    while True:

        animations = strip_states[strip_id]["animations"]

        if not animations:
            time.sleep(0.1)
            continue

        for i in range(start, end):

            r = strip_states[strip_id]["r"]
            g = strip_states[strip_id]["g"]
            b = strip_states[strip_id]["b"]

            # 🌈 Rainbow
            if "rainbow" in animations:
                r, g, b = wheel((i + t) & 255)

            # 💡 Brightness Flicker
            if "brightness_flicker" in animations:
                factor = 0.5 + ((t % 2) * 0.5)
                r = int(r * factor)
                g = int(g * factor)
                b = int(b * factor)

            # ⚡ Color Flicker
            if "color_flicker" in animations:
                if (i + t) % 10 == 0:
                    r, g, b = (255, 255, 255)

            pixels[i] = (r, g, b)

        t += 1
        time.sleep(0.05)

# ==========================================
# ANIMATION STEUERUNG
# ==========================================

def ensure_animation_thread(strip_id):

    if strip_id not in animation_threads:
        thread = threading.Thread(
            target=animation_loop,
            args=(strip_id,),
            daemon=True
        )
        animation_threads[strip_id] = thread
        thread.start()

def add_animation(strip_id, animation):

    if strip_id not in strip_states:
        return False

    if animation not in strip_states[strip_id]["animations"]:
        strip_states[strip_id]["animations"].append(animation)

    ensure_animation_thread(strip_id)
    return True

def remove_animation(strip_id, animation):

    if strip_id not in strip_states:
        return False

    if animation in strip_states[strip_id]["animations"]:
        strip_states[strip_id]["animations"].remove(animation)

    return True

def clear_animations(strip_id):

    if strip_id not in strip_states:
        return False

    strip_states[strip_id]["animations"].clear()
    return True

# ==========================================
# LED STEUERUNG
# ==========================================

def set_strip_color(strip_id, r, g, b):

    if strip_id not in strip_ranges:
        return False

    clear_animations(strip_id)

    r, g, b = clamp(r), clamp(g), clamp(b)
    start, end = strip_ranges[strip_id]

    for i in range(start, end):
        pixels[i] = (r, g, b)

    strip_states[strip_id]["r"] = r
    strip_states[strip_id]["g"] = g
    strip_states[strip_id]["b"] = b
    strip_states[strip_id]["state"] = "on" if (r or g or b) else "off"

    return True

def turn_off(strip_id):
    return set_strip_color(strip_id, 0, 0, 0)

def get_status(strip_id):

    if strip_id not in strip_states:
        return None

    s = strip_states[strip_id]

    hex_color = "#{:02X}{:02X}{:02X}".format(
        s["r"], s["g"], s["b"]
    )

    return {
        "strip": strip_id,
        "state": s["state"],
        "r": s["r"],
        "g": s["g"],
        "b": s["b"],
        "hex": hex_color,
        "animations": s["animations"]
    }

# ==========================================
# API
# ==========================================

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({
        "service": "LED API (multi-animation)",
        "strips": STRIPS,
        "total_leds": TOTAL_LEDS
    })

@app.route("/api/strip/<int:strip_id>", methods=["POST"])
def api_set_strip(strip_id):

    data = request.get_json()

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

@app.route("/api/strip/<int:strip_id>/animation/add", methods=["POST"])
def api_add_animation(strip_id):

    data = request.get_json()
    anim = data.get("animation")

    if add_animation(strip_id, anim):
        return jsonify({"animations": strip_states[strip_id]["animations"]})

    return jsonify({"error": "Invalid strip"}), 400

@app.route("/api/strip/<int:strip_id>/animation/remove", methods=["POST"])
def api_remove_animation(strip_id):

    data = request.get_json()
    anim = data.get("animation")

    if remove_animation(strip_id, anim):
        return jsonify({"animations": strip_states[strip_id]["animations"]})

    return jsonify({"error": "Invalid strip"}), 400

@app.route("/api/strip/<int:strip_id>/animation/clear", methods=["POST"])
def api_clear_animation(strip_id):

    if clear_animations(strip_id):
        return jsonify({"animations": []})

    return jsonify({"error": "Invalid strip"}), 400

# ==========================================
# START
# ==========================================

if __name__ == "__main__":
    app.run(host=HOST, port=PORT)