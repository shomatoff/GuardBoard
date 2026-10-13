"""Local-only GuardBoard foundation server."""
from __future__ import annotations

import argparse
import asyncio
import hmac
import os
import secrets
import tomllib
from pathlib import Path

from backend.collectors.system import collect
from backend.collectors.capabilities import collect as collect_capabilities, TOOLS
from backend.storage.history import HistoryStore
from backend.security.posture import check as check_posture
from backend.collectors.processes import ProcessSampler
from backend.collectors.network import NetworkSampler, snapshot as network_snapshot
from backend.collectors.external import public_ip, download_sample, tcp_latency_sample
from backend.collectors.wifi import WifiScanner, adapter as wifi_adapter
from backend.storage.wifi_rooms import RoomStore
from backend.collectors.local_devices import passive_inventory, MAC
from backend.storage.devices import DeviceStore
from backend.security.integrity import IntegrityStore, validate_project
from backend.actions.av_scan import ScanManager
from backend.security.firewall import collect as collect_firewall
from backend.security.hardening import collect as collect_hardening
from backend.security.secrets import scan as scan_secrets
from backend.collectors.privacy import collect as collect_privacy
from backend.collectors.optimizer import collect as collect_optimizer
from backend.storage.alerts import AlertStore
from backend.storage.config import ConfigStore, DEFAULT_THRESHOLDS, validate_thresholds
import sqlite3
import psutil
import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
ALLOWED_HOSTS = {"127.0.0.1", "localhost"}
PORT = int(os.environ.get("GUARDBOARD_PORT", "8765"))
if not 1024 <= PORT <= 65535:
    raise ValueError("GUARDBOARD_PORT must be between 1024 and 65535")
ALLOWED_ORIGINS = {f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"}
TOKEN = secrets.token_urlsafe(32)
CSRF = secrets.token_urlsafe(32)


class ProjectInput(BaseModel):
    path: str
    confirmed: bool

    @field_validator('path')
    @classmethod
    def validate_path_length(cls, value: str) -> str:
        if not 1 <= len(value) <= 4096 or any(ord(char) < 32 for char in value):
            raise ValueError('Invalid project path')
        return value


class AlertThresholdInput(BaseModel):
    thresholds: dict[str, float]
    confirmed: bool


class TrustDeviceInput(BaseModel):
    mac: str
    trusted: bool

    @field_validator('mac')
    @classmethod
    def validate_mac(cls, value: str) -> str:
        if not MAC.fullmatch(value):
            raise ValueError('Invalid MAC address')
        return value.lower()


class OwnershipConfirmation(BaseModel):
    confirmed_ownership: bool


class RoomInput(BaseModel):
    room: str

    @field_validator('room')
    @classmethod
    def validate_room(cls, value: str) -> str:
        cleaned = value.strip()
        if not 1 <= len(cleaned) <= 80 or any(ord(char) < 32 for char in cleaned):
            raise ValueError('Room name must be 1-80 printable characters')
        return cleaned


def create_app(demo: bool = False, history_path: Path | None = None, room_path: Path | None = None, device_path: Path | None = None, integrity_path: Path | None = None, allowed_project_root: Path | None = None) -> FastAPI:
    app = FastAPI(title="GuardBoard", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.demo = demo
    app.state.history = None if demo else HistoryStore(history_path or ROOT / ".local" / "history-real.sqlite")
    app.state.processes = ProcessSampler()
    app.state.network = NetworkSampler()
    app.state.wifi = WifiScanner()
    app.state.rooms = None if demo else RoomStore(room_path or ROOT / ".local" / "wifi-rooms.sqlite")
    app.state.devices = None if demo else DeviceStore(device_path or ROOT / ".local" / "devices.sqlite")
    app.state.integrity = None if demo else IntegrityStore(integrity_path or ROOT / ".local" / "integrity.sqlite")
    app.state.av = ScanManager()
    app.state.project_root = allowed_project_root or Path.home()
    app.state.config = None if demo else ConfigStore((history_path or ROOT / ".local" / "history-real.sqlite").with_name('config.toml'))
    app.state.config_error = None
    try:
        thresholds = DEFAULT_THRESHOLDS if demo else app.state.config.read()
    except (OSError, ValueError, tomllib.TOMLDecodeError):
        thresholds = DEFAULT_THRESHOLDS
        app.state.config_error = 'config_invalid'
    app.state.alerts = None if demo else AlertStore((history_path or ROOT / ".local" / "history-real.sqlite").with_name('alerts.sqlite'), thresholds)

    @app.middleware("http")
    async def guard(request: Request, call_next):
        host = request.headers.get("host", "").split(":", 1)[0].lower()
        if host not in ALLOWED_HOSTS:
            return JSONResponse({"error": "Invalid host"}, status_code=403)
        origin = request.headers.get("origin")
        if origin and origin not in ALLOWED_ORIGINS:
            return JSONResponse({"error": "Invalid origin"}, status_code=403)
        if request.url.path.startswith("/api/"):
            if not hmac.compare_digest(request.cookies.get("gb_session", ""), TOKEN):
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
            if request.method not in {"GET", "HEAD"} and not hmac.compare_digest(request.headers.get("x-csrf-token", ""), CSRF):
                return JSONResponse({"error": "CSRF"}, status_code=403)
        return await call_next(request)

    @app.get("/")
    async def index(request: Request):
        key = request.query_params.get("key", "")
        authenticated = hmac.compare_digest(request.cookies.get("gb_session", ""), TOKEN)
        if key and hmac.compare_digest(key, TOKEN):
            response = RedirectResponse("/", status_code=303)
            response.set_cookie("gb_session", TOKEN, httponly=True, samesite="strict", secure=False)
            return response
        if not authenticated:
            raise HTTPException(status_code=401, detail="Launch GuardBoard using the local URL printed by run.sh")
        return FileResponse(FRONTEND / "index.html")

    @app.get("/api/bootstrap")
    async def bootstrap():
        return {"demo": demo, "csrf": CSRF}

    @app.get("/api/capabilities")
    async def capabilities():
        if demo:
            return {'mode': 'demo', 'tools': {name: {'available': name in {'clamav', 'wifi', 'firewall_ufw'},
                                                  'package_state': 'demo_sample', 'binary': binary}
                                              for name, (binary, _) in TOOLS.items()}}
        return {"mode": "real", "tools": collect_capabilities()}

    @app.get("/api/security/firewall")
    async def firewall():
        return {"mode": "demo" if demo else "real", "data": None if demo else await asyncio.to_thread(collect_firewall)}

    @app.get('/api/security/hardening')
    async def hardening():
        return {'mode': 'demo' if demo else 'real', 'data': None if demo else await asyncio.to_thread(collect_hardening)}

    @app.get("/api/privacy")
    async def privacy():
        return {"mode": "demo" if demo else "real", "data": None if demo else await asyncio.to_thread(collect_privacy)}

    @app.get('/api/optimizer')
    async def optimizer():
        return {'mode': 'demo' if demo else 'real', 'data': None if demo else await asyncio.to_thread(collect_optimizer)}

    @app.get("/api/telemetry")
    async def telemetry():
        if demo:
            return {"mode": "demo", "cpu": 18.5, "memory": 42.0, "disk": 63.0, "source": "deterministic demo"}
        try:
            readings = collect()
            app.state.history.record(readings)
            try:
                app.state.alerts.observe(readings)
            except (OSError, sqlite3.Error):
                pass  # An alert storage failure must not erase live telemetry.
            return {"mode": "real", "cpu": readings["cpu"]["value"], "memory": readings["memory"]["value"], "disk": readings["disk"]["value"], "readings": readings, "source": "system collectors"}
        except (OSError, RuntimeError) as exc:
            return {"mode": "real", "cpu": None, "memory": None, "disk": None, "error": type(exc).__name__}

    @app.get('/api/alerts')
    async def alerts():
        return {'mode': 'demo' if demo else 'real', 'events': [] if demo else app.state.alerts.recent()}

    @app.get('/api/settings')
    async def settings():
        return {'mode': 'demo' if demo else 'real', 'alert_thresholds': app.state.alerts.thresholds if not demo else DEFAULT_THRESHOLDS,
                'error': app.state.config_error}

    @app.post('/api/settings/alerts')
    async def update_alert_settings(payload: AlertThresholdInput):
        if demo:
            raise HTTPException(status_code=409, detail='Unavailable in demo mode')
        if not payload.confirmed:
            raise HTTPException(status_code=403, detail='Explicit confirmation required')
        try:
            values = validate_thresholds(payload.thresholds)
            app.state.config.write(values)
            app.state.alerts.set_thresholds(values)
            app.state.config_error = None
        except (ValueError, OSError) as exc:
            raise HTTPException(status_code=422, detail=type(exc).__name__) from exc
        return {'alert_thresholds': values}

    @app.post("/api/wifi/devices/trust")
    async def wifi_trust_device(payload: TrustDeviceInput):
        if demo:
            raise HTTPException(status_code=409, detail="Unavailable in demo mode")
        if not app.state.devices.set_trusted(payload.mac, payload.trusted):
            raise HTTPException(status_code=404, detail="Device not observed")
        return {"mac": payload.mac, "trusted": payload.trusted}

    @app.post("/api/wifi/devices")
    async def wifi_devices(payload: OwnershipConfirmation):
        if not payload.confirmed_ownership:
            raise HTTPException(status_code=403, detail="Network ownership confirmation required")
        if demo:
            return {"mode": "demo", "data": None}
        try:
            data = await asyncio.to_thread(passive_inventory)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        data["devices"] = app.state.devices.observe(data["devices"])
        return {"mode": "real", "data": data}

    def prepare_project(payload: ProjectInput) -> Path:
        if demo:
            raise HTTPException(status_code=409, detail="Unavailable in demo mode")
        if not payload.confirmed:
            raise HTTPException(status_code=403, detail="Explicit confirmation required")
        try:
            project = validate_project(payload.path, app.state.project_root)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        battery = psutil.sensors_battery()
        if battery and not battery.power_plugged:
            raise HTTPException(status_code=409, detail="Connect external power before a project scan")
        if psutil.cpu_percent(interval=0.1) > 80:
            raise HTTPException(status_code=409, detail="CPU load too high for a project scan")
        return project

    @app.post("/api/projects/baseline")
    async def project_baseline(payload: ProjectInput):
        project = prepare_project(payload)
        try:
            count = await asyncio.to_thread(app.state.integrity.baseline, project)
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=type(exc).__name__) from exc
        return {"project": str(project), "files": count}

    @app.post("/api/projects/check")
    async def project_check(payload: ProjectInput):
        project = prepare_project(payload)
        try:
            result = await asyncio.to_thread(app.state.integrity.compare, project)
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=type(exc).__name__) from exc
        return {"project": str(project), "result": result}

    @app.post("/api/projects/secrets")
    async def project_secrets(payload: ProjectInput):
        project = prepare_project(payload)
        try:
            result = await asyncio.to_thread(scan_secrets, project)
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=type(exc).__name__) from exc
        return {"project": str(project), "result": result}

    @app.post("/api/av/scans")
    async def av_scan_start(payload: ProjectInput):
        project = prepare_project(payload)
        try:
            job = await app.state.av.start(project)
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)[:120]) from exc
        return job.public()

    @app.get("/api/av/scans/{job_id}")
    async def av_scan_status(job_id: str):
        job = app.state.av.jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Scan not found")
        return job.public()

    @app.post("/api/av/scans/{job_id}/cancel")
    async def av_scan_cancel(job_id: str):
        try:
            job = await app.state.av.cancel(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Scan not found") from exc
        return job.public()

    @app.get("/api/wifi/rooms")
    async def wifi_rooms():
        return {"mode": "demo" if demo else "real", "samples": [] if demo else app.state.rooms.list()}

    @app.post("/api/wifi/rooms")
    async def wifi_room_sample(payload: RoomInput):
        if demo:
            raise HTTPException(status_code=409, detail="Walk-test unavailable in demo mode")
        current = await asyncio.to_thread(wifi_adapter)
        if not current or current['rssi_dbm'] is None:
            raise HTTPException(status_code=422, detail="Current Wi-Fi signal unavailable")
        app.state.rooms.add(payload.room, current['rssi_dbm'])
        return {"samples": app.state.rooms.list()}

    @app.get("/api/wifi")
    async def wifi():
        return {"mode": "demo" if demo else "real", "data": None if demo else await asyncio.to_thread(app.state.wifi.cached)}

    @app.post("/api/wifi/scan")
    async def wifi_scan():
        if demo:
            return {"mode": "demo", "data": None}
        try:
            data = await asyncio.to_thread(app.state.wifi.scan)
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=429 if isinstance(exc, ValueError) else 502, detail=str(exc)[:100]) from exc
        return {"mode": "real", "data": data}

    @app.post("/api/network/latency-sample")
    async def check_latency():
        if demo:
            return {"mode": "demo", "result": None}
        return {"mode": "real", "result": await asyncio.to_thread(tcp_latency_sample)}

    @app.post("/api/network/download-sample")
    async def check_download():
        if demo:
            return {"mode": "demo", "result": None}
        try:
            result = await asyncio.to_thread(download_sample)
        except (OSError, ValueError, TimeoutError) as exc:
            raise HTTPException(status_code=502, detail=type(exc).__name__) from exc
        return {"mode": "real", "result": result}

    @app.post("/api/network/public-ip")
    async def check_public_ip():
        if demo:
            return {"mode": "demo", "ip": None}
        try:
            ip = await asyncio.to_thread(public_ip)
        except (OSError, ValueError, KeyError, TimeoutError) as exc:
            raise HTTPException(status_code=502, detail=type(exc).__name__) from exc
        return {"mode": "real", "ip": ip}

    @app.get("/api/network")
    async def network():
        return {"mode": "demo" if demo else "real", "data": None if demo else network_snapshot(app.state.network)}

    @app.get("/api/processes")
    async def processes():
        return {"mode": "demo" if demo else "real", "data": {"top_cpu": [], "top_memory": [], "top_disk": [], "process_count": 0} if demo else app.state.processes.sample()}

    @app.get("/api/posture")
    async def posture():
        return {"mode": "demo" if demo else "real", "posture": check_posture() if not demo else {"score": None, "status": "insufficient_evidence", "categories": {}}}

    @app.get("/api/history")
    async def history(window: str = "1h"):
        if window not in {"1h", "24h"}:
            raise HTTPException(status_code=422, detail="Unsupported window")
        if demo:
            return {"mode": "demo", "window": window, "samples": []}
        return {"mode": "real", "window": window, "samples": app.state.history.query(3600 if window == "1h" else 86400)}

    @app.websocket("/ws")
    async def websocket(ws: WebSocket):
        host = ws.headers.get("host", "").split(":", 1)[0].lower()
        origin = ws.headers.get("origin")
        if host not in ALLOWED_HOSTS or origin not in ALLOWED_ORIGINS or not hmac.compare_digest(ws.cookies.get("gb_session", ""), TOKEN):
            await ws.close(code=1008)
            return
        await ws.accept()
        try:
            await ws.send_json({"mode": "demo" if demo else "real", "status": "connected"})
            while True:
                await ws.receive_text()
        except WebSocketDisconnect:
            pass

    app.mount("/assets", StaticFiles(directory=FRONTEND), name="assets")
    return app


app = create_app() if __name__ != "__main__" else None

if __name__ == "__main__":
    if os.geteuid() == 0:
        raise SystemExit('GuardBoard must run as a normal user, never root.')
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    print(f"GuardBoard local URL: http://127.0.0.1:{PORT}/?key={TOKEN}", flush=True)
    uvicorn.run(create_app(args.demo), host="127.0.0.1", port=PORT, log_level="warning")
