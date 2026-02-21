"""Enterprise observability API routes — domain-specific endpoints."""
from fastapi import APIRouter
from metrics_engine.engine import metrics_engine
from utils.db import list_all_databases, get_active_database, set_active_database

router = APIRouter()


@router.get("/server/health")
async def server_health():
    cpu = metrics_engine.get_current("cpu")
    memory = metrics_engine.get_current("memory")
    sessions = metrics_engine.get_current("sessions")
    return {
        "status": "ok" if cpu else "initializing",
        "cpu": cpu.model_dump() if cpu else None,
        "memory": memory.model_dump() if memory else None,
        "sessions": sessions.model_dump() if sessions else None,
    }


@router.get("/server/cpu")
async def server_cpu():
    current = metrics_engine.get_current("cpu")
    history = metrics_engine.get_history("cpu", 60)
    return {
        "current": current.model_dump() if current else None,
        "history": [s.model_dump() for s in history],
    }


@router.get("/server/memory")
async def server_memory():
    current = metrics_engine.get_current("memory")
    history = metrics_engine.get_history("memory", 30)
    return {
        "current": current.model_dump() if current else None,
        "history": [s.model_dump() for s in history],
    }


@router.get("/server/waits")
async def server_waits():
    current = metrics_engine.get_current("waits")
    history = metrics_engine.get_history("waits", 60)
    return {
        "current": current.model_dump() if current else None,
        "history": [s.model_dump() for s in history],
    }


@router.get("/workload/sessions")
async def workload_sessions():
    current = metrics_engine.get_current("sessions")
    history = metrics_engine.get_history("sessions", 60)
    return {
        "current": current.model_dump() if current else None,
        "history": [s.model_dump() for s in history],
    }


@router.get("/workload/blocking")
async def workload_blocking():
    current = metrics_engine.get_current("blocking")
    return {
        "current": current.model_dump() if current else None,
    }


@router.get("/workload/queries")
async def workload_queries():
    current = metrics_engine.get_current("queries")
    return {
        "current": current.model_dump() if current else None,
    }


@router.get("/io/files")
async def io_files():
    current = metrics_engine.get_current("io")
    history = metrics_engine.get_history("io", 20)
    return {
        "current": current.model_dump() if current else None,
        "history": [s.model_dump() for s in history],
    }


@router.get("/indexes/health")
async def indexes_health():
    current = metrics_engine.get_current("indexes")
    return {
        "current": current.model_dump() if current else None,
    }


@router.get("/query-store/overview")
async def query_store_overview():
    current = metrics_engine.get_current("query_store")
    return {
        "current": current.model_dump() if current else None,
    }


@router.get("/databases/summary")
async def databases_summary():
    current = metrics_engine.get_current("databases")
    return {
        "current": current.model_dump() if current else None,
    }


@router.get("/configuration/audit")
async def configuration_audit():
    current = metrics_engine.get_current("configuration")
    return {
        "current": current.model_dump() if current else None,
    }


# ── Admin / Control Endpoints ──────────────────────────────────

@router.get("/admin/active-db")
async def get_active_db():
    """Return the currently active database name."""
    return {
        "database": get_active_database(),
        "server": "ADDY\\SQLEXPRESS",
    }


@router.get("/admin/databases")
async def list_databases():
    """List all user databases on this SQL Server instance."""
    return {
        "databases": list_all_databases(),
        "active": get_active_database(),
    }


@router.post("/admin/switch-db")
async def switch_database(payload: dict):
    """Switch the active database and re-collect all metrics."""
    db_name = payload.get("database", "").strip()
    if not db_name:
        return {"error": "database name required"}, 400

    available = list_all_databases()
    if db_name not in available:
        return {"error": f"'{db_name}' not found on server", "available": available}

    set_active_database(db_name)
    metrics_engine.reset_history()
    metrics_engine.force_refresh_all()
    return {
        "success": True,
        "active": db_name,
        "message": f"Switched to {db_name} and refreshed all metrics.",
    }


@router.post("/admin/refresh-all")
async def refresh_all():
    """Force-refresh all collectors immediately (bypasses polling timers)."""
    metrics_engine.force_refresh_all()
    return {
        "success": True,
        "database": get_active_database(),
        "message": "All collectors refreshed.",
    }

