from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from app.models import URLRequest
from app.utils import generate_short_id
from datetime import datetime

router = APIRouter()
db = {}
analytics = []

@router.post("/shorten")
def shorten_url(payload: URLRequest):
    short_id = generate_short_id()
    db[short_id] = payload.url
    return {"short_url": f"http://localhost:8000/{short_id}"}

@router.get("/{short_id}")
def redirect_to_url(short_id: str, request: Request):
    if short_id not in db:
        raise HTTPException(status_code=404, detail="URL not found")
    
    analytics.append({
        "short_id": short_id,
        "ip": request.client.host,
        "timestamp": datetime.utcnow().isoformat()
    })

    return RedirectResponse(url=db[short_id])

@router.get("/analytics")
def get_analytics():
    return {"clicks": analytics}
