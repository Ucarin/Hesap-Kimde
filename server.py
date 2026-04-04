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

# State (Memory-only for real-time sync, persistence moves to DB)
connected_clients: List[WebSocket] = []
users: Dict[str, dict] = {} # e.g. {"user_id": {"name": "Doğa", "approved": False, "safe": False}}
shared_cart: List[dict] = [] 
app_state = "shopping" 

# Local logging for debug
def log_debug(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    with open("debug.log", "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

async def mark_paid(name, current_cart=None):
    log_debug(f"mark_paid: LOSER={name}, ITEMS={len(current_cart or [])}")
    
    import datetime
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

async def check_history_reset(active_names):
    if not active_names:
        return
    hist = await get_history()
    paid_names = {h["loser"] for h in hist}
    # Herkes ödeme yapmışsa geçmişi temizle
    if all(n in paid_names for n in active_names):
        await clear_history()
        for uid in users:
            users[uid]["safe"] = False

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


# Load initial snacks
snacks = []
try:
    with open("market_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        snacks = data.get("snacks", [])
        for item in snacks:
            if item.get("market") == "A101":
                item["image"] = _sanitize_a101_image_url(item.get("image") or "")
except:
    pass

async def broadcast_state():
    state_msg = {
        "type": "state_update",
        "users": users,
        "cart": shared_cart,
        "app_state": app_state,
        "history": await get_history()
    }
    for client in connected_clients:
        try:
            await client.send_json(state_msg)
        except:
            pass

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global app_state
    await websocket.accept()
    connected_clients.append(websocket)
    user_id = str(id(websocket))
    
    users[user_id] = {"name": f"Misafir_{user_id[-4:]}", "approved": False, "safe": False}
    
    snacks = await get_snacks()
    # Sanitize A101 images specifically
    for item in snacks:
        if item.get("market") == "A101":
            item["image"] = _sanitize_a101_image_url(item.get("image") or "")

    await websocket.send_json({"type": "init_products", "products": snacks})
    await broadcast_state()
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "set_name":
                name = data.get("name")
                users[user_id]["name"] = name
                hist = await get_history()
                paid_names = {h["loser"] for h in hist}
                if name in paid_names:
                    users[user_id]["safe"] = True
                else:
                    users[user_id]["safe"] = False
                
                await check_history_reset([u["name"] for u in users.values()])
                await broadcast_state()
                
            elif msg_type == "add_to_cart":
                product = data.get("product")
                product["added_by"] = users[user_id]["name"]
                shared_cart.append(product)
                for uid in users:
                    users[uid]["approved"] = False
                await broadcast_state()
                
            elif msg_type == "remove_from_cart":
                idx = data.get("index")
                if 0 <= idx < len(shared_cart):
                    shared_cart.pop(idx)
                    for uid in users:
                        users[uid]["approved"] = False
                    await broadcast_state()
                    
            elif msg_type == "toggle_approve":
                users[user_id]["approved"] = data.get("approved", False)
                all_approved = len(users) > 0 and all(u["approved"] for u in users.values())
                if all_approved and shared_cart:
                    app_state = "wheel"
                else:
                    app_state = "shopping"
                await broadcast_state()
                
            elif msg_type == "spin_wheel":
                if app_state == "wheel":
                    msg = {
                        "type": "wheel_spin",
                        "mode": data.get("mode", "roulette"),
                        "target_index": data.get("target_index", 0)
                    }
                    for client in connected_clients:
                        await client.send_json(msg)

            elif msg_type == "wheel_result_eliminate":
                eliminated_user_id = data.get("eliminated_user_id")
                msg = {
                    "type": "user_eliminated",
                    "user_id": eliminated_user_id
                }
                for client in connected_clients:
                    await client.send_json(msg)
                    
            elif msg_type == "record_loser":
                loser_name = data.get("loser_name")
                log_debug(f"MSG RECEIVED: record_loser for {loser_name}")
                if loser_name:
                    success = await mark_paid(loser_name, list(shared_cart))
                    if success:
                        # Direct toast to all
                        toast_msg = {
                            "type": "toast",
                            "message": f"{loser_name} başarıyla kaydedildi! ✅",
                            "toast_type": "success"
                        }
                        for client in connected_clients:
                            await client.send_json(toast_msg)
                            
                    for uid in users:
                        if users[uid]["name"] == loser_name:
                            users[uid]["safe"] = True
                    await broadcast_state()

            elif msg_type == "reset_game":
                app_state = "shopping"
                for uid in users:
                    users[uid]["approved"] = False
                shared_cart.clear()
                await check_history_reset([u["name"] for u in users.values()])
                await broadcast_state()

    except WebSocketDisconnect:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        if user_id in users:
            del users[user_id]
        await broadcast_state()

from fastapi.responses import RedirectResponse
@app.get("/")
def read_root():
    return RedirectResponse(url="/static/index.html")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
