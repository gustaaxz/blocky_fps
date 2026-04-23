import re

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Add TDM to UI
tdm_old = """<div>
                        <label class="text-[10px] text-slate-400 font-bold ml-1">SENHA (OPCIONAL)</label>
                        <input type="password" id="new-room-pass" placeholder="VAZIO"
                            class="w-full p-4 bg-slate-950 border-2 border-slate-800 rounded-xl outline-none focus:border-emerald-500 text-white font-bold">
                    </div>"""
tdm_new = """<div>
                        <label class="text-[10px] text-slate-400 font-bold ml-1">SENHA (OPCIONAL)</label>
                        <input type="password" id="new-room-pass" placeholder="VAZIO"
                            class="w-full p-4 bg-slate-950 border-2 border-slate-800 rounded-xl outline-none focus:border-emerald-500 text-white font-bold">
                    </div>
                </div>
                <div class="mt-4 flex items-center gap-2">
                    <input type="checkbox" id="new-room-tdm" class="w-5 h-5 accent-emerald-500">
                    <label class="text-sm text-slate-300 font-bold">MATA-MATA EM EQUIPE (TDM)</label>"""
html = html.replace(tdm_old, tdm_new)

# Create room TDM
cr_old = "hasPass: !!rPass,"
cr_new = "hasPass: !!rPass, isTdm: document.getElementById('new-room-tdm').checked,"
html = html.replace(cr_old, cr_new)

# Join room logic for TDM
em_old = "me.hp = 100; me.targetHp = 100;"
em_new = """me.hp = 100; me.targetHp = 100;
            const rData = (await get(ref(db, `v3/rooms/${roomId}`))).val();
            let isTdm = rData.isTdm;
            window.currentRoomIsTdm = isTdm;
            if (isTdm) {
                const count = rData.players ? Object.keys(rData.players).length : 0;
                me.team = (count % 2 === 0) ? 'BLUE' : 'RED';
                document.getElementById('player-name-hud').innerText = `[${me.team}] ${me.name}`;
            }"""
html = html.replace(em_old, em_new)

# Add team logic in EnterMatch fbUpdate
em_up_old = "set(pRef, { id: myId, name: me.name, x: me.x, y: me.y, hp: 100, targetHp: 100, kills: 0, weapon: 1 });"
em_up_new = "set(pRef, { id: myId, name: me.name, x: me.x, y: me.y, hp: 100, targetHp: 100, kills: 0, weapon: 1, team: me.team || 'NONE' });"
html = html.replace(em_up_old, em_up_new)

# Damage check TDM
dmg_check_old = "const newTarget = Math.max(0, currentTarget - dmg);"
dmg_check_new = """if (window.currentRoomIsTdm && p.team === me.team && id !== myId) return;
                const newTarget = Math.max(0, currentTarget - dmg);"""
html = html.replace(dmg_check_old, dmg_check_new)

# Generate destructible barricades & powerups
gen_old = """        function generateObstacles(seedStr) {
            obstacles = []; bushes = [];"""
gen_new = """        function generateObstacles(seedStr) {
            obstacles = []; bushes = []; items = [];
            const rnd = mulberry32(hashCode(seedStr || "default"));"""
html = html.replace(gen_old, gen_new)

gen2_old = """            for (let i = 0; i < 20; i++) {
                bushes.push({ x: (rnd() - 0.5) * MAP_SIZE * 1.8, y: (rnd() - 0.5) * MAP_SIZE * 1.8, w: 120 + rnd() * 100, h: 120 + rnd() * 100 });
            }
        }"""
gen2_new = """            for (let i = 0; i < 20; i++) {
                bushes.push({ x: (rnd() - 0.5) * MAP_SIZE * 1.8, y: (rnd() - 0.5) * MAP_SIZE * 1.8, w: 120 + rnd() * 100, h: 120 + rnd() * 100 });
            }
            for (let i = 0; i < 20; i++) {
                obstacles.push({ x: (rnd() - 0.5) * MAP_SIZE * 1.8, y: (rnd() - 0.5) * MAP_SIZE * 1.8, w: 60, h: 60, destructible: true, hp: 100 });
            }
            for (let i = 0; i < 15; i++) {
                items.push({ x: (rnd() - 0.5) * MAP_SIZE * 1.8, y: (rnd() - 0.5) * MAP_SIZE * 1.8, active: true });
            }
        }"""
html = html.replace(gen2_old, gen2_new)

# Draw barricades & powerups
draw_old = "ctx.fillStyle = '#1e293b'; obstacles.forEach(o => ctx.fillRect(o.x, o.y, o.w, o.h));"
draw_new = """obstacles.forEach(o => {
                if (o.destructible) { ctx.fillStyle = '#854d0e'; ctx.fillRect(o.x, o.y, o.w, o.h); }
                else { ctx.fillStyle = '#1e293b'; ctx.fillRect(o.x, o.y, o.w, o.h); }
            });
            items.forEach(i => {
                if(i.active) {
                    ctx.fillStyle = '#ffffff'; ctx.fillRect(i.x-15, i.y-15, 30, 30);
                    ctx.fillStyle = '#ef4444'; ctx.fillRect(i.x-10, i.y-4, 20, 8); ctx.fillRect(i.x-4, i.y-10, 8, 20);
                }
            });"""
html = html.replace(draw_old, draw_new)

# Destructible projectile collision
proj_col_old = """                for (let o of obstacles) {
                    if (p.x > o.x && p.x < o.x + o.w && p.y > o.y && p.y < o.y + o.h) {
                        hitObstacle = true; break;
                    }
                }"""
proj_col_new = """                for (let i = obstacles.length - 1; i >= 0; i--) {
                    let o = obstacles[i];
                    if (p.x > o.x && p.x < o.x + o.w && p.y > o.y && p.y < o.y + o.h) {
                        if (o.destructible) {
                            o.hp -= p.damage;
                            if (o.hp <= 0) {
                                explosions.push({x: o.x+o.w/2, y: o.y+o.h/2, r: 0, maxR: o.w, alpha: 1});
                                obstacles.splice(i, 1);
                                playSound('explosion');
                            }
                        }
                        hitObstacle = true; break;
                    }
                }"""
html = html.replace(proj_col_old, proj_col_new)

# Projectile filter bounce for grenade
p2_old = """                    for (let o of obstacles) {
                        if (p.x > o.x && p.x < o.x + o.w && p.y > o.y && p.y < o.y + o.h) {
                            p.angle += Math.PI / 2;
                            p.x += Math.cos(p.angle) * p.speed * 2;
                            p.y += Math.sin(p.angle) * p.speed * 2;
                        }
                    }"""
p2_new = """                    for (let i = obstacles.length - 1; i >= 0; i--) {
                        let o = obstacles[i];
                        if (p.x > o.x && p.x < o.x + o.w && p.y > o.y && p.y < o.y + o.h) {
                            if (o.destructible) { o.hp -= 50; if(o.hp<=0) obstacles.splice(i,1); }
                            p.angle += Math.PI / 2;
                            p.x += Math.cos(p.angle) * p.speed * 2;
                            p.y += Math.sin(p.angle) * p.speed * 2;
                        }
                    }"""
html = html.replace(p2_old, p2_new)

# Update Game for Powerups and Bots
up_end_old = """            camera.x += (lookX - camera.x) * 0.1;
            camera.y += (lookY - camera.y) * 0.1;

            projectiles = projectiles.filter(p => {"""
up_end_new = """            camera.x += (lookX - camera.x) * 0.1;
            camera.y += (lookY - camera.y) * 0.1;
            
            // Medkits check
            for (let i of items) {
                if (i.active && Math.hypot(me.x - i.x, me.y - i.y) < 30) {
                    i.active = false;
                    me.targetHp = Math.min(100, me.targetHp + 40);
                    playSound('reload');
                }
            }

            // AI Bots logic
            const allIds = Object.keys(players).sort();
            if (allIds[0] === myId) {
                let botCount = Object.values(players).filter(p => p.isBot).length;
                let hCount = Object.values(players).filter(p => !p.isBot).length;
                if (botCount + hCount < 4 && Math.random() < 0.01) {
                    const bId = 'BOT_' + Math.random().toString(36).substring(7);
                    const spawn = getSafeSpawn();
                    let bTeam = 'RED';
                    if (window.currentRoomIsTdm) {
                        const tc = Object.values(players).filter(p => p.team === 'RED').length;
                        bTeam = tc > (botCount+hCount)/2 ? 'BLUE' : 'RED';
                    }
                    set(ref(db, `v3/rooms/${currentRoomId}/players/${bId}`), {
                        id: bId, name: 'CYBORG', x: spawn.x, y: spawn.y, angle: 0, hp: 100, targetHp: 100, kills: 0, weapon: 2, isBot: true, team: bTeam
                    });
                }
                
                for (let id in players) {
                    const p = players[id];
                    if (p.isBot && p.hp > 0) {
                        let nearest = null; let minDist = Infinity;
                        for (let hid in players) {
                            if (players[hid].hp > 0 && id !== hid && (!window.currentRoomIsTdm || players[hid].team !== p.team)) {
                                let d = Math.hypot(p.x - players[hid].x, p.y - players[hid].y);
                                if (d < minDist) { minDist = d; nearest = players[hid]; }
                            }
                        }
                        if (nearest) {
                            let ang = Math.atan2(nearest.y - p.y, nearest.x - p.x);
                            let nx = p.x + Math.cos(ang) * 4.5;
                            let ny = p.y + Math.sin(ang) * 4.5;
                            let cx = false, cy = false;
                            obstacles.forEach(o => {
                                if (checkCol(o, nx, p.y)) cx = true;
                                if (checkCol(o, p.x, ny)) cy = true;
                            });
                            if (!cx) p.x = nx; else p.y += (Math.random()-0.5)*15;
                            if (!cy) p.y = ny; else p.x += (Math.random()-0.5)*15;
                            
                            p.angle = ang;
                            if (minDist < 600 && Math.random() < 0.04) {
                                const shot = { owner: id, x: p.x, y: p.y, angle: p.angle + (Math.random()-0.5)*0.2, weapon: p.weapon };
                                push(ref(db, `v3/rooms/${currentRoomId}/shots`), shot);
                            }
                            fbUpdate(ref(db, `v3/rooms/${currentRoomId}/players/${id}`), { x: p.x, y: p.y, angle: p.angle });
                        }
                    } else if (p.isBot && p.hp <= 0 && p.targetHp <= 0 && !p.respawning) {
                        fbUpdate(ref(db, `v3/rooms/${currentRoomId}/players/${id}`), { targetHp: 100, respawning: true });
                        setTimeout(() => {
                           if(active) {
                               const spawn = getSafeSpawn();
                               fbUpdate(ref(db, `v3/rooms/${currentRoomId}/players/${id}`), { x: spawn.x, y: spawn.y, hp: 100, targetHp: 100, respawning: false });
                           }
                        }, 3000);
                    }
                }
            }

            projectiles = projectiles.filter(p => {"""
html = html.replace(up_end_old, up_end_new)

# BGM looping drone when audio enabled
audio_old = "document.getElementById('audio-btn').innerText = audioEnabled ? '🔊 AUDIO ON' : '🔇 AUDIO OFF';"
audio_new = """document.getElementById('audio-btn').innerText = audioEnabled ? '🔊 AUDIO ON' : '🔇 AUDIO OFF';
            if (audioEnabled && !window.bgmOsc) {
                window.bgmOsc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                window.bgmOsc.type = 'triangle';
                window.bgmOsc.frequency.setValueAtTime(60, audioCtx.currentTime);
                gain.gain.setValueAtTime(0.01, audioCtx.currentTime);
                window.bgmOsc.connect(gain); gain.connect(audioCtx.destination);
                window.bgmOsc.start();
            } else if (!audioEnabled && window.bgmOsc) {
                window.bgmOsc.stop(); window.bgmOsc = null;
            }"""
html = html.replace(audio_old, audio_new)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Patch 4 applied!")
