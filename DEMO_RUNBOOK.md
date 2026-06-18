# Smart Transit Security System - Demo Runbook

## Project Architecture

```text
Webcam
   ↓
Detection Service (YOLO + Tracking + Zones)
   ↓
Analytics Service (Loitering, Crowd, Restricted Zone, Theft)
   ↓
Backend API (FastAPI)
   ↓
PostgreSQL Database
   ↓
Dashboard / API Queries
```

---

# Startup Procedure (After Laptop Restart)

## 1. Start PostgreSQL

Verify PostgreSQL service is running.

PowerShell:

```powershell
Get-Service postgresql*
```

Expected:

```text
Status : Running
```

If not running:

```powershell
Start-Service postgresql-x64-18
```

---

## 2. Open Project Directory

```powershell
cd C:\Users\Shashank\Projects\SECURITY-TRANSIT-SYSTEM
```

Activate environment:

```powershell
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& .\venv311\Scripts\Activate.ps1)
```

---

## 3. Start Backend

Terminal 1:

```powershell
uvicorn backend.app:app --host 0.0.0.0 --port 8001
```

Verify:

```powershell
curl.exe http://localhost:8001/health
```

Expected:

```json
{
  "status":"ok"
}
```

Leave this terminal running.

---

## 4. Start Analytics Service

Terminal 2:

```powershell
python analytics/main.py
```

Expected:

```text
Application startup complete
Uvicorn running on http://0.0.0.0:8002
```

Leave this terminal running.

---

## 5. Start Detection Service

Terminal 3:

```powershell
python detection/main.py
```

Expected:

* Webcam window opens
* Zone overlays visible
* Person detection visible
* Tracking IDs visible

Leave running.

---

# Verification Checklist

## Backend

```powershell
curl.exe http://localhost:8001/health
```

Must return HTTP 200.

---

## Analytics

Verify terminal shows no startup errors.

Expected:

```text
Application startup complete
```

---

## Detection

Verify:

* Webcam opens
* Bounding box around person
* Tracking ID visible

Example:

```text
ID 1 person
```

---

# Demo Flow

## Demo 1 - Person Detection

Stand in camera view.

Show:

* Bounding box
* Tracking ID
* Live detection

---

## Demo 2 - Loitering Alert

Stand in same area for:

```text
15+ seconds
```

Expected:

```text
alert_type = loitering
```

Verify:

```powershell
curl.exe http://localhost:8001/api/v1/alerts
```

---

## Demo 3 - Database Proof

Open PostgreSQL:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d smart_transit
```

Check:

```sql
SELECT COUNT(*) FROM alerts;
```

Check:

```sql
SELECT COUNT(*) FROM analytics_results;
```

---

## Demo 4 - API Proof

```powershell
curl.exe http://localhost:8001/api/v1/alerts
```

Show generated alert JSON.

---

# Shutdown Procedure

Stop Detection:

```text
Ctrl+C
```

Stop Analytics:

```text
Ctrl+C
```

Stop Backend:

```text
Ctrl+C
```

PostgreSQL may remain running.

---

# Known Working Features

✓ YOLO Person Detection

✓ Object Tracking

✓ Zone Assignment

✓ Event Storage

✓ Loitering Detection

✓ Analytics Result Storage

✓ Alert Storage

✓ REST API Retrieval

---

# Demo Success Criteria

1. Person detected
2. Object tracked
3. Loitering alert generated
4. Alert stored in PostgreSQL
5. Alert retrievable through API
6. End-to-end pipeline demonstrated
