# Sistem Monitoring Meja Billiard Realtime

Project ini mensimulasikan 5 meja billiard yang mengirim data realtime ke MQTT, menyimpan data ke InfluxDB, dan menampilkan dashboard di Node-RED.

## Arsitektur

```text
Python Simulator -> MQTT Mosquitto -> Node-RED -> InfluxDB
                                     -> Dashboard
```

## Komponen

- `mosquitto`: broker MQTT
- `influxdb`: database time-series InfluxDB v2
- `node-red`: dashboard monitoring dan flow integrasi
- `simulator`: publisher Python yang mensimulasikan sensor 5 meja

## Struktur Folder

```text
tresno/
├─ docker-compose.yml
├─ .env.example
├─ README.md
├─ mosquitto/
│  ├─ config/mosquitto.conf
│  ├─ data/
│  └─ log/
├─ influxdb/
│  ├─ data/
│  └─ config/
├─ node-red/
│  └─ data/
│     ├─ flows.json
│     └─ package.json
└─ simulator/
   ├─ Dockerfile
   ├─ app.py
   └─ requirements.txt
```

## Prasyarat

- Windows dengan Docker Desktop aktif
- Docker Compose V2

Verifikasi:

```powershell
docker --version
docker compose version
```

## Menjalankan Semua Service

Jalankan dari root project:

```powershell
docker compose up -d --build
```

Cek status container:

```powershell
docker compose ps
```

Lihat log realtime:

```powershell
docker compose logs -f
```

## Endpoint

- Node-RED: `http://localhost:1880`
- InfluxDB: `http://localhost:8086`
- MQTT: `localhost:1883`

## Kredensial InfluxDB

- Username: `admin`
- Password: `admin12345`
- Organization: `billiard-org`
- Bucket: `billiard-monitoring`
- Token: `billiard-super-token-12345`

## Detail Simulator

Simulator mengelola 5 meja:

- Status: `dipakai` atau `kosong`
- Durasi: bertambah otomatis saat status `dipakai`
- Alarm: aktif jika `duration_minutes > 120`
- Publish: setiap 5 detik ke topik `billiard/table/{id}`

Payload JSON contoh:

```json
{
  "table_id": 3,
  "table_name": "Meja 3",
  "status": "dipakai",
  "duration_minutes": 125,
  "alarm": true,
  "overtime_minutes": 5,
  "updated_at": "2026-05-07T14:53:10.581553+00:00"
}
```

Catatan simulasi:

- `SIMULATION_MINUTES_PER_TICK=5` artinya setiap 1 publish mewakili 5 menit pemakaian simulasi.
- Nilai ini sengaja dipercepat supaya alarm overtime bisa terlihat saat demo.

## Node-RED

Flow sudah disiapkan di:

- [node-red/data/flows.json](node-red/data/flows.json)

Saat container Node-RED menyala, flow akan otomatis dimuat karena `FLOWS=flows.json`.

Dependency Node-RED yang diinstall otomatis:

- `node-red-dashboard`
- `node-red-contrib-influxdb`

Dashboard menampilkan:

- Kartu status 5 meja
- Durasi pemakaian realtime
- Alarm visual saat overtime
- Grafik durasi pemakaian realtime per meja

## Testing End-to-End

### 1. Pastikan container hidup

```powershell
docker compose ps
```

Yang harus terlihat: `mosquitto`, `influxdb`, `node-red`, `simulator`.

### 2. Pastikan simulator publish ke MQTT

```powershell
docker compose logs simulator
```

Harus terlihat log `Published billiard/table/...`

### 3. Pastikan Node-RED menerima data

```powershell
docker compose logs node-red
```

Jika flow termuat normal, tidak ada error `unknown node type`.

### 4. Pastikan data masuk ke InfluxDB

Buka `http://localhost:8086`, login, lalu buka bucket `billiard-monitoring`.

Atau jalankan query dari container:

```powershell
docker exec billiard-influxdb influx query "from(bucket: \"billiard-monitoring\") |> range(start: -15m)" --token billiard-super-token-12345 --org billiard-org
```

### 5. Pastikan dashboard tampil

Buka `http://localhost:1880/ui`

Yang harus muncul:

- 5 kartu meja
- Status berubah-ubah
- Durasi terus update
- Warna alarm merah berkedip jika overtime
- Grafik garis durasi pemakaian

## Error Umum

### `docker: command not found`

Docker Desktop belum terinstall atau CLI belum masuk `PATH`.

### Port bentrok

Jika `1880`, `1883`, atau `8086` sudah dipakai aplikasi lain, ubah mapping port di `docker-compose.yml`.

### Node-RED tidak memuat dashboard

Tunggu 1-2 menit saat startup pertama karena Node-RED perlu menginstall dependency dari `package.json`.

Cek:

```powershell
docker compose logs -f node-red
```

### InfluxDB tidak menyimpan data

Pastikan token, org, dan bucket di flow sama dengan environment InfluxDB.

### Simulator gagal connect ke MQTT

Pastikan service `mosquitto` statusnya `Up`.

### InfluxDB setup error karena volume lama

Jika sebelumnya pernah menjalankan stack dengan state lama:

```powershell
docker compose down -v
docker compose up -d --build
```

## Menjalankan Simulator Lokal Tanpa Docker

Opsional, untuk debug cepat:

```powershell
cd simulator
python -m pip install -r requirements.txt
python app.py
```
