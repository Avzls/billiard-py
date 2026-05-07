import json
import os
import random
import signal
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "billiard/table")
TABLE_COUNT = int(os.getenv("TABLE_COUNT", "5"))
PUBLISH_INTERVAL_SECONDS = int(os.getenv("PUBLISH_INTERVAL_SECONDS", "5"))
SIMULATION_MINUTES_PER_TICK = int(os.getenv("SIMULATION_MINUTES_PER_TICK", "5"))
RANDOM_SEED = int(os.getenv("RANDOM_SEED", "42"))
OVERTIME_LIMIT_MINUTES = 120

random.seed(RANDOM_SEED)
running = True


@dataclass
class TableState:
    table_id: int
    table_name: str
    status: str
    duration_minutes: int
    alarm: bool
    overtime_minutes: int
    updated_at: str


class BilliardSimulator:
    def __init__(self) -> None:
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="billiard-simulator")
        self.tables = self._create_initial_tables()

    def _create_initial_tables(self) -> dict[int, TableState]:
        tables: dict[int, TableState] = {}
        for table_id in range(1, TABLE_COUNT + 1):
            initial_status = random.choice(["dipakai", "kosong"])
            initial_duration = random.randint(0, 90) if initial_status == "dipakai" else 0
            tables[table_id] = self._build_state(table_id, initial_status, initial_duration)
        return tables

    def _build_state(self, table_id: int, status: str, duration_minutes: int) -> TableState:
        overtime_minutes = max(duration_minutes - OVERTIME_LIMIT_MINUTES, 0)
        return TableState(
            table_id=table_id,
            table_name=f"Meja {table_id}",
            status=status,
            duration_minutes=duration_minutes,
            alarm=overtime_minutes > 0,
            overtime_minutes=overtime_minutes,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

    def connect(self) -> None:
        while running:
            try:
                print(f"Connecting to MQTT broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}...")
                self.client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=60)
                self.client.loop_start()
                print("Connected to MQTT broker.")
                return
            except OSError as exc:
                print(f"MQTT broker not ready yet: {exc}. Retrying in 5 seconds.")
                time.sleep(5)

    def simulate_tick(self) -> None:
        for table_id, table in self.tables.items():
            status = table.status
            duration = table.duration_minutes

            if status == "kosong":
                if random.random() < 0.30:
                    status = "dipakai"
                    duration = random.randint(0, 20)
            else:
                if random.random() < 0.18:
                    status = "kosong"
                    duration = 0
                else:
                    duration += SIMULATION_MINUTES_PER_TICK

            self.tables[table_id] = self._build_state(table_id, status, duration)

    def publish_all(self) -> None:
        for table in self.tables.values():
            topic = f"{MQTT_TOPIC_PREFIX}/{table.table_id}"
            payload = json.dumps(asdict(table))
            result = self.client.publish(topic, payload=payload, qos=0, retain=False)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"Published {topic}: {payload}")
            else:
                print(f"Failed to publish to {topic}: rc={result.rc}")

    def run(self) -> None:
        self.connect()
        while running:
            self.simulate_tick()
            self.publish_all()
            time.sleep(PUBLISH_INTERVAL_SECONDS)
        self.client.loop_stop()
        self.client.disconnect()


def stop_handler(signum, frame) -> None:
    del signum, frame
    global running
    running = False
    print("Stopping simulator...")


signal.signal(signal.SIGINT, stop_handler)
signal.signal(signal.SIGTERM, stop_handler)


if __name__ == "__main__":
    try:
        BilliardSimulator().run()
    except KeyboardInterrupt:
        stop_handler(None, None)
        sys.exit(0)

