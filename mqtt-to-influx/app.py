import json
import os
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision


MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "mosquitto")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "billiard/table/+")

INFLUX_URL = os.getenv("INFLUX_URL", "http://influxdb:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "billiard-super-token-12345")
INFLUX_ORG = os.getenv("INFLUX_ORG", "billiard-org")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "billiard-monitoring")


class MqttToInfluxBridge:
    def __init__(self) -> None:
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="mqtt-to-influx-bridge")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.influx = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
        self.writer = self.influx.write_api()

    def on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        del userdata, flags, properties
        print(f"Connected to MQTT broker with reason_code={reason_code}")
        client.subscribe(MQTT_TOPIC)
        print(f"Subscribed to topic: {MQTT_TOPIC}")

    def on_message(self, client, userdata, msg) -> None:
        del client, userdata
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            updated_at = datetime.fromisoformat(payload["updated_at"])
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)

            point = (
                Point("billiard_usage")
                .tag("table_id", str(payload["table_id"]))
                .tag("table_name", payload["table_name"])
                .tag("status", payload["status"])
                .field("duration_minutes", int(payload["duration_minutes"]))
                .field("in_use", 1 if payload["status"] == "dipakai" else 0)
                .field("alarm", 1 if payload["alarm"] else 0)
                .field("overtime_minutes", int(payload["overtime_minutes"]))
                .time(updated_at, WritePrecision.MS)
            )

            self.writer.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
            print(f"Wrote to InfluxDB from topic {msg.topic}: {payload}")
        except Exception as exc:
            print(f"Failed to process message from {msg.topic}: {exc}")

    def run(self) -> None:
        while True:
            try:
                print(f"Connecting to MQTT broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}...")
                self.client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=60)
                self.client.loop_forever()
            except Exception as exc:
                print(f"Bridge connection failed: {exc}. Retrying in 5 seconds.")
                time.sleep(5)


if __name__ == "__main__":
    MqttToInfluxBridge().run()
