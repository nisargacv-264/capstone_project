import sqlite3
from pathlib import Path


class Database:

    def __init__(self):
        # database folder
        database_dir = Path(__file__).resolve().parent

        # database file
        self.db_path = database_dir / "telemetry.db"

        # open connection
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)

        # create tables
        self.create_tables()

    def create_tables(self):

        cursor = self.connection.cursor()

        # -----------------------------------------
        # Telemetry table
        # -----------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,

                temperature REAL,
                pressure REAL,
                altitude REAL,

                accel_x REAL,
                accel_y REAL,
                accel_z REAL,

                gyro_x REAL,
                gyro_y REAL,
                gyro_z REAL,

                temperature_status TEXT,
                pressure_status TEXT,
                imu_status TEXT
            )
        """)

        # -----------------------------------------
        # Anomaly events table
        # -----------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomaly_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                sensor TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)

        self.connection.commit()

    def insert_telemetry(self, data, status):

        cursor = self.connection.cursor()

        imu = data.get("imu")
        barometer = data.get("barometer")

        # IMU values
        if imu is not None:
            accel_x = imu.get("accel_x")
            accel_y = imu.get("accel_y")
            accel_z = imu.get("accel_z")

            gyro_x = imu.get("gyro_x")
            gyro_y = imu.get("gyro_y")
            gyro_z = imu.get("gyro_z")

        else:
            accel_x = None
            accel_y = None
            accel_z = None

            gyro_x = None
            gyro_y = None
            gyro_z = None

        # Barometer values
        if barometer is not None:
            pressure = barometer.get("pressure")
            altitude = barometer.get("altitude")

        else:
            pressure = None
            altitude = None

        cursor.execute("""
            INSERT INTO telemetry (
                timestamp,
                temperature,
                pressure,
                altitude,
                accel_x,
                accel_y,
                accel_z,
                gyro_x,
                gyro_y,
                gyro_z,
                temperature_status,
                pressure_status,
                imu_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("timestamp"),
            data.get("temperature"),

            pressure,
            altitude,

            accel_x,
            accel_y,
            accel_z,

            gyro_x,
            gyro_y,
            gyro_z,

            status.get("temperature"),
            status.get("pressure"),
            status.get("imu")
        ))

        self.connection.commit()

    def insert_anomaly_events(self, timestamp, status):

        cursor = self.connection.cursor()

        for sensor, sensor_status in status.items():

            if sensor_status != "NORMAL":

                cursor.execute("""
                    INSERT INTO anomaly_events (
                        timestamp,
                        sensor,
                        status
                    )
                    VALUES (?, ?, ?)
                """, (
                    timestamp,
                    sensor,
                    sensor_status
                ))

        self.connection.commit()

    def close(self):
        self.connection.close()