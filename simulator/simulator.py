# import time
# import json
# from datetime import datetime

# from imu import IMUSimulator
# from temperature import TemperatureSimulator
# from barometer import BarometerSimulator
# from fault_injector import FaultInjector


# # Create sensor objects
# imu = IMUSimulator()
# temperature = TemperatureSimulator()
# barometer = BarometerSimulator()

# # Create fault injector
# fault_injector = FaultInjector()

# SAMPLE_INTERVAL = 1


# def generate_data():

#     # Get currently active faults
#     active_faults = fault_injector.update()

#     # Generate normal sensor data
#     imu_data = imu.generate()
#     temperature_data = temperature.generate()
#     barometer_data = barometer.generate()

#     # ------------------------------------------------
#     # Inject temperature fault
#     # ------------------------------------------------
#     if "high_temperature" in active_faults:
#         temperature_data = 70.0

#     # ------------------------------------------------
#     # Inject pressure fault
#     # ------------------------------------------------
#     if "high_pressure" in active_faults:
#         barometer_data["pressure"] = 1200.0

#     # ------------------------------------------------
#     # Inject acceleration fault
#     # ------------------------------------------------
#     if "high_acceleration" in active_faults:
#         imu_data["accel_x"] = 20.0
#         imu_data["accel_y"] = 20.0
#         imu_data["accel_z"] = 20.0

#     # ------------------------------------------------
#     # Sensor failure
#     # ------------------------------------------------
#     if "temperature_failure" in active_faults:
#         temperature_data = None

#     if "pressure_failure" in active_faults:
#         barometer_data = None

#     if "imu_failure" in active_faults:
#         imu_data = None

#     # Create complete telemetry packet
#     data = {
#         "timestamp": datetime.now().isoformat(),
#         "imu": imu_data,
#         "temperature": temperature_data,
#         "barometer": barometer_data
#     }

#     return data


# while True:

#     sensor_data = generate_data()

#     print(json.dumps(sensor_data, indent=4))
#     print("-" * 60)

#     time.sleep(SAMPLE_INTERVAL)

import time
import json
from datetime import datetime

# Support both:
# 1. Running simulator.py directly
# 2. Importing simulator.py from the project root
try:
    from .imu import IMUSimulator
    from .temperature import TemperatureSimulator
    from .barometer import BarometerSimulator
    from .fault_injector import FaultInjector
except ImportError:
    from imu import IMUSimulator
    from temperature import TemperatureSimulator
    from barometer import BarometerSimulator
    from fault_injector import FaultInjector


# Create sensor objects
imu = IMUSimulator()
temperature = TemperatureSimulator()
barometer = BarometerSimulator()

# Create fault injector
fault_injector = FaultInjector()

SAMPLE_INTERVAL = 1


def generate_data():

    # Get currently active faults
    active_faults = fault_injector.update()

    # Generate normal sensor data
    imu_data = imu.generate()
    temperature_data = temperature.generate()
    barometer_data = barometer.generate()

    # ------------------------------------------------
    # Inject temperature fault
    # ------------------------------------------------
    if "high_temperature" in active_faults:
        temperature_data = 70.0

    # ------------------------------------------------
    # Inject pressure fault
    # ------------------------------------------------
    if "high_pressure" in active_faults:
        barometer_data["pressure"] = 1200.0

    # ------------------------------------------------
    # Inject acceleration fault
    # ------------------------------------------------
    if "high_acceleration" in active_faults:
        imu_data["accel_x"] = 20.0
        imu_data["accel_y"] = 20.0
        imu_data["accel_z"] = 20.0

    # ------------------------------------------------
    # Sensor failure
    # ------------------------------------------------
    if "temperature_failure" in active_faults:
        temperature_data = None

    if "pressure_failure" in active_faults:
        barometer_data = None

    if "imu_failure" in active_faults:
        imu_data = None

    # Create telemetry packet
    data = {
        "timestamp": datetime.now().isoformat(),
        "imu": imu_data,
        "temperature": temperature_data,
        "barometer": barometer_data
    }

    return data


# Run continuously only when this file is executed directly.
# Do NOT run the loop when publisher.py imports generate_data().
if __name__ == "__main__":

    while True:

        sensor_data = generate_data()

        print(json.dumps(sensor_data, indent=4))
        print("-" * 60)

        time.sleep(SAMPLE_INTERVAL)