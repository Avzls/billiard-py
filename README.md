# Sistem Monitoring Meja Billiard Realtime

Simulasi monitoring 5 meja billiard berbasis Docker di Windows. Python mensimulasikan sensor meja, data dikirim lewat MQTT, disimpan ke InfluxDB, lalu ditampilkan di dashboard Node-RED.

## Arsitektur

```text
Python Simulator -> Mosquitto MQTT -> Node-RED Dashboard
                                 -> MQTT-to-Influx Bridge -> InfluxDB v2
```

## Fitur

- 5 meja billiard realtime
- Status meja `dipakai` / `kosong`
- Durasi pemakaian update otomatis
- Alarm overtime jika durasi lebih dari 120 menit
- Dashboard monitoring di Node-RED
- Histori data tersimpan di InfluxDB

## 1. Prasyarat

Pastikan di PC sudah ada:

- Windows
- Docker Desktop aktif
- Git

Cek versi:

```powershell
docker --version
docker compose version
git --version
```

## 2. Clone Project

Clone repository:

```powershell
git clone https://github.com/Avzls/billiard-py.git
```

Masuk ke folder project:

```powershell
cd billiard-py
```

## 3. Struktur Project

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

## 4. Jalankan Semua Service

Jalankan dari root project:

```powershell
docker compose up -d --build
```

Cek apakah semua container hidup:

```powershell
docker compose ps
```

Yang normal muncul:

- `billiard-mosquitto`
- `billiard-influxdb`
- `billiard-node-red`
- `billiard-simulator`
- `billiard-mqtt-to-influx`

Kalau ada container lama nyangkut:

```powershell
docker compose down --remove-orphans
docker compose up -d --build
```

## 5. Endpoint yang Dipakai

Setelah semua service jalan, buka:

- Dashboard monitoring: `http://localhost:1880/ui`
- Editor Node-RED: `http://localhost:1880`
- InfluxDB: `http://localhost:8086`

## 6. Login InfluxDB

Kalau buka InfluxDB, pakai:

- Username: `admin`
- Password: `admin12345`
- Organization: `billiard-org`
- Bucket: `billiard-monitoring`
- Token: `billiard-super-token-12345`

## 7. Cara Kerja Sistem

Alur data:

1. `simulator` membuat data palsu 5 meja billiard
2. data dikirim ke broker MQTT `mosquitto`
3. `node-red` membaca data MQTT untuk dashboard realtime
4. `mqtt-to-influx` membaca data MQTT yang sama lalu menyimpannya ke InfluxDB

## 8. Cara Monitoring dari UI

Buka:

```text
http://localhost:1880/ui
```

Di dashboard akan terlihat:

- kartu status 5 meja
- warna hijau untuk meja `kosong`
- warna kuning untuk meja `dipakai`
- warna merah untuk `overtime`
- durasi pemakaian realtime
- grafik perubahan durasi
- panel alarm overtime

Kalau dashboard belum update, lakukan hard refresh:

```text
Ctrl + F5
```

## 9. Ini Simulasi, Bukan Sensor Asli

Data yang tampil adalah simulasi software, bukan dari hardware meja billiard asli.

Artinya:

- status meja bisa berubah otomatis
- durasi bisa naik lalu reset ke `0`
- perubahan itu normal karena dibuat oleh program simulator

## 10. Setting Interval Simulasi

Kalau mau ubah interval kirim data, edit file:

- `docker-compose.yml`

Cari bagian:

```yml
PUBLISH_INTERVAL_SECONDS: 5
SIMULATION_MINUTES_PER_TICK: 5
```

Penjelasan:

- `PUBLISH_INTERVAL_SECONDS`: kirim data tiap berapa detik nyata
- `SIMULATION_MINUTES_PER_TICK`: tiap 1 kali kirim mewakili berapa menit simulasi

Contoh:

```yml
PUBLISH_INTERVAL_SECONDS: 10
SIMULATION_MINUTES_PER_TICK: 5
```

Setelah diubah, jalankan:

```powershell
docker compose up -d --build simulator
```

## 11. Testing Cepat

### Cek log simulator

```powershell
docker compose logs --tail 20 simulator
```

Harus terlihat:

```text
Published billiard/table/...
```

### Cek log bridge ke InfluxDB

```powershell
docker compose logs --tail 20 mqtt-to-influx
```

Harus terlihat:

```text
Wrote to InfluxDB from topic ...
```

### Cek log Node-RED

```powershell
docker compose logs --tail 20 node-red
```

### Cek data masuk ke InfluxDB

```powershell
docker exec billiard-influxdb sh -lc 'influx query --org billiard-org --token billiard-super-token-12345 "from(bucket: \"billiard-monitoring\") |> range(start: -10m) |> limit(n: 20)"'
```

## 12. Stop Project

Untuk menghentikan semua service:

```powershell
docker compose down
```

## 13. Reset Total

Kalau ingin mulai ulang dari kondisi bersih:

```powershell
docker compose down
Get-ChildItem .\influxdb\data -Force | Remove-Item -Recurse -Force
Get-ChildItem .\influxdb\config -Force | Remove-Item -Recurse -Force
docker volume rm billiard-py_node_red_data
docker compose up -d --build
```

## 14. Troubleshooting

### Dashboard terbuka tapi tidak berubah

- lakukan `Ctrl + F5`
- cek `docker compose logs --tail 20 simulator`
- cek `docker compose logs --tail 20 node-red`

### Container dobel

Kalau ada container service yang dobel:

```powershell
docker compose down --remove-orphans
docker compose up -d --build
```

### Port bentrok

Kalau port `1880`, `1883`, atau `8086` dipakai aplikasi lain, ubah port mapping di `docker-compose.yml`.

### Data InfluxDB error karena state lama

Lakukan reset total sesuai langkah di atas.
