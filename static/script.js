let ws;

let snacksData = [];

let usersState = {};

let cartState = [];

let myApproved = false;

let currentRotation = 0;

let currentUser = JSON.parse(localStorage.getItem('sr_user')) || null;



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

    const authTab = document.querySelector('[data-tab="auth"]');

    const authLoginView = document.getElementById('auth-login-view');

    const authRegisterView = document.getElementById('auth-register-view');

    const showRegister = document.getElementById('show-register');

    const showLogin = document.getElementById('show-login');

    const loginBtn = document.getElementById('login-btn');

    const registerBtn = document.getElementById('register-btn');

    const logoutBtn = document.getElementById('logout-btn');

    const loggedInInfo = document.getElementById('logged-in-info');

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



    let historyInitialized = false;

    let lastHistoryLength = 0;




    // Canvas Context
    let ctx = null;
    if (wheelCanvas) {
        ctx = wheelCanvas.getContext('2d');
    }




    function syncCartPanelButtonLabels() {

        const open = winnerCartSummary.style.display === 'block';

        viewPayerCartBtn.textContent = open ? 'Sepeti gizle' : 'Sepeti görüntüle';

        wheelCartToggleBtn.textContent = open ? 'Sepeti gizle' : 'Ortak sepet';

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




    // Auth View Switching
    if (showRegister) {
        showRegister.addEventListener('click', (e) => {
            e.preventDefault();
            authLoginView.style.display = 'none';
            authRegisterView.style.display = 'block';
        });
    }

    if (showLogin) {
        showLogin.addEventListener('click', (e) => {
            e.preventDefault();
            authRegisterView.style.display = 'none';
            authLoginView.style.display = 'block';
        });
    }



    // Login / Register Actions
    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            const usernameInput = document.getElementById('login-username');
            const passwordInput = document.getElementById('login-password');
            if (!usernameInput || !passwordInput) return;

            const username = usernameInput.value.trim();
            const password = passwordInput.value;

            if (!username || !password) return showToast("Eksik bilgi!", "error");
            ws.send(JSON.stringify({ type: 'login', username, password }));
        });
    }



    if (registerBtn) {
        registerBtn.addEventListener('click', () => {
            const usernameInput = document.getElementById('reg-username');
            const passwordInput = document.getElementById('reg-password');
            if (!usernameInput || !passwordInput) return;

            const username = usernameInput.value.trim();
            const password = passwordInput.value;

            if (!username || !password) return showToast("Eksik bilgi!", "error");
            ws.send(JSON.stringify({ type: 'register', username, password }));
        });
    }



    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            currentUser = null;
            localStorage.removeItem('sr_user');
            updateAuthUI();
        });
    }




    function updateAuthUI() {

        if (currentUser) {

            usernameInput.style.display = 'none';

            loggedInInfo.style.display = 'block';

            loggedUserName.textContent = currentUser.username;

            openProfileBtn.style.display = 'inline-block';

            // Also update the input used for joining rooms

            usernameInput.value = currentUser.username;

        } else {

            usernameInput.style.display = 'block';

            loggedInInfo.style.display = 'none';

            openProfileBtn.style.display = 'none';

        }

    }



    // Profile Modal

    openProfileBtn.addEventListener('click', () => {

        renderProfile();

        profileModal.classList.add('active');

    });

    closeProfileBtn.addEventListener('click', () => profileModal.classList.remove('active'));



    function renderProfile() {

        if (!currentUser) return;

        document.getElementById('profile-name').textContent = currentUser.username;

        document.getElementById('profile-total-spent').textContent = (currentUser.total_spent || 0).toFixed(2) + " TL";

        document.getElementById('profile-total-wins').textContent = currentUser.wins || 0;

        document.getElementById('profile-total-losses').textContent = currentUser.losses || 0;



        // Render Badges

        const badgesContainer = document.getElementById('profile-badges');

        badgesContainer.innerHTML = '';

        if ((currentUser.total_spent || 0) > 200) badgesContainer.innerHTML += '<span class="badge">💎 Zengin</span>';

        if ((currentUser.wins || 0) > 5) badgesContainer.innerHTML += '<span class="badge">🍀 Şanslı Balık</span>';

        if ((currentUser.losses || 0) > 5) badgesContainer.innerHTML += '<span class="badge">💀 Fakir Savar</span>';



        // Render Personal History (filtered from global history if available)

        // Note: For a more robust app, the server should send the specific history for this user only.

        // For now, we filter what we have in historyState if available (need to ensure historyState is updated).

        const historyList = document.getElementById('profile-history-list');

        const personalHistory = globalHistory.filter(h => h.loser === currentUser.username);



        if (personalHistory.length === 0) {

            historyList.innerHTML = '<p class="no-history">Henüz bir ödemen bulunmuyor. Şanslısın!</p>';

        } else {

            historyList.innerHTML = personalHistory.map(h => `

                <div class="mini-history-card">

                    <span>${h.date}</span>

                    <strong>${h.total} TL</strong>

                </div>

            `).join('');

        }

    }



    // Create Room

    createBtn.addEventListener('click', () => {

        const name = usernameInput.value.trim();

        const room = newRoomIdInput.value.trim();

        const pass = newRoomPassInput.value.trim();

        if (!name) { showToast("Önce adını yaz!", "error"); return; }

        if (!room) { showToast("Oda adı gerekli!", "error"); return; }



        ws.send(JSON.stringify({ type: 'create_room', name, room_id: room, password: pass || null }));

    });



    // Password Prompt State

    let pendingRoomId = null;



    function openPasswordModal(roomId) {

        pendingRoomId = roomId;

        joinRoomPassInput.value = '';

        passwordModal.classList.add('active');

        joinRoomPassInput.focus();

    }



    cancelPassBtn.addEventListener('click', () => {

        passwordModal.classList.remove('active');

        pendingRoomId = null;

    });



    submitPassBtn.addEventListener('click', () => {

        const name = usernameInput.value.trim();

        const pass = joinRoomPassInput.value.trim();

        if (!name) { showToast("Önce adını yaz!", "error"); return; }



        passwordModal.classList.remove('active');

        ws.send(JSON.stringify({ type: 'join_room', name, room_id: pendingRoomId, password: pass }));

        pendingRoomId = null;

    });



    // Rendering Lobbies

    function renderLobbyList(rooms) {

        if (!rooms || rooms.length === 0) {

            roomListContainer.innerHTML = '<div class="no-rooms">Henüz aktif lobi yok. İlkini sen kur!</div>';

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



        // Add double click listeners

        document.querySelectorAll('.room-card').forEach(card => {

            card.addEventListener('dblclick', () => {

                const rid = card.dataset.rid;

                const name = usernameInput.value.trim();

                if (!name) { showToast("Önce adını yaz!", "error"); return; }



                const room = rooms.find(r => r.room_id === rid);

                if (room && room.protected) {

                    openPasswordModal(rid);

                } else {

                    ws.send(JSON.stringify({ type: 'join_room', name, room_id: rid }));

                }

            });

        });

    }



    const cartArea = document.getElementById('cart-area');

    const cartMobileToggle = document.getElementById('cart-mobile-toggle');

    if (cartMobileToggle) {

        cartMobileToggle.addEventListener('click', () => {

            cartArea.classList.toggle('mobile-open');

        });

    }



    // Connection

    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname;
        const port = window.location.port ? `:${window.location.port}` : '';
        const wsUrl = `${protocol}//${host}${port}/ws`;



        console.log("WebSocket bağlantısı başlatılıyor:", wsUrl);

        if (ws) {
            ws.close();
        }

        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log("Sunucuya başarıyla bağlandık! ✅");
            showToast("Sunucu bağlantısı aktif.", "success");
        };

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);

            if (msg.type === 'error') {
                showToast(msg.message, 'error');
            }
            else if (msg.type === 'room_list') {
                renderLobbyList(msg.rooms);
            }
            else if (msg.type === 'login_success') {
                currentUser = msg.user;
                localStorage.setItem('sr_user', JSON.stringify(currentUser));
                updateAuthUI();
                showToast("Giriş başarılı! Hoşgeldin.", "success");
                // Navigate to Lobby tab
                tabBtns[0].click();
            }
            else if (msg.type === 'init_products') {
                loginModal.classList.remove('active');
                snacksData = msg.products;
                renderProducts(snacksData);
            }
            else if (msg.type === 'state_update') {
                usersState = msg.users;
                cartState = msg.cart;

                renderUsers();
                renderCart();
                if (msg.history) {
                    globalHistory = msg.history; // Update global reference
                    lastHistoryLength = msg.history.length;
                    historyInitialized = true;
                    renderHistory(msg.history);
                    renderLastResult(msg.history[msg.history.length - 1]);
                }

                if (msg.app_state === "wheel") {
                    wheelOverlay.classList.add('active');
                    drawWheel();
                    winnerCartSummary.style.display = 'none';
                    winnerCartSummary.innerHTML = '';
                    wheelEndActions.style.display = 'none';
                    syncCartPanelButtonLabels();
                } else {
                    wheelOverlay.classList.remove('active');
                    wheelEndActions.style.display = 'none';
                    spinBtn.disabled = false;
                    winnerText.textContent = '';
                    winnerCartSummary.style.display = 'none';
                    winnerCartSummary.innerHTML = '';
                    currentRotation = 0;
                    wheelCanvas.style.transition = 'none';
                    wheelCanvas.style.transform = 'rotate(0deg)';
                    setTimeout(() => { wheelCanvas.style.transition = ''; }, 50);
                    syncCartPanelButtonLabels();

                    // reset approval btn state if cart changed
                    const allFalse = Object.values(usersState).every(u => !u.approved);
                    if (allFalse) {
                        myApproved = false;
                        approveBtn.classList.remove('approved');
                        approveBtn.textContent = 'Sepeti Onaylıyorum';
                    }
                }
            }
            else if (msg.type === 'wheel_spin') {
                spinBtn.disabled = true;
                winnerText.textContent = "Çark Dönüyor...";
                winnerCartSummary.style.display = 'none';
                winnerCartSummary.innerHTML = '';
                wheelEndActions.style.display = 'none';
                syncCartPanelButtonLabels();

                const targetIndex = msg.target_index;
                const activeUsers = getWheelSlots();
                if (activeUsers.length === 0) return;

                const sliceDeg = 360 / activeUsers.length;
                const randomOffset = Math.random() * sliceDeg;
                const lambdaPick = targetIndex * sliceDeg + randomOffset;
                let nSpin = 5;
                let Cprime = 270 - lambdaPick + nSpin * 360;
                let deltaR = Cprime - currentRotation;
                while (deltaR < 1080) {
                    nSpin++;
                    Cprime = 270 - lambdaPick + nSpin * 360;
                    deltaR = Cprime - currentRotation;
                }
                currentRotation += deltaR;
                wheelCanvas.style.transform = `rotate(${currentRotation}deg)`;

                setTimeout(() => {
                    const loser = activeUsers[targetIndex];
                    if (!loser) return;

                    const loserColor = colors[targetIndex % colors.length];
                    let text = `Sonuç: ${loser.name}!`;
                    let showPayerCartSummary = false;

                    if (msg.mode === 'survivor') {
                        text = `${loser.name} KURTULDU!`;
                        if (activeUsers.length > 2) {
                            setTimeout(() => {
                                ws.send(JSON.stringify({ type: 'wheel_result_eliminate', eliminated_user_id: loser.userId }));
                                spinBtn.disabled = false;
                                winnerText.textContent = "Sıradaki kişi için çevir!";
                                syncCartPanelButtonLabels();
                            }, 2000);
                        } else {
                            const ultimateLoserInfo = activeUsers.filter((u, i) => i !== targetIndex)[0];
                            const ultimateLoserColor = colors[activeUsers.indexOf(ultimateLoserInfo) % colors.length];
                            text = `HESAP <span style="color:${ultimateLoserColor}">${ultimateLoserInfo.name}</span> KİŞİSİNE KALDI! 💀`;
                            ws.send(JSON.stringify({ type: 'record_loser', loser_name: ultimateLoserInfo.name }));
                            wheelEndActions.style.display = 'flex';
                            showPayerCartSummary = true;
                            drawWheel([ultimateLoserInfo], ultimateLoserColor);
                        }
                    } else {
                        text = `HESAP <span style="color:${loserColor}">${loser.name}</span> KİŞİSİNE KALDI! 💀`;
                        ws.send(JSON.stringify({ type: 'record_loser', loser_name: loser.name }));
                        wheelEndActions.style.display = 'flex';
                        showPayerCartSummary = true;
                        drawWheel([loser], loserColor);
                    }
                    winnerText.innerHTML = text;
                    if (showPayerCartSummary) renderWinnerCartSummary();
                }, 4000);
            }
            else if (msg.type === 'user_eliminated') {
                delete usersState[msg.user_id];
                drawWheel();
            }
        };

        ws.onclose = (e) => {
            console.log("WebSocket bağlantısı koptu! ❌ Sebeb:", e.reason);
            setTimeout(() => {
                console.log("Tekrar bağlanmaya çalışılıyor...");
                connectWebSocket();
            }, 3000);
        };

        ws.onerror = (err) => {
            console.error("WebSocket hatası tespit edildi:", err);
            ws.close();
        };
    }



    let globalHistory = [];



    // Connect immediately to see lobbies

    connectWebSocket();

    updateAuthUI();



    const CATEGORY_EMOJIS = {

        'Çikolata': '🍫', 'Gofret': '🧇', 'Bisküvi & Kraker': '🍪',

        'Kek': '🎂', 'Cips': '🥔', 'Kuruyemiş': '🥜',

        'Şekerleme & Sakız': '🍬', 'Sağlıklı': '🍏', 'default': '🛒'

    };



    const FAKE_IMAGE_KEYWORDS = ['aldin-aldin', 'haftanin-yildizlari', 'aldin_aldin', 'haftanin_yildizlari', 'placeholder', 'default_image'];

    function isRealImage(url) {

        if (!url) return false;

        return !FAKE_IMAGE_KEYWORDS.some(kw => url.toLowerCase().includes(kw.toLowerCase()));

    }



    function escapeHtml(str) {

        const d = document.createElement('div');

        d.textContent = str == null ? '' : String(str);

        return d.innerHTML;

    }



    function renderWinnerCartSummary(heading) {

        const h = heading != null && heading !== ''

            ? heading

            : 'Ortak sepet — ödeyecek kişi bu ürünleri görüyor';

        if (!cartState.length) {

            winnerCartSummary.innerHTML =

                `<h4>${escapeHtml(h)}</h4><p class="winner-cart-empty">Sepette ürün yok.</p>`;

            winnerCartSummary.style.display = 'block';

            syncCartPanelButtonLabels();

            return;

        }

        let total = 0;

        const rows = cartState.map((item) => {

            const priceNum = parseFloat(String(item.price).replace(',', '.').replace(/[^0-9.]/g, ''));

            if (!isNaN(priceNum)) total += priceNum;

            const hasRealImg = isRealImage(item.image);

            const emoji = CATEGORY_EMOJIS[item.category] || CATEGORY_EMOJIS['default'];

            const thumb = hasRealImg

                ? `<span class="winner-cart-thumb-wrap"><img class="winner-cart-thumb" src="${escapeHtml(item.image)}" alt="" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"><span class="winner-cart-emoji-fallback" style="display:none">${emoji}</span></span>`

                : `<span class="winner-cart-thumb-wrap"><span class="winner-cart-emoji">${emoji}</span></span>`;

            const who = item.added_by ? escapeHtml(item.added_by) : '—';

            return `<div class="winner-cart-row">${thumb}<div class="winner-cart-meta"><strong>${escapeHtml(item.name)}</strong><span>${escapeHtml(item.price)} · ${who}</span></div></div>`;

        }).join('');

        winnerCartSummary.innerHTML = `

            <h4>${escapeHtml(h)}</h4>

            <div class="winner-cart-list">${rows}</div>

            <div class="winner-cart-total"><span>Toplam</span><strong>${total.toFixed(2)} TL</strong></div>

        `;

        winnerCartSummary.style.display = 'block';

        syncCartPanelButtonLabels();

    }



    function renderHistory(history) {

        if (!history || history.length === 0) {

            historyContainer.innerHTML = '<p class="loading">Henüz bir geçmiş kaydı yok.</p>';

            return;

        }



        historyContainer.innerHTML = history.slice().reverse().map(h => {

            const cartHtml = h.cart && h.cart.length > 0

                ? `<ul>${h.cart.map(i => `<li><span class="hist-item-name">${i.name}</span> <span>${i.price}</span></li>`).join('')}</ul>`

                : 'Sepet boş';



            return `

                <div class="history-card">

                    <div class="history-card-header">

                        <span class="history-date">${h.date}</span>

                        <span class="history-price">${h.total} TL</span>

                    </div>

                    <div class="history-loser">

                        <span class="history-loser-label">Ödeyen</span>

                        <span>💀 ${h.loser}</span>

                    </div>

                    <div class="history-items-summary" style="max-height: none;">

                        ${cartHtml}

                    </div>

                </div>

             `;

        }).join('');

    }



    function renderLastResult(last) {

        if (!last) {

            lastResultContainer.innerHTML = '';

            return;

        }



        const cartHtml = last.cart && last.cart.length > 0

            ? `<ul>${last.cart.map(i => `<li><span>${i.name}</span> <strong>${i.price}</strong></li>`).join('')}</ul>`

            : 'Sepet boş';



        lastResultContainer.innerHTML = `

            <div class="last-result-section">

                <div class="section-header">

                    <h2>Son Çekiliş <span class="highlight">Sonucu</span> 🏆</h2>

                    <p>En son yapılan çekilişin özeti aşağıdadır:</p>

                </div>

                <div class="last-result-card">

                    <div class="last-result-info">

                        <div class="last-result-loser-badge">

                            ${last.loser} 💀

                        </div>

                        <div class="cart-total">

                            <span>Toplam:</span>

                            <strong>${last.total} TL</strong>

                        </div>

                        <span class="history-date">${last.date} tarihinde belirlendi.</span>

                    </div>

                    <div class="last-result-items">

                        <h4>Alınacak Ürünler:</h4>

                        ${cartHtml}

                    </div>

                </div>

            </div>

        `;

    }



    // Rendering Products

    function renderProducts(products) {

        if (products.length === 0) {

            productGrid.innerHTML = `<div class="loading">Bu kategoride ürün bulunamadı.</div>`;

            return;

        }



        productGrid.innerHTML = products.map((product, i) => {

            const hasRealImg = isRealImage(product.image);

            const emoji = CATEGORY_EMOJIS[product.category] || CATEGORY_EMOJIS['default'];

            const imgHtml = hasRealImg

                ? `<img src="${product.image}" class="product-img" alt="${product.name}" onerror="this.parentElement.querySelector('.product-emoji').style.display='flex'; this.style.display='none';">`

                : '';

            const emojiHtml = `<div class="product-emoji" style="display:${hasRealImg ? 'none' : 'flex'}">${emoji}</div>`;

            return `

            <div class="product-card">

                ${imgHtml}

                ${emojiHtml}

                <h3>${product.name}</h3>

                <div class="price-row">

                    <span class="price">${product.price}</span>

                    <button class="add-btn" onclick="addToCart('${encodeURIComponent(JSON.stringify(product))}')">+</button>

                </div>

            </div>`;

        }).join('');

    }



    let activeCategory = 'Tümü';



    // Category filter buttons

    document.querySelectorAll('.cat-btn').forEach(btn => {

        btn.addEventListener('click', () => {

            document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));

            btn.classList.add('active');

            activeCategory = btn.dataset.cat;

            applyFilters();

        });

    });



    // Search

    searchInput.addEventListener('input', applyFilters);



    function applyFilters() {

        const term = searchInput.value.toLowerCase().trim();

        let filtered = snacksData;



        if (activeCategory !== 'Tümü') {

            filtered = filtered.filter(p => p.category === activeCategory);

        }

        if (term) {

            filtered = filtered.filter(p =>

                p.name.toLowerCase().includes(term) ||

                (p.price && p.price.toLowerCase().includes(term))

            );

        }

        renderProducts(filtered);

    }



    // Globals for inline onclick

    window.addToCart = (encodedStr) => {

        const product = JSON.parse(decodeURIComponent(encodedStr));

        ws.send(JSON.stringify({ type: 'add_to_cart', product }));
        const currentLang = localStorage.getItem('lang') || 'tr';
        showToast(translations[currentLang]?.added_toast || 'Sepete eklendi!', 'success');

    };



    window.removeFromCart = (index) => {

        ws.send(JSON.stringify({ type: 'remove_from_cart', index }));

    };



    function renderUsers() {

        const uList = Object.values(usersState);

        userCount.textContent = uList.length;



        usersList.innerHTML = uList.map(u => `

            <li style="${u.safe ? 'opacity: 0.5;' : ''}">

                <span>${u.name} ${u.safe ? `<small>🛡️ ${translations[localStorage.getItem('lang') || 'tr']?.safe_badge || 'Güvende'}</small>` : ''}</span>

                ${u.approved ? '<span class="status-check">✅</span>' : '<span class="status-cross">⏳</span>'}

            </li>

        `).join('');

    }



    function renderCart() {

        if (cartState.length === 0) {

            cartList.innerHTML = `<li>${translations[localStorage.getItem('lang') || 'tr']?.empty_cart || 'Sepet boş.'}</li>`;

            cartTotalPrice.textContent = "0.00 TL";

            return;

        }



        cartList.innerHTML = cartState.map((item, i) => `

            <li>

                <div class="cart-item-info">

                    <span>${item.name} <small style="color:var(--text-muted)">(${item.added_by || (translations[localStorage.getItem('lang') || 'tr']?.system_label || 'Sistem')})</small></span>

                    <span class="cart-item-price">${item.price}</span>

                </div>

                <button class="remove-btn" onclick="removeFromCart(${i})">x</button>

            </li>

        `).join('');



        // Calculate Total

        let total = 0;

        cartState.forEach(item => {

            const priceNum = parseFloat(item.price.replace(',', '.').replace(/[^0-9.]/g, ''));

            if (!isNaN(priceNum)) total += priceNum;

        });

        cartTotalPrice.textContent = total.toFixed(2) + " TL";



        const cartMobileInfo = document.getElementById('cart-mobile-info');

        if (cartMobileInfo) {

            cartMobileInfo.textContent = `${cartState.length} ${translations[localStorage.getItem('lang') || 'tr']?.items_count || 'Ürün'} - ${total.toFixed(2)} TL`;

        }

    }



    // Approve logic

    approveBtn.addEventListener('click', () => {

        myApproved = !myApproved;

        if (myApproved) {

            approveBtn.classList.add('approved');

            approveBtn.textContent = 'Onaylandı ✅';

        } else {

            approveBtn.classList.remove('approved');

            approveBtn.textContent = 'Sepeti Onaylıyorum';

        }

        ws.send(JSON.stringify({ type: 'toggle_approve', approved: myApproved }));

    });



    // Çark: sadece ödemesi henüz düşmeyenler (!safe). Sıra Object.keys ile sabit — spin / çizim / sonuç aynı indeksi kullanmalı.

    function getWheelSlots() {

        return Object.keys(usersState)

            .filter((id) => !usersState[id].safe)

            .map((userId) => ({ userId, ...usersState[userId] }));

    }



    const colors = ['#f97316', '#4f46e5', '#10b981', '#ef4444', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4'];



    // Wheel logic

    function drawWheel(overrideUsers, overrideColor) {

        const activeUsers = overrideUsers || getWheelSlots();



        const centerX = wheelCanvas.width / 2;

        const centerY = wheelCanvas.height / 2;

        const radius = centerX;



        if (activeUsers.length === 0) {

            ctx.clearRect(0, 0, wheelCanvas.width, wheelCanvas.height);

            ctx.fillStyle = '#fff';

            ctx.font = 'bold 20px Outfit';

            ctx.textAlign = 'center';

            // Only show fallback if we are NOT overriding for the winner display

            if (!overrideUsers) {

                const lang = localStorage.getItem('lang') || 'tr';
                const msg = lang === 'tr' ? "Herkes güvende! Tur sıfırlanıyor..." : (lang === 'es' ? "¡Todos a salvo! Reiniciando..." : "Everyone is safe! Resetting tour...");
                ctx.fillText(msg, centerX, centerY);

            }

            return;

        }



        const sliceAngle = (2 * Math.PI) / activeUsers.length;



        ctx.clearRect(0, 0, wheelCanvas.width, wheelCanvas.height);



        // Reset rotation if it's a "winner take all" redraw to align with the pointer

        if (overrideUsers) {

            wheelCanvas.style.transition = 'none';

            wheelCanvas.style.transform = 'rotate(90deg)'; // Adjust so text at PI ends up at top

        }



        for (let i = 0; i < activeUsers.length; i++) {

            const startAngle = i * sliceAngle;

            const endAngle = startAngle + sliceAngle;



            ctx.beginPath();

            ctx.moveTo(centerX, centerY);

            ctx.arc(centerX, centerY, radius, startAngle, endAngle);

            ctx.closePath();



            ctx.fillStyle = overrideColor || colors[i % colors.length];

            ctx.fill();

            ctx.strokeStyle = '#fff';

            ctx.lineWidth = 2;

            ctx.stroke();



            // Text

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



    spinBtn.addEventListener('click', () => {

        const activeUsersCount = getWheelSlots().length;

        if (activeUsersCount === 0) return;



        const targetIndex = Math.floor(Math.random() * activeUsersCount);

        const mode = document.querySelector('input[name="wheel-mode"]:checked').value;



        ws.send(JSON.stringify({ type: 'spin_wheel', mode, target_index: targetIndex }));

    });



    viewPayerCartBtn.addEventListener('click', () => {

        if (winnerCartSummary.style.display === 'block') {

            winnerCartSummary.style.display = 'none';

            syncCartPanelButtonLabels();

        } else {

            renderWinnerCartSummary();

        }

    });



    wheelCartToggleBtn.addEventListener('click', () => {

        if (winnerCartSummary.style.display === 'block') {

            winnerCartSummary.style.display = 'none';

            syncCartPanelButtonLabels();

        } else {

            const lang = localStorage.getItem('lang') || 'tr';
            renderWinnerCartSummary(translations[lang]?.joint_cart_desc || 'Ortak sepet');

        }

    });



    resetGameBtn.addEventListener('click', () => {

        ws.send(JSON.stringify({ type: 'reset_game' }));

    });



    closeWheelBtn.addEventListener('click', () => {

        ws.send(JSON.stringify({ type: 'reset_game' }));

    });



    openHistoryBtn.addEventListener('click', () => {

        historyOverlay.classList.add('active');

    });



    closeHistoryBtn.addEventListener('click', () => {

        historyOverlay.classList.remove('active');

    });



    // Toast Helper

    function showToast(message, type = 'success') {

        const toast = document.createElement('div');

        toast.className = `toast ${type}`;



        let icon = '🔔';

        if (type === 'success') icon = '✅';

        if (type === 'error') icon = '❌';



        toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;

        toastContainer.appendChild(toast);



        setTimeout(() => {

            toast.classList.add('fade-out');

            setTimeout(() => {

                toast.remove();

            }, 400);

        }, 3000);

    }

});