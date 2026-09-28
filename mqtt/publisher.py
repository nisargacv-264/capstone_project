# import json
# import time
# import paho.mqtt.client as mqtt

# BROKER = "localhost"
# PORT = 1883
# TOPIC = "telemetry/test"

# client = mqtt.Client()

# client.connect(BROKER, PORT, 60)

# print("MQTT Publisher connected")
# print("Publishing messages...")

# while True:

#     data = {
#         "temperature": 25.5,
#         "pressure": 1013.2,
#         "accel_x": 0.2,
#         "accel_y": 0.1,
#         "accel_z": 9.8
#     }

#     message = json.dumps(data)

#     client.publish(TOPIC, message)

#     print("Published:", message)

#     time.sleep(2)

import json
import time

import paho.mqtt.client as mqtt

from simulator.simulator import generate_data


BROKER = "localhost"
PORT = 1883
TOPIC = "telemetry/all"

client = mqtt.Client()

client.connect(BROKER, PORT, 60)

print("MQTT Publisher connected")
print("Publishing sensor telemetry...")


try:

    while True:

        # Get telemetry from the simulator
        sensor_data = generate_data()

        # Convert Python dictionary to JSON
        message = json.dumps(sensor_data)

        # Publish telemetry
        client.publish(TOPIC, message)

        print("\nPublished:")
        print(json.dumps(sensor_data, indent=4))
        print("-" * 60)

        time.sleep(1)

except KeyboardInterrupt:

    print("\nPublisher stopped.")

finally:

    client.disconnect()