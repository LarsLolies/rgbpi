import os
import requests
from dotenv import load_dotenv

# .env laden
load_dotenv()

url = os.getenv("IP_PI")
if not url:
    raise ValueError("IP_PI ist nicht in der .env gesetzt!")

# Sauber sicherstellen, dass keine doppelte / entsteht
url = url.rstrip("/")


def testget():
    """GET /strip/0/status"""
    try:
        full_url = url + "/strip/0/status"
        print("GET Request an:", full_url)

        response = requests.get(full_url, timeout=5)
        print("Status Code:", response.status_code)
        print("Raw Text:", response.text)

        response.raise_for_status()
        data = response.json()
        print("JSON:", data)

    except requests.exceptions.RequestException as e:
        print(f"Request Fehler: {e}")

    except ValueError:
        print("Antwort ist kein JSON:")
        print(response.text)


def testPostStaticColor():
    """POST /strip/0 - setze Farbe auf Rot"""
    try:
        full_url = url + "/strip/0"
        payload = {"r": 255, "g": 0, "b": 0}
        print("POST Request an:", full_url, "mit Payload:", payload)

        response = requests.post(full_url, json=payload, timeout=5)
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        response.raise_for_status()
        print("Farbe erfolgreich gesetzt!")

    except requests.exceptions.RequestException as e:
        print(f"Request Fehler: {e}")




def addRainbowAnimation():
    """Fügt Rainbow-Animation zu Strip 1 hinzu"""
    try:
        full_url = url + "/strip/1/animation/add"
        payload = {
            "animation": "rainbow"  # ✅ richtig
        }

        print("POST Request an:", full_url, "mit Payload:", payload)
        response = requests.post(full_url, json=payload, timeout=5)
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        response.raise_for_status()
        print("Rainbow Animation auf Strip 1 gestartet!")

    except requests.exceptions.RequestException as e:
        print(f"Request Fehler: {e}")



def setStrip2Green():
    """Setzt Strip 2 auf grün"""
    try:
        full_url = url + "/strip/2"
        payload = {"r": 0, "g": 255, "b": 0}  # Grün
        print("POST Request an:", full_url, "mit Payload:", payload)
        response = requests.post(full_url, json=payload, timeout=5)
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        response.raise_for_status()
        print("Strip 2 auf Grün gesetzt!")

    except requests.exceptions.RequestException as e:
        print(f"Request Fehler: {e}")


def addColorFlickerStrip2():
    """Fügt color_flicker Animation zu Strip 2 hinzu"""
    try:
        full_url = url + "/strip/2/animation/add"
        payload = {"animation": "color_flicker"}
        print("POST Request an:", full_url, "mit Payload:", payload)
        response = requests.post(full_url, json=payload, timeout=5)
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        response.raise_for_status()
        print("color_flicker Animation auf Strip 2 gestartet!")

    except requests.exceptions.RequestException as e:
        print(f"Request Fehler: {e}")




if __name__ == "__main__":
    print("=== LED Control Script ===")
    
    # Status Strip 0
    testget()
    
    # Rot auf Strip 0 setzen
    print("\n--- Setze Strip 0 auf Rot ---")
    testPostStaticColor()
    
    # Rainbow Animation auf Strip 1
    print("\n--- Starte Rainbow Animation auf Strip 1 ---")
    addRainbowAnimation()
    
    # Grün auf Strip 2
    print("\n--- Setze Strip 2 auf Grün ---")
    setStrip2Green()
    
    # brightness_flicker auf Strip 2
    print("\n--- Starte color_flicker auf Strip 2 ---")
    addColorFlickerStrip2()
    
    # Status nach allen Änderungen
    print("\n--- Status nach allen Aktionen ---")
    testget()