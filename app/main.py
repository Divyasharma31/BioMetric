from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from contextlib import asynccontextmanager
from app.api.routes import attendance, admin, users
from app.mqtt.client import mqtt_manager
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting GridSphere IoT Core...")
    mqtt_manager.start() # [cite: 74, 84]
    yield
    logger.info("Shutting down...")
    mqtt_manager.stop()

app = FastAPI(title="GridSphere Multi-Tenant API", lifespan=lifespan)

# --- UI ROUTE (Placed at the top for priority) ---
@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def serve_dashboard():
    # Looks for index.html in the biomet root folder
    # This goes up one level from app/main.py
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "index.html")
    
    if os.path.exists(file_path):
        return FileResponse(file_path)
    
    return HTMLResponse(
        content=f"<h1>Dashboard File Not Found</h1><p>Looked in: {file_path}</p>", 
        status_code=404
    )

# --- REGISTER ROUTERS ---
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(attendance.router, prefix="/api/attendance", tags=["Attendance"]) # [cite: 74, 79]
app.include_router(admin.router, prefix="/api/admin", tags=["Admin/Commands"]) # [cite: 78]

# --- GLOBAL ERROR HANDLING ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"System Error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})