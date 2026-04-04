let ws;
let snacksData = [];
let usersState = {};
let cartState = [];
let myApproved = false;
let currentRotation = 0;
let currentUser = JSON.parse(localStorage.getItem('sr_user')) || null;
let globalHistory = [];

document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const loginModal = document.getElementById('login-modal');
    const usernameInput = document.getElementById('username-input');

    // Lobby Elements
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const roomListContainer = document.getElementById('room-list');
    const createBtn = document.getElementById('create-btn');
    const newRoomIdInput = document.getElementById('new-room-id');
    const newRoomPassInput = document.getElementById('new-room-pass');

    // Password Modal Elements
    const passwordModal = document.getElementById('password-modal');
    const joinRoomPassInput = document.getElementById('join-room-pass');
    const submitPassBtn = document.getElementById('submit-pass-btn');
    const cancelPassBtn = document.getElementById('cancel-pass-btn');
    
    const productGrid = document.getElementById('product-grid');
    const searchInput = document.getElementById('search-input');
    
    const userCount = document.getElementById('user-count');
    const usersList = document.getElementById('users-list');
    
    const cartList = document.getElementById('cart-list');
    const cartTotalPrice = document.getElementById('cart-total-price');
    const approveBtn = document.getElementById('approve-btn');

    // Auth Elements
    const authTabBtn = document.querySelector('[data-tab="auth"]');
    const lobbyTabBtn = document.querySelector('[data-tab="lobby"]');
    const authLoginView = document.getElementById('auth-login-view');
    const authRegisterView = document.getElementById('auth-register-view');
    const showRegister = document.getElementById('show-register');
    const showLogin = document.getElementById('show-login');
    const loginBtn = document.getElementById('login-btn');
    const registerBtn = document.getElementById('register-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const loggedInInfo = document.getElementById('loggedInInfo'); // CSS'deki isimlendirme
    const loggedUserName = document.getElementById('logged-user-name');
    const openProfileBtn = document.getElementById('open-profile-btn');
    const profileModal = document.getElementById('profile-modal');
    const closeProfileBtn = document.getElementById('close-profile-btn');
    
    const wheelOverlay = document.getElementById('wheel-overlay');
    const wheelCanvas = document.getElementById('wheel-canvas');
    const spinBtn = document.getElementById('spin-btn');
    const winnerText = document.getElementById('winner-text');
    const winnerCartSummary = document.getElementById('winner-cart-summary');
    const wheelEndActions = document.getElementById('wheel-end-actions');
    const viewPayerCartBtn = document.getElementById('view-payer-cart-btn');
    const wheelCartToggleBtn = document.getElementById('wheel-cart-toggle-btn');
    const resetGameBtn = document.getElementById('reset-game-btn');
    const closeWheelBtn = document.getElementById('close-wheel-btn');

    const openHistoryBtn = document.getElementById('open-history-btn');
    const closeHistoryBtn = document.getElementById('close-history-btn');
    const historyOverlay = document.getElementById('history-overlay');
    const lastResultContainer = document.getElementById('last-result-container');
    const historyContainer = document.getElementById('history-container');
    const toastContainer = document.getElementById('toast-container');

    const ctx = wheelCanvas.getContext('2d');

    // --- AUTH UI GÜNCELLEME (Portal Uyumu) ---
    function updateAuthUI() {
        if (currentUser) {
            // Kayıtlı Giriş Yapılmış
            usernameInput.style.display = 'none';
            if(loggedInInfo) loggedInInfo.style.display = 'block';
            if(loggedUserName) loggedUserName.textContent = currentUser.username;
            if(openProfileBtn) openProfileBtn.style.display = 'inline-block';
            if(authTabBtn) authTabBtn.innerHTML = `<span>👤 ${currentUser.username}</span>`;
            
            // Register/Login formlarını gizle
            if(authLoginView) authLoginView.style.display = 'none';
            if(authRegisterView) authRegisterView.style.display = 'none';
            
            usernameInput.value = currentUser.username;
        } else {
            // Misafir Durumu
            usernameInput.style.display = 'block';
            if(loggedInInfo) loggedInInfo.style.display = 'none';
            if(openProfileBtn) openProfileBtn.style.display = 'none';
            if(authTabBtn) authTabBtn.innerHTML = `<span>Giriş / Kayıt</span>`;
            if(authLoginView) authLoginView.style.display = 'block';
        }
    }

    // Tab Switching
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
        });
    });

    // Login / Register Actions
    loginBtn.addEventListener('click', () => {
        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value;
        if(!username || !password) return showToast("Eksik bilgi!", "error");
        ws.send(JSON.stringify({ type: 'login', username, password }));
    });

    registerBtn.addEventListener('click', () => {
        const username = document.getElementById('reg-username').value.trim();
        const password = document.getElementById('reg-password').value;
        if(!username || !password) return showToast("Eksik bilgi!", "error");
        ws.send(JSON.stringify({ type: 'register', username, password }));
    });

    logoutBtn.addEventListener('click', () => {
        currentUser = null;
        localStorage.removeItem('sr_user');
        updateAuthUI();
        showToast("Çıkış yapıldı.", "info");
    });

    // Create Room (Kayıtlı/Misafir bilgisini gönderir)
    createBtn.addEventListener('click', () => {
        const name = usernameInput.value.trim();
        const room = newRoomIdInput.value.trim();
        const pass = newRoomPassInput.value.trim();
        if(!name) { showToast("Önce adını yaz!", "error"); return; }
        if(!room) { showToast("Oda adı gerekli!", "error"); return; }
        
        ws.send(JSON.stringify({ 
            type: 'create_room', 
            name, 
            room_id: room, 
            password: pass || null,
            is_registered: currentUser !== null 
        }));
    });

    submitPassBtn.addEventListener('click', () => {
        const name = usernameInput.value.trim();
        const pass = joinRoomPassInput.value.trim();
        if(!name) { showToast("Önce adını yaz!", "error"); return; }
        
        passwordModal.classList.remove('active');
        ws.send(JSON.stringify({ 
            type: 'join_room', 
            name, 
            room_id: pendingRoomId, 
            password: pass,
            is_registered: currentUser !== null 
        }));
        pendingRoomId = null;
    });

    // WebSocket Connection
    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            
            if (msg.type === 'error') showToast(msg.message, 'error');
            else if (msg.type === 'room_list') renderLobbyList(msg.rooms);
            else if (msg.type === 'login_success') {
                currentUser = msg.user;
                localStorage.setItem('sr_user', JSON.stringify(currentUser));
                updateAuthUI();
                showToast("Giriş başarılı! ✅", "success");
                if(lobbyTabBtn) lobbyTabBtn.click();
            }
            else if (msg.type === 'init_products') {
                if(loginModal) loginModal.classList.remove('active');
                snacksData = msg.products;
                renderProducts(snacksData);
            } 
            else if (msg.type === 'state_update') {
                usersState = msg.users;
                cartState = msg.cart;
                renderUsers();
                renderCart();
                if (msg.history) {
                    globalHistory = msg.history;
                    renderHistory(msg.history);
                    renderLastResult(msg.history[msg.history.length - 1]);
                }
                handleAppState(msg.app_state);
            }
            else if (msg.type === 'wheel_spin') {
                handleWheelSpin(msg);
            }
            else if (msg.type === 'toast') {
                showToast(msg.message, msg.toast_type || 'success');
            }
        };
    }

    // Lobby Listesi Render (Double Click)
    function renderLobbyList(rooms) {
        if(!rooms || rooms.length === 0) {
            roomListContainer.innerHTML = '<div class="no-rooms">Henüz aktif lobi yok.</div>';
            return;
        }

        roomListContainer.innerHTML = rooms.map(room => `
            <div class="room-card ${room.protected ? 'protected' : ''}" data-rid="${room.room_id}">
                <div class="room-info">
                    <span class="room-name">${room.room_id} ${room.protected ? '🔒' : ''}</span>
                    <span class="room-count">${room.count} Kişi</span>
                </div>
                <div class="room-join-hint">Katılmak için çift tıkla</div>
            </div>
        `).join('');

        document.querySelectorAll('.room-card').forEach(card => {
            card.addEventListener('dblclick', () => {
                const rid = card.dataset.rid;
                const name = usernameInput.value.trim();
                if(!name) { showToast("Önce adını yaz!", "error"); return; }
                const room = rooms.find(r => r.room_id === rid);
                if(room && room.protected) openPasswordModal(rid);
                else ws.send(JSON.stringify({ type: 'join_room', name, room_id: rid, is_registered: currentUser !== null }));
            });
        });
    }

    // Çark Çizim ve Mantığı (Sadece Aktifler)
    function drawWheel(overrideUsers, overrideColor) {
        const activeUsers = overrideUsers || getWheelSlots();
        const centerX = wheelCanvas.width / 2;
        const centerY = wheelCanvas.height / 2;
        const radius = centerX;

        if(activeUsers.length === 0) {
            ctx.clearRect(0, 0, wheelCanvas.width, wheelCanvas.height);
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 20px Outfit';
            ctx.textAlign = 'center';
            ctx.fillText("Yeni tur bekleniyor...", centerX, centerY);
            return;
        }
        
        const sliceAngle = (2 * Math.PI) / activeUsers.length;
        ctx.clearRect(0, 0, wheelCanvas.width, wheelCanvas.height);

        for (let i = 0; i < activeUsers.length; i++) {
            const startAngle = i * sliceAngle;
            const endAngle = startAngle + sliceAngle;
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, startAngle, endAngle);
            ctx.fillStyle = overrideColor || colors[i % colors.length];
            ctx.fill();
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            ctx.stroke();
            
            ctx.save();
            ctx.translate(centerX, centerY);
            ctx.rotate(startAngle + sliceAngle / 2);
            ctx.textAlign = 'right';
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 20px Outfit';
            ctx.fillText(activeUsers[i].name, radius - 20, 10);
            ctx.restore();
        }
    }

    // Helper: Toast mesajları
    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        let icon = type === 'success' ? '✅' : (type === 'error' ? '❌' : '🔔');
        toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => toast.remove(), 400);
        }, 3000);
    }

    // Init
    connectWebSocket();
    updateAuthUI();
});