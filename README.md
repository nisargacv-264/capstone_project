# Remote Telemetry Monitoring & Diagnostics PoC

## 1. Project Overview

The **Remote Telemetry Monitoring & Diagnostics PoC** is a software-based monitoring system that simulates a remote embedded sensor node used during environmental testing.

The system continuously generates telemetry for:

- **IMU** — 3-axis acceleration and 3-axis angular velocity
- **Temperature**
- **Barometer** — pressure and altitude

The simulated telemetry is transmitted through **MQTT**, received by a subscriber, analyzed for abnormal conditions, stored in **SQLite**, exposed through a **Flask REST API**, and displayed on a web dashboard.

The project demonstrates how a real embedded monitoring solution can move from sensor acquisition to communication, diagnostics, storage, visualization, and data export even when physical hardware is not available.

### High-level data flow

```text
Virtual Sensor Simulator
        |
        v
Fault Injector
        |
        v
MQTT Publisher
        |
        v
Mosquitto MQTT Broker
        |
        v
MQTT Subscriber
        |
        v
Anomaly Detector
        |
        v
SQLite Database
        |
        v
Flask REST API
        |
        v
Web Dashboard
        |
        +------> CSV Export
```

---

## 2. Project Objective

The objective is to build a **software-only remote telemetry monitoring system** for an embedded node used during environmental testing.

The system:

1. Simulates realistic sensor measurements.
2. Generates telemetry continuously at a configurable sampling interval.
3. Simulates abnormal conditions and sensor failures.
4. Publishes telemetry through MQTT.
5. Receives telemetry using an MQTT subscriber.
6. Independently detects abnormal conditions using an anomaly detector.
7. Stores complete telemetry history in a database.
8. Stores detected anomaly events separately.
9. Provides telemetry through REST APIs.
10. Displays live and historical data on a web dashboard.
11. Shows warnings, critical conditions, and sensor failures.
12. Allows engineers to export telemetry data to CSV.

The project intentionally separates **fault generation** from **fault detection**.

The simulator creates abnormal sensor behavior, while the anomaly detector independently determines whether the received measurements are abnormal.

---

## 3. Why This Architecture Is Used

In a real embedded system, a sensor reports measurements such as:

```text
Temperature = 70 °C
Pressure = 1200 hPa
Acceleration = 20 m/s²
```

The sensor does not normally send a message saying:

```text
STATUS = CRITICAL
```

The monitoring software receives measurements and applies limits or diagnostic rules to determine whether the condition is normal, a warning, critical, or a sensor failure.

Since this PoC does not have physical hardware, the **Fault Injector** acts as the test mechanism that creates abnormal conditions.

Therefore:

```text
Fault Injector
      |
      | creates abnormal measurement
      v
Telemetry
      |
      v
Anomaly Detector
      |
      v
NORMAL / WARNING / CRITICAL / SENSOR_FAILURE
```

This separation makes the PoC representative of a real monitoring architecture.

---

## 4. System Architecture

### Complete Architecture

```text
+----------------------------+
|    Virtual Sensor Node     |
|                            |
|  IMU                       |
|  Temperature               |
|  Barometer                 |
+-------------+--------------+
              |
              v
+----------------------------+
|      Fault Injector        |
|                            |
| High temperature           |
| High pressure              |
| High acceleration          |
| Sensor failure             |
| Multiple simultaneous     |
| faults                     |
+-------------+--------------+
              |
              v
+----------------------------+
|      MQTT Publisher        |
+-------------+--------------+
              |
              v
+----------------------------+
|    Mosquitto MQTT Broker   |
|       localhost:1883       |
+-------------+--------------+
              |
              v
+----------------------------+
|      MQTT Subscriber       |
+-------------+--------------+
              |
              v
+----------------------------+
|      Anomaly Detector      |
|                            |
| Temperature rules          |
| Pressure rules             |
| IMU rules                  |
| Sensor failure detection   |
+-------------+--------------+
              |
              v
+----------------------------+
|       SQLite Database      |
|                            |
| telemetry                  |
| anomaly_events             |
+-------------+--------------+
              |
              v
+----------------------------+
|       Flask Backend        |
|                            |
| REST API                   |
| Latest data                |
| Historical data            |
| Anomaly data               |
| CSV export                 |
+-------------+--------------+
              |
              v
+----------------------------+
|       Web Dashboard        |
|                            |
| Live values                |
| Historical graphs          |
| Alerts                     |
| Sensor status              |
| CSV export                 |
+----------------------------+
```

---

## 5. Technologies Used

### Python

Python is used for:

- Sensor simulation
- Fault injection
- MQTT publisher/subscriber
- Anomaly detection
- Database access
- Flask backend
- CSV export
- Startup/launcher script

### MQTT

MQTT is the telemetry transport protocol.

The communication model is:

```text
Publisher -> Broker -> Subscriber
```

### Paho MQTT

The Python application uses `paho-mqtt` for MQTT publisher and subscriber functionality.

### Mosquitto

Eclipse Mosquitto is used as the local MQTT broker.

The broker listens on:

```text
localhost:1883
```

### Flask

Flask provides the REST API used by the dashboard.

The dashboard does not directly access SQLite:

```text
Dashboard -> Flask API -> SQLite
```

### SQLite

SQLite is the local telemetry database. No separate database server is required.

### Frontend

The dashboard uses:

- HTML
- CSS
- JavaScript
- Chart.js

---

## 6. Folder Structure

```text
C:\project
|
+-- run_project.py
+-- README.md
+-- requirements.txt
+-- .gitignore
+-- config.yaml
|
+-- simulator/
|   +-- __init__.py
|   +-- simulator.py
|   +-- imu.py
|   +-- temperature.py
|   +-- barometer.py
|   +-- fault_injector.py
|
+-- mqtt/
|   +-- __init__.py
|   +-- publisher.py
|   +-- subscriber.py
|
+-- backend/
|   +-- __init__.py
|   +-- app.py
|   +-- anomaly_detector.py
|   +-- database.py
|   +-- csv_export.py
|
+-- database/
|   +-- __init__.py
|   +-- database.py
|   +-- telemetry.db
|
+-- dashboard/
|   +-- templates/
|       +-- index.html
|   +-- static/
|       +-- css/
|       |   +-- style.css
|       +-- js/
|           +-- dashboard.js
|           +-- chart.umd.min.js
|
+-- logs/
```

### Component responsibilities

| File | Responsibility |
|---|---|
| `simulator/imu.py` | Generates IMU data |
| `simulator/temperature.py` | Generates temperature |
| `simulator/barometer.py` | Generates pressure and altitude |
| `simulator/fault_injector.py` | Generates simulated faults |
| `simulator/simulator.py` | Combines sensor data |
| `mqtt/publisher.py` | Publishes telemetry |
| `mqtt/subscriber.py` | Receives telemetry and starts processing |
| `backend/anomaly_detector.py` | Detects abnormal conditions |
| `database/database.py` | Writes telemetry and anomaly events |
| `backend/database.py` | Reads database data for Flask APIs |
| `backend/app.py` | Flask REST API |
| `backend/csv_export.py` | Generates CSV exports |
| `dashboard/templates/index.html` | Dashboard layout |
| `dashboard/static/js/dashboard.js` | Dashboard logic |
| `run_project.py` | Starts publisher, subscriber, and backend |

---

## 7. Installation

### 7.1 Python

Verify Python:

```powershell
python --version
```

Verify pip:

```powershell
pip --version
```

### 7.2 Mosquitto

Install Eclipse Mosquitto for Windows.

Verify:

```powershell
mosquitto -h
```

Also verify:

```powershell
mosquitto_pub -h
mosquitto_sub -h
```

The project expects the broker at:

```text
localhost:1883
```

### 7.3 Python packages

Install:

```powershell
pip install paho-mqtt flask flask-cors
```

The following are from Python's standard library and do not require separate installation:

- `sqlite3`
- `json`
- `time`
- `datetime`
- `random`
- `pathlib`
- `csv`
- `subprocess`

---

## 8. Configuration

The project contains:

```text
config.yaml
```

Example configuration:

```yaml
simulation:
  interval: 1

temperature:
  normal_min: 20
  normal_max: 60
  warning: 55
  critical: 60

pressure:
  normal_min: 950
  normal_max: 1050
  warning: 1040
  critical: 1050

imu:
  acceleration_warning: 12
  acceleration_critical: 15
```

These are simulation values for the PoC. When actual engineering requirements are provided, they should be replaced with approved limits.

---

## 9. How to Run

### Recommended: one-command startup

The project contains:

```text
run_project.py
```

From the project root:

```powershell
cd C:\project
python run_project.py
```

The launcher starts separate terminals for:

- MQTT Subscriber
- Flask Backend
- MQTT Publisher

Mosquitto continues to run as the local MQTT broker/service.

The dashboard is opened at:

```text
http://127.0.0.1:5000/
```

### Manual startup

For debugging, components can also be started separately:

```powershell
python -m mqtt.subscriber
```

```powershell
python -m mqtt.publisher
```

```powershell
python -m backend.app
```

Then open:

```text
http://127.0.0.1:5000/
```

---

## 10. MQTT Communication

The MQTT model is:

```text
             Mosquitto Broker
                    |
          +---------+---------+
          |                   |
          v                   v
     Publisher            Subscriber
```

The publisher and subscriber do not communicate directly. Both communicate through the broker.

Because this project is software-only, SPI/I2C/UART are not used between the simulated sensors and the software. In a future hardware implementation, a physical sensor driver could use SPI/I2C/UART, while MQTT could still carry telemetry to the monitoring system.

---

## 11. MQTT Topics

The main telemetry topic is:

```text
telemetry/all
```

The complete sensor packet is sent as one JSON message.

Example:

```json
{
  "timestamp": "2026-09-30T10:20:15.123456",
  "imu": {
    "accel_x": 0.12,
    "accel_y": -0.05,
    "accel_z": 9.82,
    "gyro_x": 0.01,
    "gyro_y": -0.02,
    "gyro_z": 0.03
  },
  "temperature": 25.4,
  "barometer": {
    "pressure": 1013.2,
    "altitude": -0.8
  }
}
```

---

## 12. Sensor Data Format

### Timestamp

Each packet contains an ISO-formatted timestamp:

```text
timestamp
```

### Temperature

Field:

```text
temperature
```

Unit:

```text
°C
```

### Barometer

Fields:

```text
pressure
altitude
```

Units:

```text
pressure -> hPa
altitude -> m
```

Altitude is derived from the simulated pressure.

### IMU

Accelerometer:

```text
accel_x
accel_y
accel_z
```

Units:

```text
m/s²
```

Gyroscope:

```text
gyro_x
gyro_y
gyro_z
```

Units:

```text
°/s
```

---

## 13. Fault Injection

The fault injector creates abnormal telemetry so the complete monitoring pipeline can be tested without physical hardware.

### High temperature

Example injected value:

```text
temperature = 70°C
```

### High pressure

Example:

```text
pressure = 1200 hPa
```

### High acceleration

Example:

```text
accel_x = 20 m/s²
accel_y = 20 m/s²
accel_z = 20 m/s²
```

### Sensor failure

Temperature failure:

```json
{
  "temperature": null
}
```

Pressure failure:

```json
{
  "barometer": null
}
```

IMU failure:

```json
{
  "imu": null
}
```

### Multiple faults

More than one fault can be active at the same time, for example:

```text
high_temperature + high_pressure
```

The anomaly detector checks each sensor independently.

### Fault timing

Faults are generated at random intervals and remain active for a short duration before clearing. This produces sequences such as:

```text
Normal
   |
   v
High Temperature
   |
   v
Normal
   |
   v
High Pressure + High Temperature
   |
   v
Normal
```

---

## 14. Anomaly Detection

The anomaly detector is separate from the fault injector.

It receives telemetry values and independently decides the condition.

### Temperature rules

```text
<= 55°C       -> NORMAL
> 55°C        -> WARNING
> 60°C        -> CRITICAL
None          -> SENSOR_FAILURE
```

### Pressure rules

```text
<= 1040 hPa   -> NORMAL
> 1040 hPa    -> WARNING
> 1050 hPa    -> CRITICAL
None          -> SENSOR_FAILURE
```

### IMU rules

The detector evaluates the absolute acceleration components and uses the highest component against the thresholds.

```text
<= 12 m/s²    -> NORMAL
> 12 m/s²     -> WARNING
> 15 m/s²     -> CRITICAL
Missing IMU   -> SENSOR_FAILURE
```

### Example

The simulator can produce:

```text
Temperature = 70°C
```

The MQTT pipeline transports it as telemetry.

The detector independently checks:

```text
70°C > 60°C
```

and creates:

```text
temperature = CRITICAL
```

The simulator does not need to send a precomputed `CRITICAL` status.

---

## 15. Database

SQLite database:

```text
database/telemetry.db
```

SQLite is used because it is simple, local, lightweight, and suitable for this proof of concept.

The database contains two main tables:

```text
telemetry
anomaly_events
```

---

## 16. Database Schema

### telemetry table

Stores every telemetry sample.

| Column | Description |
|---|---|
| `id` | Unique row ID |
| `timestamp` | Measurement timestamp |
| `temperature` | Temperature in °C |
| `pressure` | Pressure in hPa |
| `altitude` | Altitude in m |
| `accel_x` | X acceleration |
| `accel_y` | Y acceleration |
| `accel_z` | Z acceleration |
| `gyro_x` | X angular velocity |
| `gyro_y` | Y angular velocity |
| `gyro_z` | Z angular velocity |
| `temperature_status` | Temperature condition |
| `pressure_status` | Pressure condition |
| `imu_status` | IMU condition |

Example:

```text
id | timestamp | temperature | pressure | accel_x | ... | temperature_status | pressure_status | imu_status
1  | ...       | 25.4        | 1013.2   | 0.12    | ... | NORMAL              | NORMAL          | NORMAL
2  | ...       | 70.0        | 1200.0   | 20.0    | ... | CRITICAL            | CRITICAL        | CRITICAL
```

### anomaly_events table

Stores detected abnormal conditions.

| Column | Description |
|---|---|
| `id` | Unique event ID |
| `timestamp` | Event timestamp |
| `sensor` | Affected sensor |
| `status` | Detected condition |

Example:

```text
id | timestamp | sensor       | status
1  | ...       | temperature  | CRITICAL
2  | ...       | pressure     | CRITICAL
3  | ...       | imu          | CRITICAL
```

---

## 17. Database Processing Flow

```text
MQTT Message
     |
     v
JSON Parsing
     |
     v
Anomaly Detector
     |
     +-------------------+
     |                   |
     v                   v
Telemetry Table      Anomaly Events
     |                   |
     +---------+---------+
               |
               v
          SQLite DB
```

Every sample is stored in `telemetry`.

When an abnormal condition is detected, the corresponding sensor event is also inserted into `anomaly_events`.

DB Browser for SQLite can be used to inspect the database during development.

---

## 18. Flask Backend

The Flask backend is the interface between the database and the web dashboard.

```text
Dashboard
    |
    v
Flask REST API
    |
    v
SQLite Database
```

The MQTT subscriber remains responsible for receiving telemetry and saving it to the database. Flask does not replace MQTT as the telemetry ingestion path.

---

## 19. API Endpoints

### Root

```http
GET /
```

Returns backend service information.

### Health

```http
GET /api/health
```

Example response:

```json
{
  "status": "ok"
}
```

### Latest telemetry

```http
GET /api/latest
```

Returns the newest telemetry record.

### Historical telemetry

```http
GET /api/telemetry?limit=40
```

Returns the most recent telemetry rows.

The dashboard uses this endpoint to populate historical graphs.

### Recent anomalies

```http
GET /api/anomalies?limit=25
```

Returns recently detected anomaly events.

### CSV export

```http
GET /api/export
```

Generates and returns the telemetry CSV file.

---

## 20. Dashboard

The dashboard is the engineer-facing visualization layer.

It provides:

### Sensor summary

- Temperature
- Pressure
- IMU
- Current status

### Live sensor values

Temperature:

- Current value
- Minimum
- Maximum
- Average
- Diagnostic status

Pressure:

- Current value
- Minimum
- Maximum
- Average
- Diagnostic status

IMU:

- Accelerometer X/Y/Z
- Gyroscope X/Y/Z
- IMU magnitude
- Diagnostic status

### Historical graphs

The dashboard displays graphs for:

- Temperature
- Pressure
- IMU acceleration X/Y/Z

The graph data comes from the Flask `/api/telemetry` endpoint.

### Recent alerts

The dashboard shows detected anomalies such as:

```text
Temperature -> CRITICAL
Pressure    -> WARNING
IMU         -> CRITICAL
```

### Dashboard data flow

```text
SQLite
   |
   v
Flask REST API
   |
   v
JavaScript
   |
   +----> Live cards
   +----> Historical graphs
   +----> Alerts table
```

The browser does not generate fake sensor values for the final monitoring workflow.

---

## 21. CSV Export

The project supports CSV export from the dashboard.

The export contains telemetry stored in the SQLite database.

Typical fields include:

```text
id
timestamp
temperature
pressure
altitude
accel_x
accel_y
accel_z
gyro_x
gyro_y
gyro_z
temperature_status
pressure_status
imu_status
```

The CSV can be used for:

- Offline analysis
- Test reports
- Spreadsheet analysis
- Data sharing
- Post-test investigation

The database remains the primary storage; the CSV is an on-demand export.

---

## 22. End-to-End Example

### Normal operation

```text
Temperature = 25.4°C
Pressure    = 1013.2 hPa
Accel X     = 0.12 m/s²
```

Flow:

```text
Simulator
   |
   v
MQTT Publisher
   |
   v
Mosquitto
   |
   v
MQTT Subscriber
   |
   v
Anomaly Detector -> NORMAL
   |
   v
SQLite
   |
   v
Flask API
   |
   v
Dashboard
```

### High temperature

```text
Fault Injector
      |
      v
Temperature = 70°C
      |
      v
MQTT
      |
      v
Subscriber
      |
      v
Anomaly Detector
      |
      v
CRITICAL
```

The database then stores the reading with:

```text
temperature = 70
temperature_status = CRITICAL
```

and an event is recorded:

```text
sensor = temperature
status = CRITICAL
```

### Multiple fault

Example:

```text
temperature = 70°C
pressure = 1200 hPa
```

The detector can return:

```json
{
  "temperature": "CRITICAL",
  "pressure": "CRITICAL",
  "imu": "NORMAL"
}
```

---

## 23. Troubleshooting

### Python is not recognized

Run:

```powershell
python --version
```

If Python is installed but not found, add Python to PATH or use the Python launcher if available.

### Mosquitto is not recognized

Check:

```powershell
mosquitto -h
```

Also verify the broker is listening:

```powershell
netstat -ano | findstr :1883
```

### MQTT communication fails

Confirm Mosquitto is running and the application is connecting to:

```text
localhost:1883
```

### Database is empty

Make sure the publisher and subscriber are running:

```powershell
python -m mqtt.subscriber
python -m mqtt.publisher
```

Then inspect:

```text
database/telemetry.db
```

using DB Browser for SQLite.

### Dashboard has no data

Test the backend directly:

```text
http://127.0.0.1:5000/api/health
```

Then:

```text
http://127.0.0.1:5000/api/latest
```

If `/api/latest` returns telemetry, the backend and database are functioning.

### Dashboard graphs are blank

The dashboard uses Chart.js.

Check in the browser developer console:

```javascript
typeof Chart
```

A working Chart.js load should return:

```text
"function"
```

If it returns `"undefined"`, check that Chart.js is present in:

```text
dashboard/static/js/chart.umd.min.js
```

and that `index.html` loads it before `dashboard.js`.

---

## 24. Git and Version Control

Runtime files should normally not be committed to GitHub.

Recommended `.gitignore` entries:

```gitignore
__pycache__/
*.pyc
*.db
*.sqlite
*.sqlite3
*.csv
*.log
.env
venv/
.venv/
```

Typical checkpoint:

```powershell
git status
git add .
git commit -m "Complete remote telemetry monitoring PoC"
git push origin main
```

---

## 25. Current Project Status

```text
Sensor Simulation              ✅
Fault Injection                ✅
MQTT Publisher                 ✅
MQTT Broker                    ✅
MQTT Subscriber                ✅
Anomaly Detection              ✅
SQLite Database                ✅
Flask Backend                  ✅
REST APIs                      ✅
Dashboard                      ✅
Live Telemetry                 ✅
Historical Telemetry           ✅
Anomaly Display                ✅
CSV Export                     ✅
One-command Startup            ✅
```

The main startup command is:

```powershell
python run_project.py
```

---

## 26. Future Enhancements

Possible future improvements include:

- Real hardware sensor integration
- SPI/I2C/UART sensor drivers
- ROS 2 integration
- WebSocket-based telemetry streaming
- Authentication and user management
- Remote MQTT broker
- TLS-secured MQTT
- Advanced anomaly detection
- Configurable fault scenarios from the dashboard
- Fault start/clear lifecycle tracking
- Alert acknowledgement
- Multi-device monitoring
- Long-term database optimization
- Docker-based deployment
- Cloud telemetry storage

---

## 27. Summary

This project demonstrates a complete software-based telemetry monitoring pipeline for a remote environmental test node.

The system starts with virtual sensor data and ends with an engineering dashboard:

```text
Sensors
   |
   v
Fault Simulation
   |
   v
MQTT Communication
   |
   v
Telemetry Processing
   |
   v
Anomaly Detection
   |
   v
Database Storage
   |
   v
REST API
   |
   v
Dashboard
   |
   v
CSV Analysis
```

The PoC demonstrates:

- Embedded/IoT telemetry concepts
- Sensor simulation
- Fault injection
- MQTT publish/subscribe communication
- Diagnostic logic
- Database storage
- Backend API development
- Web-based monitoring
- Historical analysis
- Engineering data export

The intended single-command startup is:

```powershell
python run_project.py
```