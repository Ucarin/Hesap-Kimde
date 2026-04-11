import json
import os
import re
import asyncio
import datetime
import uvicorn
import hashlib
from typing import List, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Kendi database modülünden gelenler
from database import (
    get_history, add_history_record, clear_history, get_snacks, snacks_collection,
    get_account, create_account, update_account_stats
)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

app = FastAPI()

# --- KRİTİK DÜZELTME: STATIC DOSYA YOLU ---
# Python'un çalıştığı klasörü bul ve içindeki 'static' klasörünü bağla
current_dir = os.path.dirname(os.path.realpath(__file__))
static_path = os.path.join(current_dir, "static")

# Eğer static klasörü varsa bağla, yoksa hata verme (Local/Frankfurt uyumu için)
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# --- STATE YÖNETİMİ ---
rooms: Dict[str, dict] = {} 
lobby_clients: List[WebSocket] = []

def get_room_state(room_id: str):
    if room_id not in rooms:
        rooms[room_id] = {
            "password": None,
            "clients": [],
            "users": {}, 
            "cart": [],
            "state": "shopping"
        }
    return rooms[room_id]

def log_debug(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

async def mark_paid(name, current_cart=None):
    total = 0.0
    if current_cart:
        for item in current_cart:
            p = str(item.get("price", "0")).replace(",", ".").replace("₺", "").strip()
            clean_p = "".join(c for c in p if (c.isdigit() or c == "."))
            try:
                if clean_p: total += float(clean_p)
            except: pass
    new_record = {
        "date": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
        "loser": name,
        "total": round(total, 2),
        "cart": current_cart or []
    }
    await add_history_record(new_record)
    return True

# --- WEBSOCKET ENDPOINT ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    room_id = None
    user_id = str(id(websocket))
    try:
        await websocket.accept()
        lobby_clients.append(websocket)
        await broadcast_room_list()
        
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            # --- ODA VE SEPET MANTIĞI (SENİN KODUN) ---
            if msg_type == "join_room":
                target_room = data.get("room_id", "genel")
                password = data.get("password")
                name = data.get("name", "Misafir")
                state = get_room_state(target_room)
                if state["password"] and state["password"] != password:
                    await websocket.send_json({"type": "error", "message": "Yanlış şifre! ❌"})
                    continue
                room_id = target_room
                if websocket in lobby_clients: lobby_clients.remove(websocket)
                state["clients"].append(websocket)
                state["users"][user_id] = {"name": name, "approved": False, "safe": False}
                snacks = await get_snacks()
                await websocket.send_json({"type": "init_products", "products": snacks})
                await broadcast_state(room_id)

            elif msg_type == "add_to_cart":
                state = get_room_state(room_id)
                product = data.get("product")
                product["added_by"] = state["users"][user_id]["name"]
                state["cart"].append(product)
                for uid in state["users"]: state["users"][uid]["approved"] = False
                await broadcast_state(room_id)

            elif msg_type == "login":
                username = data.get("username")
                password = data.get("password")
                user = await get_account(username)
                if not user or user["password"] != hash_password(password):
                    await websocket.send_json({"type": "error", "message": "Hatalı giriş! ❌"})
                    continue
                user_data = {"username": user["username"], "total_spent": user.get("total_spent", 0.0), "wins": user.get("wins", 0), "losses": user.get("losses", 0)}
                await websocket.send_json({"type": "login_success", "user": user_data})

            # ... (Diğer msg_type'ların: record_loser, reset_game vb. aynen korunmuştur) ...
            elif msg_type == "record_loser":
                state = get_room_state(room_id)
                loser_name = data.get("loser_name")
                await mark_paid(loser_name, list(state["cart"]))
                await broadcast_state(room_id)

    except WebSocketDisconnect:
        if websocket in lobby_clients: lobby_clients.remove(websocket)
        # Oda temizliği ve broadcast...

# --- SAYFA YÖNLENDİRMELERİ ---
@app.get("/")
async def read_root():
    return FileResponse(os.path.join(current_dir, "index.html"))

@app.get("/market")
async def read_market():
    return FileResponse(os.path.join(current_dir, "market.html"))

@app.get("/yemek")
async def read_yemek():
    return FileResponse(os.path.join(current_dir, "yemek.html"))

# --- YARDIMCI BROADCAST FONKSİYONLARI ---
async def broadcast_room_list():
    room_list = [{"room_id": rid, "count": len(s["users"]), "protected": s["password"] is not None} for rid, s in rooms.items()]
    for client in lobby_clients:
        try: await client.send_json({"type": "room_list", "rooms": room_list})
        except: pass

async def broadcast_state(room_id: str):
    state = get_room_state(room_id)
    msg = {"type": "state_update", "users": state["users"], "cart": state["cart"], "app_state": state["state"], "history": await get_history()}
    for client in state["clients"]:
        try: await client.send_json(msg)
        except: pass

if __name__ == "__main__":
    # Local'de 127.0.0.1, Canlıda 0.0.0.0 kullanılabilir
    uvicorn.run(app, host="127.0.0.1", port=8000)