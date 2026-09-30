# import paho.mqtt.client as mqtt

# BROKER = "localhost"
# PORT = 1883
# TOPIC = "telemetry/test"


# def on_connect(client, userdata, flags, rc):
#     if rc == 0:
#         print("MQTT Subscriber connected")
#         client.subscribe(TOPIC)
#         print("Subscribed to:", TOPIC)
#     else:
#         print("Connection failed")


# def on_message(client, userdata, msg):

#     print("\nMessage received")
#     print("Topic:", msg.topic)
#     print("Data:", msg.payload.decode())


# client = mqtt.Client()

# client.on_connect = on_connect
# client.on_message = on_message

# client.connect(BROKER, PORT, 60)

# print("Waiting for messages...")

# client.loop_forever()

# import json
# import paho.mqtt.client as mqtt

# BROKER = "localhost"
# PORT = 1883
# TOPIC = "telemetry/all"


# def on_connect(client, userdata, flags, rc):
#     if rc == 0:
#         print("MQTT Subscriber connected")
#         client.subscribe(TOPIC)
#         print("Subscribed to:", TOPIC)
#     else:
#         print("Connection failed with code:", rc)


# def on_message(client, userdata, msg):

#     try:
#         sensor_data = json.loads(msg.payload.decode())

#         print("\nMessage received")
#         print("Topic:", msg.topic)
#         print(json.dumps(sensor_data, indent=4))
#         print("-" * 60)

#     except json.JSONDecodeError:
#         print("Invalid JSON received")


# client = mqtt.Client()

# client.on_connect = on_connect
# client.on_message = on_message

# client.connect(BROKER, PORT, 60)

# print("Waiting for telemetry...")

# client.loop_forever()


import json
import os
import sys
import paho.mqtt.client as mqtt
import requests

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

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

    except json.JSONDecodeError:
        print("Invalid JSON received")

    except Exception as e:
        print("Processing error:", e)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
print("Waiting for telemetry...")

client.loop_forever()