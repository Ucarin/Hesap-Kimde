import json
import os
import re
import asyncio
import datetime
import uvicorn
from typing import List, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from database import get_history, add_history_record, clear_history, get_snacks, snacks_collection

app = FastAPI()

app.mount("/static", StaticFiles(directory="."), name="static")

# State (Dictionary indexed by room_id)
rooms: Dict[str, dict] = {} 
lobby_clients: List[WebSocket] = []

def get_room_state(room_id: str):
    if room_id not in rooms:
        rooms[room_id] = {
            "password": None,
            "clients": [],
            "users": {}, # uid -> data (name, approved, safe)
            "cart": [],
            "state": "shopping"
        }
    return rooms[room_id]

# Local logging for debug
def log_debug(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    with open("debug.log", "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

async def mark_paid(name, current_cart=None):
    log_debug(f"mark_paid: LOSER={name}, ITEMS={len(current_cart or [])}")
    
    total = 0.0
    if current_cart:
        for item in current_cart:
            p = str(item.get("price", "0")).replace(",", ".").replace("₺", "").strip()
            clean_p = "".join(c for c in p if (c.isdigit() or c == "."))
            try:
                if clean_p:
                    total += float(clean_p)
            except Exception as e:
                log_debug(f"PRICE ERROR: {p} -> {e}")

    new_record = {
        "date": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
        "loser": name,
        "total": round(total, 2),
        "cart": current_cart or []
    }
    
    await add_history_record(new_record)
    log_debug(f"SAVE SUCCESS: Record added to MongoDB for {name}")
    return True

async def check_history_reset(room_id, active_names):
    if not active_names:
        return
    state = get_room_state(room_id)
    hist = await get_history()
    paid_names = {h["loser"] for h in hist}
    # Herkes ödeme yapmışsa geçmişi temizle
    if all(n in paid_names for n in active_names):
        await clear_history()
        for uid in state["users"]:
            state["users"][uid]["safe"] = False

_BAD_A101_URL = (
    "aldin-aldin", "aldin_aldin", "haftanin-yildizlari", "haftanin_yildizlari",
)


def _sanitize_a101_image_url(url: str) -> str:
    if not url or "a101.com.tr" not in url.lower():
        return url
    low = url.lower()
    if any(b in low for b in _BAD_A101_URL):
        return ""
    m = re.search(r"/CALL/Image/get/([^_/?]+)_(\d+)x(\d+)\.(png|jpg|jpeg|webp)", url, re.I)
    if m:
        slug = m.group(1)
        if "-" in slug and slug.islower() and not any(c.isdigit() for c in slug):
            return ""
    return url


async def broadcast_room_list():
    room_list = []
    for rid, state in rooms.items():
        if rid == "genel" or len(state["clients"]) > 0:
            room_list.append({
                "room_id": rid,
                "count": len(state["users"]),
                "protected": state["password"] is not None
            })
    
    msg = {"type": "room_list", "rooms": room_list}
    for client in lobby_clients:
        try:
            await client.send_json(msg)
        except:
            pass

async def broadcast_state(room_id: str):
    state = get_room_state(room_id)
    state_msg = {
        "type": "state_update",
        "users": state["users"],
        "cart": state["cart"],
        "app_state": state["state"],
        "history": await get_history()
    }
    for client in state["clients"]:
        try:
            await client.send_json(state_msg)
        except:
            pass
    # Anytime state (users) changes, lobby might need refresh
    await broadcast_room_list()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    room_id = None
    user_id = str(id(websocket))
    
    try:
        await websocket.accept()
        lobby_clients.append(websocket)
        
        # Send initial lobby list
        await broadcast_room_list()
        
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "join_room":
                target_room = data.get("room_id", "genel")
                password = data.get("password")
                name = data.get("name", "Misafir")
                
                state = get_room_state(target_room)
                
                # Password check
                if state["password"] and state["password"] != password:
                    await websocket.send_json({"type": "error", "message": "Yanlış şifre! ❌"})
                    continue
                
                # Join logic
                room_id = target_room
                if websocket in lobby_clients:
                    lobby_clients.remove(websocket)
                
                state["clients"].append(websocket)
                state["users"][user_id] = {"name": name, "approved": False, "safe": False}
                
                log_debug(f"User {name} joined room {room_id}")
                
                snacks = await get_snacks()
                for item in snacks:
                    if item.get("market") == "A101":
                        item["image"] = _sanitize_a101_image_url(item.get("image") or "")
                
                await websocket.send_json({"type": "init_products", "products": snacks})
                await broadcast_state(room_id)

            elif msg_type == "create_room":
                new_room_id = data.get("room_id")
                new_password = data.get("password")
                name = data.get("name", "Misafir")
                
                if not new_room_id:
                    await websocket.send_json({"type": "error", "message": "Oda adı boş olamaz!"})
                    continue
                
                if new_room_id in rooms and len(rooms[new_room_id]["clients"]) > 0:
                    await websocket.send_json({"type": "error", "message": "Bu oda adı zaten alınmış!"})
                    continue
                
                # Initialize room
                state = get_room_state(new_room_id)
                state["password"] = new_password if new_password else None
                
                # Auto-join
                room_id = new_room_id
                if websocket in lobby_clients:
                    lobby_clients.remove(websocket)
                
                state["clients"].append(websocket)
                state["users"][user_id] = {"name": name, "approved": False, "safe": False}
                
                log_debug(f"Room {room_id} created by {name}")
                
                snacks = await get_snacks()
                await websocket.send_json({"type": "init_products", "products": snacks})
                await broadcast_state(room_id)
                
            elif msg_type == "add_to_cart":
                if not room_id: continue
                state = get_room_state(room_id)
                product = data.get("product")
                product["added_by"] = state["users"][user_id]["name"]
                state["cart"].append(product)
                for uid in state["users"]:
                    state["users"][uid]["approved"] = False
                await broadcast_state(room_id)
                
            elif msg_type == "remove_from_cart":
                if not room_id: continue
                state = get_room_state(room_id)
                idx = data.get("index")
                if 0 <= idx < len(state["cart"]):
                    state["cart"].pop(idx)
                    for uid in state["users"]:
                        state["users"][uid]["approved"] = False
                    await broadcast_state(room_id)
                    
            elif msg_type == "toggle_approve":
                if not room_id: continue
                state = get_room_state(room_id)
                state["users"][user_id]["approved"] = data.get("approved", False)
                all_approved = len(state["users"]) > 0 and all(u["approved"] for u in state["users"].values())
                if all_approved and state["cart"]:
                    state["state"] = "wheel"
                else:
                    state["state"] = "shopping"
                await broadcast_state(room_id)
                
            elif msg_type == "spin_wheel":
                if not room_id: continue
                state = get_room_state(room_id)
                if state["state"] == "wheel":
                    msg = {
                        "type": "wheel_spin",
                        "mode": data.get("mode", "roulette"),
                        "target_index": data.get("target_index", 0)
                    }
                    for client in state["clients"]:
                        await client.send_json(msg)

            elif msg_type == "wheel_result_eliminate":
                if not room_id: continue
                state = get_room_state(room_id)
                eliminated_user_id = data.get("eliminated_user_id")
                for client in state["clients"]:
                    await client.send_json({"type": "user_eliminated", "user_id": eliminated_user_id})
                    
            elif msg_type == "record_loser":
                if not room_id: continue
                state = get_room_state(room_id)
                loser_name = data.get("loser_name")
                log_debug(f"MSG RECEIVED: record_loser for {loser_name} in room {room_id}")
                
                already_safe = any(u["name"] == loser_name and u["safe"] for u in state["users"].values())
                if not already_safe and loser_name:
                    for uid in state["users"]:
                        if state["users"][uid]["name"] == loser_name:
                            state["users"][uid]["safe"] = True
                    success = await mark_paid(loser_name, list(state["cart"]))
                    if success:
                        toast_msg = {"type": "toast", "message": f"{loser_name} başarıyla kaydedildi! ✅", "toast_type": "success"}
                        for client in state["clients"]:
                            await client.send_json(toast_msg)
                    await broadcast_state(room_id)

            elif msg_type == "reset_game":
                if not room_id: continue
                state = get_room_state(room_id)
                state["state"] = "shopping"
                for uid in state["users"]:
                    state["users"][uid]["approved"] = False
                state["cart"].clear()
                await check_history_reset(room_id, [u["name"] for u in state["users"].values()])
                await broadcast_state(room_id)

    except WebSocketDisconnect:
        if websocket in lobby_clients:
            lobby_clients.remove(websocket)
        if room_id:
            state = get_room_state(room_id)
            if websocket in state["clients"]:
                state["clients"].remove(websocket)
            if user_id in state["users"]:
                del state["users"][user_id]
            
            # Clean up empty rooms (except genel)
            if len(state["clients"]) == 0 and room_id != "genel":
                if room_id in rooms:
                    del rooms[room_id]
            
            await broadcast_state(room_id)
            await broadcast_room_list()
            
    except Exception as e:
        log_debug(f"WEBSOCKET ERROR: {e}")
        if websocket in lobby_clients:
            lobby_clients.remove(websocket)
        if room_id:
            state = get_room_state(room_id)
            if websocket in state["clients"]:
                state["clients"].remove(websocket)
            await broadcast_state(room_id)

from fastapi.responses import RedirectResponse
@app.get("/")
def read_root():
    return RedirectResponse(url="/static/index.html")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
