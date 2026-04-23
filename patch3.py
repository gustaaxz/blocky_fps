import re

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# HTML inject
hud_em_jogo = "<!-- HUD EM JOGO -->"
new_ui = """<!-- 5. SCOREBOARD & CHAT -->
    <div id="tab-scoreboard" class="hidden" style="position: absolute; inset: 10%; background: rgba(15,23,42,0.95); border: 2px solid #10b981; border-radius: 10px; z-index: 2000; padding: 20px; color: white;">
        <h2 class="text-3xl font-black mb-4 text-emerald-400 italic text-center">PLACAR DE OPERAÇÕES</h2>
        <div id="tab-list" class="space-y-2"></div>
    </div>

    <div id="chat-container" class="hidden" style="position: absolute; left: 20px; bottom: 150px; width: 300px; background: rgba(0,0,0,0.5); border-radius: 8px; padding: 10px; pointer-events: auto; z-index: 100;">
        <div id="chat-messages" style="height: 100px; overflow-y: auto; color: white; font-size: 12px; margin-bottom: 5px; display: flex; flex-direction: column-reverse;"></div>
        <input type="text" id="chat-input" placeholder="Pressione T para falar..." style="width: 100%; background: rgba(0,0,0,0.8); border: 1px solid #10b981; color: white; padding: 5px; outline: none; border-radius: 4px; font-size: 12px; text-transform: none;">
    </div>
    
    <button onclick="toggleAudio()" id="audio-btn" class="hidden hud-panel !bg-slate-900/50 hover:bg-slate-700 !pointer-events-auto transition-all text-xs font-black" style="position: absolute; top: 20px; left: 20px; z-index: 50;">🔇 AUDIO OFF</button>
    
    <!-- HUD EM JOGO -->"""
html = html.replace(hud_em_jogo, new_ui)

# State
me_old = """            dashCooldown: 0, dashTimer: 0, dashAngle: 0, reloading: 0, grenades: 3,
            shake: 0, lastHp: 100, hitFlash: 0, killerPos: null
        };"""
me_new = """            dashCooldown: 0, dashTimer: 0, dashAngle: 0, reloading: 0, grenades: 3,
            shake: 0, lastHp: 100, hitFlash: 0, killerPos: null, streak: 0, rank: 'RECRUTA'
        };
        
        let myXp = parseInt(localStorage.getItem('blocky_xp') || '0');
        function getRank(xp) {
            if (xp > 100) return 'LENDÁRIO';
            if (xp > 50) return 'GENERAL';
            if (xp > 20) return 'SARGENTO';
            if (xp > 5) return 'SOLDADO';
            return 'RECRUTA';
        }
        
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        let audioEnabled = false;
        window.toggleAudio = () => {
            if (audioCtx.state === 'suspended') audioCtx.resume();
            audioEnabled = !audioEnabled;
            document.getElementById('audio-btn').innerText = audioEnabled ? '🔊 AUDIO ON' : '🔇 AUDIO OFF';
        };

        function playSound(type) {
            if (!audioEnabled || audioCtx.state === 'suspended') return;
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.connect(gain); gain.connect(audioCtx.destination);
            const now = audioCtx.currentTime;
            
            if (type === 'shoot') {
                osc.type = 'square'; osc.frequency.setValueAtTime(300, now); osc.frequency.exponentialRampToValueAtTime(100, now + 0.1);
                gain.gain.setValueAtTime(0.02, now); gain.gain.exponentialRampToValueAtTime(0.001, now + 0.1);
                osc.start(now); osc.stop(now + 0.1);
            } else if (type === 'hit') {
                osc.type = 'sawtooth'; osc.frequency.setValueAtTime(150, now); osc.frequency.exponentialRampToValueAtTime(50, now + 0.2);
                gain.gain.setValueAtTime(0.05, now); gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
                osc.start(now); osc.stop(now + 0.2);
            } else if (type === 'explosion') {
                osc.type = 'sawtooth'; osc.frequency.setValueAtTime(100, now); osc.frequency.exponentialRampToValueAtTime(20, now + 0.5);
                gain.gain.setValueAtTime(0.1, now); gain.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
                osc.start(now); osc.stop(now + 0.5);
            }
        }"""
html = html.replace(me_old, me_new)

# Keys logic completely replaced
keys_old = """        window.addEventListener('keydown', e => {
            keys[e.code] = true;
            if (e.code.includes('Digit')) {
                const d = e.code.replace('Digit', '');
                if (WEAPONS[d]) {
                    me.weapon = d;
                    document.querySelectorAll('.weapon-slot').forEach(s => s.classList.remove('active'));
                    document.getElementById(`w-${d}`).classList.add('active');
                    updateAmmoDisplay();
                }
            }
        });
        window.addEventListener('keyup', e => keys[e.code] = false);"""
keys_new = """        window.addEventListener('keydown', e => {
            if (e.code === 'Tab') {
                e.preventDefault();
                document.getElementById('tab-scoreboard').classList.remove('hidden');
                const list = Object.values(players).sort((a, b) => b.kills - a.kills);
                document.getElementById('tab-list').innerHTML = list.map((p, i) => `
                    <div class="flex justify-between items-center p-3 border-b border-slate-700 bg-slate-800/50 rounded">
                        <div class="font-bold ${p.id === myId ? 'text-emerald-400' : 'text-white'}">${i+1}. [${p.rank || 'RECRUTA'}] ${p.name}</div>
                        <div class="font-black text-xl">${p.kills} <span class="text-xs text-slate-400">KILLS</span></div>
                    </div>
                `).join('');
            }
            if (e.code === 'KeyT' && document.activeElement !== document.getElementById('chat-input')) {
                e.preventDefault();
                document.getElementById('chat-input').focus();
            }
            if (e.code === 'Enter' && document.activeElement === document.getElementById('chat-input')) {
                const input = document.getElementById('chat-input');
                if (input.value.trim()) {
                    push(ref(db, `v3/rooms/${currentRoomId}/chat`), { name: me.name, text: input.value.trim() });
                    input.value = '';
                }
                input.blur();
            }
            
            if (document.activeElement !== document.getElementById('chat-input') && document.activeElement !== document.getElementById('nickname') && document.activeElement !== document.getElementById('new-room-name') && document.activeElement !== document.getElementById('new-room-pass')) {
                keys[e.code] = true;
                if (e.code.includes('Digit')) {
                    const d = e.code.replace('Digit', '');
                    if (WEAPONS[d]) {
                        me.weapon = d;
                        document.querySelectorAll('.weapon-slot').forEach(s => s.classList.remove('active'));
                        document.getElementById(`w-${d}`).classList.add('active');
                        updateAmmoDisplay();
                    }
                }
            }
        });
        window.addEventListener('keyup', e => {
            if (e.code === 'Tab') document.getElementById('tab-scoreboard').classList.add('hidden');
            keys[e.code] = false;
        });"""
html = html.replace(keys_old, keys_new)

# Sounds in shooting
shoot_sound_old = """createProjectile(shot, true);
                }"""
shoot_sound_new = """createProjectile(shot, true);
                }
                playSound('shoot');"""
html = html.replace(shoot_sound_old, shoot_sound_new)

grenade_sound_old = """createProjectile(shot, true);
                updateAmmoDisplay();
            }"""
grenade_sound_new = """createProjectile(shot, true);
                updateAmmoDisplay();
                playSound('shoot');
            }"""
html = html.replace(grenade_sound_old, grenade_sound_new)

expl_old = "createExplosion(p.x, p.y, 200);"
expl_new = "createExplosion(p.x, p.y, 200); playSound('explosion');"
html = html.replace(expl_old, expl_new)
html = html.replace("createExplosion(p.x, p.y, 150);", "createExplosion(p.x, p.y, 150); playSound('explosion');")

# Handle enter match UI
em_old = "document.getElementById('player-name-hud').innerText = me.name;"
em_new = """document.getElementById('player-name-hud').innerText = me.name;
            document.getElementById('chat-container').classList.remove('hidden');
            document.getElementById('audio-btn').classList.remove('hidden');
            me.rank = getRank(myXp);"""
html = html.replace(em_old, em_new)

# Init game network chat
nt_old = "onValue(ref(db, `v3/rooms/${currentRoomId}/players`), (snap) => {"
nt_new = """onChildAdded(ref(db, `v3/rooms/${currentRoomId}/chat`), (snap) => {
                const msg = snap.val();
                const el = document.createElement('div');
                el.innerHTML = `<span class="font-bold text-emerald-400">${msg.name}:</span> <span class="text-white">${msg.text}</span>`;
                document.getElementById('chat-messages').prepend(el);
            });
            onValue(ref(db, `v3/rooms/${currentRoomId}/players`), (snap) => {"""
html = html.replace(nt_old, nt_new)

# Add XP, Rank and Killstreak on kill
dmg_logic_old = """if (newTarget === 0 && currentTarget > 0) {
                    me.kills++; 
                    fbUpdate(ref(db, `v3/rooms/${currentRoomId}/players/${myId}`), { kills: me.kills });
                    notify(me.name, p.name);"""
dmg_logic_new = """if (newTarget === 0 && currentTarget > 0) {
                    me.kills++; 
                    myXp++; localStorage.setItem('blocky_xp', myXp);
                    me.rank = getRank(myXp);
                    me.streak++;
                    if (me.streak === 3) push(ref(db, `v3/rooms/${currentRoomId}/chat`), { name: 'SISTEMA', text: `${me.name} ESTÁ IMPARÁVEL (3 KILLS)!` });
                    if (me.streak === 5) push(ref(db, `v3/rooms/${currentRoomId}/chat`), { name: 'SISTEMA', text: `${me.name} É UM DEUS DA GUERRA (5 KILLS)!` });
                    
                    fbUpdate(ref(db, `v3/rooms/${currentRoomId}/players/${myId}`), { kills: me.kills, rank: me.rank });
                    notify(me.name, p.name);"""
html = html.replace(dmg_logic_old, dmg_logic_new)

# Handle Death streak reset
hd_old = "me.hp = 0;"
hd_new = "me.hp = 0; me.streak = 0;"
html = html.replace(hd_old, hd_new)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Patch 3 applied!")
