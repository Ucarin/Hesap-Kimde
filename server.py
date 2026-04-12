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
current_dir = os.path.dirname(os.path.realpath(__file__))
static_path = os.path.join(current_dir, "static")

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

            elif msg_type == "create_room":
                new_room = data.get("room_id")
                new_pass = data.get("password")
                name = data.get("name", "Misafir")
                if not new_room:
                    await websocket.send_json({"type": "error", "message": "Oda adı boş olamaz! ❌"})
                    continue
                state = get_room_state(new_room)
                state["password"] = new_pass
                room_id = new_room
                if websocket in lobby_clients: lobby_clients.remove(websocket)
                if websocket not in state["clients"]:
                    state["clients"].append(websocket)
                state["users"][user_id] = {"name": name, "approved": False, "safe": False}
                snacks = await get_snacks()
                await websocket.send_json({"type": "init_products", "products": snacks})
                await broadcast_room_list()
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

            elif msg_type == "register":
                username = data.get("username")
                password = data.get("password")
                exists = await get_account(username)
                if exists:
                    await websocket.send_json({"type": "error", "message": "Bu kullanıcı adı alınmış! ❌"})
                    continue
                success = await create_account(username, hash_password(password))
                if success:
                    await websocket.send_json({"type": "login_success", "user": {"username": username, "total_spent": 0, "wins": 0, "losses": 0}})
                else:
                    await websocket.send_json({"type": "error", "message": "Kayıt sırasında hata oluştu! ❌"})

            elif msg_type == "add_to_cart":
                state = get_room_state(room_id)
                product = data.get("product")
                product["added_by"] = state["users"][user_id]["name"]
                state["cart"].append(product)
                for uid in state["users"]: state["users"][uid]["approved"] = False
                await broadcast_state(room_id)

            elif msg_type == "remove_from_cart":
                state = get_room_state(room_id)
                index = data.get("index")
                if 0 <= index < len(state["cart"]):
                    state["cart"].pop(index)
                    for uid in state["users"]: state["users"][uid]["approved"] = False
                    await broadcast_state(room_id)

            elif msg_type == "toggle_approve":
                state = get_room_state(room_id)
                approved = data.get("approved", False)
                state["users"][user_id]["approved"] = approved
                await broadcast_state(room_id)
                # Check if everyone is approved
                all_approved = all(u["approved"] for u in state["users"].values())
                if all_approved and len(state["users"]) > 0 and len(state["cart"]) > 0:
                    state["state"] = "wheel"
                    await broadcast_state(room_id)

            elif msg_type == "spin_wheel":
                state = get_room_state(room_id)
                mode = data.get("mode", "roulette")
                target_index = data.get("target_index")
                await broadcast_to_room(room_id, {
                    "type": "wheel_spin",
                    "mode": mode,
                    "target_index": target_index
                })

            elif msg_type == "wheel_result_eliminate":
                state = get_room_state(room_id)
                elim_id = data.get("eliminated_user_id")
                if elim_id in state["users"]:
                    state["users"][elim_id]["safe"] = True
                    await broadcast_state(room_id)

            elif msg_type == "record_loser":
                state = get_room_state(room_id)
                loser_name = data.get("loser_name")
                total = 0.0
                for item in state["cart"]:
                    p = str(item.get("price", "0")).replace(",", ".").replace("₺", "").strip()
                    clean_p = "".join(c for c in p if (c.isdigit() or c == "."))
                    try: total += float(clean_p)
                    except: pass
                
                await mark_paid(loser_name, list(state["cart"]))
                await update_account_stats(loser_name, total, is_loss=True)
                for uid, udata in state["users"].items():
                    if udata["name"] != loser_name:
                        await update_account_stats(udata["name"], 0, is_loss=False)
                
                await broadcast_state(room_id)

            elif msg_type == "reset_game":
                state = get_room_state(room_id)
                state["cart"] = []
                state["state"] = "shopping"
                for uid in state["users"]:
                    state["users"][uid]["approved"] = False
                    state["users"][uid]["safe"] = False
                await broadcast_state(room_id)

    except WebSocketDisconnect:
        if websocket in lobby_clients: lobby_clients.remove(websocket)
        for rid, s in rooms.items():
            if websocket in s["clients"]:
                s["clients"].remove(websocket)
                if user_id in s["users"]: del s["users"][user_id]
                await broadcast_state(rid)
        await broadcast_room_list()

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

async def broadcast_to_room(room_id: str, msg: dict):
    state = get_room_state(room_id)
    for client in state["clients"]:
        try: await client.send_json(msg)
        except: pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)