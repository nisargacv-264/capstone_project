import json
import paho.mqtt.client as mqtt
import requests

BROKER = "localhost"
PORT = 1883
TOPIC = "telemetry/all"

BACKEND_URL = "http://localhost:5000/analyze"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT Subscriber connected")
        client.subscribe(TOPIC)
        print("Subscribed to:", TOPIC)
    else:
        print("Connection failed with code:", rc)

def on_message(client, userdata, msg):
    try:
        sensor_data = json.loads(msg.payload.decode())

        print("\nTelemetry received:")
        print(json.dumps(sensor_data, indent=4))

        response = requests.post(BACKEND_URL, json=sensor_data, timeout=5)
        print("Backend response:", response.status_code)
        print(response.text)

    except Exception as e:
        print("Processing error:", e)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
print("Waiting for telemetry...")
client.loop_forever()