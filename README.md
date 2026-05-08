# Sistem Monitoring Meja Billiard Realtime

Simulasi monitoring 5 meja billiard berbasis Docker di Windows. Python mensimulasikan sensor meja, data dikirim lewat MQTT, disimpan ke InfluxDB, lalu divisualisasikan di dashboard Node-RED.

## Arsitektur

```text
Python Simulator -> Mosquitto MQTT -> Node-RED Dashboard
                                 -> MQTT-to-Influx Bridge -> InfluxDB v2
```

## Fitur

- 5 meja billiard realtime
- Status meja `dipakai` / `kosong`
- Durasi pemakaian update tiap 5 detik
- Alarm overtime jika durasi lebih dari 120 menit
- Dashboard Node-RED dengan kartu meja, ringkasan status, panel alarm, dan grafik histori
- Penyimpanan histori ke InfluxDB

## Struktur Folder

```text
billiard-py/
├─ docker-compose.yml
├─ README.md
├─ .gitignore
├─ mosquitto/
│  ├─ config/mosquitto.conf
│  ├─ data/
│  └─ log/
├─ influxdb/
│  ├─ config/
│  └─ data/
├─ node-red/
│  ├─ Dockerfile
│  └─ data/
│     ├─ flows.json
│     └─ package.json
├─ simulator/
│  ├─ Dockerfile
│  ├─ app.py
│  └─ requirements.txt
└─ mqtt-to-influx/
   ├─ Dockerfile
   ├─ app.py
   └─ requirements.txt
```

## Prasyarat

- Windows + Docker Desktop aktif
- Docker Compose v2

Verifikasi:

```powershell
docker --version
docker compose version
```

## Menjalankan Project

Jalankan dari root project:

```powershell
docker compose up -d --build
```

Cek status service:

```powershell
docker compose ps
```

Lihat log:

```powershell
docker compose logs -f
```

## Endpoint

- Dashboard Node-RED: `http://localhost:1880/ui`
- Editor Node-RED: `http://localhost:1880`
- InfluxDB: `http://localhost:8086`
- MQTT broker: `localhost:1883`

## Kredensial InfluxDB

- Username: `admin`
- Password: `admin12345`
- Organization: `billiard-org`
- Bucket: `billiard-monitoring`
- Token: `billiard-super-token-12345`

## Cara Pakai

1. Jalankan stack dengan `docker compose up -d --build`.
2. Buka `http://localhost:1880/ui`.
3. Amati dashboard:
   - kartu hijau: meja kosong
   - kartu kuning: meja sedang dipakai
   - kartu merah: overtime aktif
   - grafik bawah: histori durasi per meja
4. Buka `http://localhost:8086` jika ingin melihat data histori di InfluxDB.
5. Buka `http://localhost:1880` jika ingin mengubah flow atau tampilan dashboard.

Catatan simulasi:

- Data dikirim setiap 5 detik.
- `SIMULATION_MINUTES_PER_TICK=5`, jadi 1 tick simulasi mewakili 5 menit pemakaian.
- Ini sengaja dipercepat agar alarm overtime mudah terlihat saat demo.

## Payload MQTT

Topik:

```text
billiard/table/{id}
```

Contoh payload:

```json
{
  "table_id": 3,
  "table_name": "Meja 3",
  "status": "dipakai",
  "duration_minutes": 125,
  "alarm": true,
  "overtime_minutes": 5,
  "updated_at": "2026-05-08T02:12:57.805215+00:00"
}
```

## Komponen

- `mosquitto`: broker MQTT
- `simulator`: publisher Python untuk simulasi 5 meja
- `mqtt-to-influx`: subscriber MQTT yang menulis data ke InfluxDB
- `influxdb`: database time-series
- `node-red`: dashboard monitoring realtime

## Testing Cepat

### 1. Pastikan semua container hidup

```powershell
docker compose ps
```

Yang harus muncul:

- `billiard-mosquitto`
- `billiard-influxdb`
- `billiard-node-red`
- `billiard-simulator`
- `billiard-mqtt-to-influx`

### 2. Pastikan simulator publish data

```powershell
docker compose logs --tail 20 simulator
```

Harus terlihat log `Published billiard/table/...`

### 3. Pastikan data masuk ke InfluxDB

```powershell
docker exec billiard-influxdb sh -lc 'influx query --org billiard-org --token billiard-super-token-12345 "from(bucket: \"billiard-monitoring\") |> range(start: -10m) |> limit(n: 20)"'
```

### 4. Pastikan bridge menulis ke InfluxDB

```powershell
docker compose logs --tail 20 mqtt-to-influx
```

Harus terlihat `Wrote to InfluxDB from topic ...`

### 5. Pastikan dashboard realtime

Buka:

```text
http://localhost:1880/ui
```

Lalu lakukan hard refresh jika perlu:

```text
Ctrl + F5
```

## Operasional

Stop semua service:

```powershell
docker compose down
```

Start lagi:

```powershell
docker compose up -d --build
```

## Reset Total Data

Jika ingin mengulang dari kondisi benar-benar bersih:

```powershell
docker compose down
Get-ChildItem .\influxdb\data -Force | Remove-Item -Recurse -Force
Get-ChildItem .\influxdb\config -Force | Remove-Item -Recurse -Force
docker volume rm billiard-py_node_red_data
docker compose up -d --build
```

## Troubleshooting

### Dashboard terbuka tapi tidak berubah

- lakukan hard refresh `Ctrl + F5`
- cek `docker compose logs --tail 20 node-red`
- cek `docker compose logs --tail 20 simulator`

### Node-RED hidup tapi dashboard kosong

- pastikan `http://localhost:1880/ui` yang dibuka, bukan editor
- pastikan log menunjukkan `Connected to broker`

### Data tidak masuk ke InfluxDB

- cek log bridge:

```powershell
docker compose logs -f mqtt-to-influx
```

### InfluxDB error karena state lama

- reset folder `influxdb/data` dan `influxdb/config`
- start ulang stack

### Port bentrok

Jika port `1880`, `1883`, atau `8086` sudah dipakai aplikasi lain, ubah port mapping di `docker-compose.yml`.
