"""API Gateway — single entry point that routes to downstream services."""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
from typing import Any

app = FastAPI(title="AutoShop API Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVICE_URLS = {
    "vehicle_catalog": "http://localhost:8001",
    "order_service": "http://localhost:8002",
    "inventory_service": "http://localhost:8003",
    "auth_service": "http://localhost:8004",
    "notification_service": "http://localhost:8005",
}


async def proxy_request(service_name: str, path: str, method: str, body: Any = None, params: dict = None) -> dict:
    """Forward a request to a downstream service and return the response."""
    base_url = SERVICE_URLS.get(service_name)
    if not base_url:
        raise HTTPException(status_code=503, detail=f"Unknown service: {service_name}")
    url = f"{base_url}{path}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.request(method=method, url=url, json=body, params=params)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


def check_service_health(service_name: str) -> dict:
    """Synchronously check the health of a single service."""
    base_url = SERVICE_URLS.get(service_name)
    if not base_url:
        return {"status": "unknown", "service": service_name}
    try:
        resp = httpx.get(f"{base_url}/health", timeout=3.0)
        return resp.json()
    except httpx.RequestError:
        return {"status": "unreachable", "service": service_name}


def aggregate_vehicle_orders(vehicle_id: int) -> dict:
    """Aggregate vehicle details with its orders — cross-service composite call."""
    vehicle_resp = httpx.get(f"{SERVICE_URLS['vehicle_catalog']}/vehicles/{vehicle_id}", timeout=5.0)
    if vehicle_resp.status_code != 200:
        raise HTTPException(status_code=vehicle_resp.status_code, detail="Vehicle not found")
    vehicle = vehicle_resp.json()
    orders_resp = httpx.get(f"{SERVICE_URLS['order_service']}/orders/vehicle/{vehicle_id}", timeout=5.0)
    orders = orders_resp.json() if orders_resp.status_code == 200 else []
    return {"vehicle": vehicle, "orders": orders, "order_count": len(orders)}


def get_inventory_summary() -> dict:
    """Retrieve inventory status including low-stock parts."""
    parts_resp = httpx.get(f"{SERVICE_URLS['inventory_service']}/parts", timeout=5.0)
    low_stock_resp = httpx.get(f"{SERVICE_URLS['inventory_service']}/stock/low", timeout=5.0)
    parts = parts_resp.json() if parts_resp.status_code == 200 else []
    low_stock = low_stock_resp.json() if low_stock_resp.status_code == 200 else []
    return {"total_parts": len(parts), "low_stock_count": len(low_stock), "low_stock_items": low_stock}


def forward_login_request(username: str, password: str) -> dict:
    """Forward login credentials to the auth service."""
    resp = httpx.post(
        f"{SERVICE_URLS['auth_service']}/login",
        params={"username": username, "password": password},
        timeout=5.0,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Authentication failed")
    return resp.json()


def validate_token_via_auth(token: str) -> dict:
    """Ask auth_service to validate a bearer token."""
    resp = httpx.get(f"{SERVICE_URLS['auth_service']}/verify", params={"token": token}, timeout=5.0)
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return resp.json()


# Gateway routes
@app.get("/health")
def gateway_health():
    healths = {name: check_service_health(name) for name in SERVICE_URLS}
    return {"gateway": "ok", "services": healths}


@app.get("/vehicles/{vehicle_id}/full")
def vehicle_full_profile(vehicle_id: int):
    return aggregate_vehicle_orders(vehicle_id)


@app.get("/inventory/summary")
def inventory_summary():
    return get_inventory_summary()


@app.post("/auth/login")
def login(username: str, password: str):
    return forward_login_request(username, password)


@app.get("/auth/verify")
def verify_token(token: str):
    return validate_token_via_auth(token)


@app.get("/vehicles")
async def list_vehicles(skip: int = 0, limit: int = 100):
    return await proxy_request("vehicle_catalog", "/vehicles", "GET", params={"skip": skip, "limit": limit})


@app.get("/orders")
async def list_orders(skip: int = 0, limit: int = 100):
    return await proxy_request("order_service", "/orders", "GET", params={"skip": skip, "limit": limit})


@app.post("/orders")
async def create_order(request: Request):
    body = await request.json()
    return await proxy_request("order_service", "/orders", "POST", body=body)
