import re

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1,2,4,5: Dash, Reload, Grenade, Laser Sights WEAPONS
html = html.replace("damage: 20 }", "damage: 20, clip: 12, reload: 1000 }")
html = html.replace("damage: 12 }", "damage: 12, clip: 30, reload: 1500 }")
html = html.replace("damage: 15 }", "damage: 15, clip: 6, reload: 2000 }")
html = html.replace("damage: 85 }", "damage: 85, clip: 5, reload: 2500, laser: true }")
html = html.replace("isAoE: true }", "isAoE: true, clip: 1, reload: 3000 }")

# Add me state
me_old = """        let me = {
            x: 0, y: 0, angle: 0, hp: 100, targetHp: 100, kills: 0, name: "",
            weapon: 1, lastFired: 0, ammo: { 1: Infinity, 2: 150, 3: 30, 4: 10, 5: 5 },
            dashCooldown: 0, shake: 0, lastHp: 100, hitFlash: 0, killerPos: null
        };"""
me_new = """        let me = {
            x: 0, y: 0, angle: 0, hp: 100, targetHp: 100, kills: 0, name: "",
            weapon: 1, lastFired: 0, ammo: { 1: Infinity, 2: 150, 3: 30, 4: 10, 5: 5 },
            clip: { 1: 12, 2: 30, 3: 6, 4: 5, 5: 1 },
            dashCooldown: 0, dashTimer: 0, dashAngle: 0, reloading: 0, grenades: 3,
            shake: 0, lastHp: 100, hitFlash: 0, killerPos: null
        };"""
html = html.replace(me_old, me_new)

# Movement dash
mov_old = """            let mx = 0, my = 0;
            const speed = keys.Space ? 15 : 5.5;
            if (keys.KeyW) my -= speed; if (keys.KeyS) my += speed;
            if (keys.KeyA) mx -= speed; if (keys.KeyD) mx += speed;
            if (mx !== 0 && my !== 0) { mx *= 0.707; my *= 0.707; }"""
mov_new = """            let mx = 0, my = 0;
            const speed = 5.5;
            
            if (me.dashCooldown > 0) me.dashCooldown--;
            if (keys.ShiftLeft && me.dashCooldown <= 0) {
                me.dashCooldown = 120;
                me.dashTimer = 10;
                me.dashAngle = Math.atan2(mouseY - canvas.height / 2, mouseX - canvas.width / 2);
            }

            if (me.dashTimer > 0) {
                mx = Math.cos(me.dashAngle) * 20;
                my = Math.sin(me.dashAngle) * 20;
                me.dashTimer--;
            } else {
                if (keys.KeyW) my -= speed; if (keys.KeyS) my += speed;
                if (keys.KeyA) mx -= speed; if (keys.KeyD) mx += speed;
                if (mx !== 0 && my !== 0) { mx *= 0.707; my *= 0.707; }
            }"""
html = html.replace(mov_old, mov_new)

# Shooting
shoot_old = """            const w = WEAPONS[me.weapon];
            if (keys.MouseDown && Date.now() - me.lastFired > w.fireRate && me.ammo[me.weapon] > 0) {
                me.lastFired = Date.now();
                if (w.ammo !== Infinity) me.ammo[me.weapon]--;
                me.shake = w.recoil * 2;
                updateAmmoDisplay();

                for (let i = 0; i < w.count; i++) {
                    const shot = { owner: myId, x: me.x, y: me.y, angle: me.angle + (Math.random() - 0.5) * w.spread, weapon: me.weapon };
                    push(ref(db, `v3/rooms/${currentRoomId}/shots`), shot);
                    createProjectile(shot, true);
                }
            }

            fbUpdate(ref(db, `v3/rooms/${currentRoomId}/players/${myId}`), { x: me.x, y: me.y, angle: me.angle, hp: me.hp, weapon: me.weapon });
            camera.x += (me.x - camera.x) * 0.1; camera.y += (me.y - camera.y) * 0.1;"""
shoot_new = """            const w = WEAPONS[me.weapon];
            
            if (me.reloading > 0) {
                me.reloading -= 16;
                if (me.reloading <= 0) {
                    me.clip[me.weapon] = w.clip;
                    updateAmmoDisplay();
                }
            } else if (keys.KeyR && me.clip[me.weapon] < w.clip && me.ammo[me.weapon] > 0) {
                me.reloading = w.reload;
                updateAmmoDisplay();
            } else if (keys.MouseDown && Date.now() - me.lastFired > w.fireRate && me.ammo[me.weapon] > 0 && me.clip[me.weapon] > 0) {
                me.lastFired = Date.now();
                if (w.ammo !== Infinity) me.ammo[me.weapon]--;
                me.clip[me.weapon]--;
                me.shake = w.recoil * 2;
                updateAmmoDisplay();

                for (let i = 0; i < w.count; i++) {
                    const shot = { owner: myId, x: me.x, y: me.y, angle: me.angle + (Math.random() - 0.5) * w.spread, weapon: me.weapon };
                    push(ref(db, `v3/rooms/${currentRoomId}/shots`), shot);
                    createProjectile(shot, true);
                }
                
                if (me.clip[me.weapon] === 0 && me.ammo[me.weapon] > 0) {
                    me.reloading = w.reload;
                    updateAmmoDisplay();
                }
            }

            if (keys.KeyG && me.grenades > 0 && Date.now() - (me.lastGrenade||0) > 2000) {
                me.grenades--;
                me.lastGrenade = Date.now();
                const shot = { owner: myId, x: me.x, y: me.y, angle: me.angle, weapon: 'grenade' };
                push(ref(db, `v3/rooms/${currentRoomId}/shots`), shot);
                createProjectile(shot, true);
                updateAmmoDisplay();
            }

            fbUpdate(ref(db, `v3/rooms/${currentRoomId}/players/${myId}`), { x: me.x, y: me.y, angle: me.angle, hp: me.hp, weapon: me.weapon });
            
            const lookX = me.x + (mouseX - canvas.width / 2) * 0.4;
            const lookY = me.y + (mouseY - canvas.height / 2) * 0.4;
            camera.x += (lookX - camera.x) * 0.1;
            camera.y += (lookY - camera.y) * 0.1;"""
html = html.replace(shoot_old, shoot_new)

# Grenade logic
proj_old = """            projectiles = projectiles.filter(p => {
                const w = WEAPONS[p.weapon];"""
proj_new = """            projectiles = projectiles.filter(p => {
                if (p.weapon === 'grenade') {
                    p.x += Math.cos(p.angle) * p.speed;
                    p.y += Math.sin(p.angle) * p.speed;
                    p.speed *= 0.95;
                    p.timer--;
                    
                    for (let o of obstacles) {
                        if (p.x > o.x && p.x < o.x + o.w && p.y > o.y && p.y < o.y + o.h) {
                            p.angle += Math.PI / 2;
                            p.x += Math.cos(p.angle) * p.speed * 2;
                            p.y += Math.sin(p.angle) * p.speed * 2;
                        }
                    }
                    
                    if (p.timer <= 0) {
                        createExplosion(p.x, p.y, 200);
                        if (p.local) {
                            for (let id in players) {
                                if (players[id].hp > 0) {
                                    const dist = Math.hypot(p.x - players[id].x, p.y - players[id].y);
                                    if (dist < 200) {
                                        const dmg = 150 * (1 - dist / 200);
                                        if (id !== myId) damage(id, dmg, p.x, p.y);
                                        else me.targetHp = Math.max(0, me.targetHp - dmg);
                                    }
                                }
                            }
                        }
                        return false;
                    }
                    return true;
                }
                const w = WEAPONS[p.weapon];"""
html = html.replace(proj_old, proj_new)

cp_old = """        function createProjectile(d, local) {
            const w = WEAPONS[d.weapon];
            projectiles.push({ ...d, speed: w.speed, damage: w.damage, local, dist: 0, color: w.color });
        }"""
cp_new = """        function createProjectile(d, local) {
            if (d.weapon === 'grenade') {
                projectiles.push({ ...d, speed: 12, timer: 120, local, color: '#10b981' });
                return;
            }
            const w = WEAPONS[d.weapon];
            projectiles.push({ ...d, speed: w.speed, damage: w.damage, local, dist: 0, color: w.color });
        }"""
html = html.replace(cp_old, cp_new)

# Laser logic
laser_old = "for (let id in players) if (players[id].hp > 0) drawSoldier(players[id], id === myId);"
laser_new = """for (let id in players) if (players[id].hp > 0) {
                drawSoldier(players[id], id === myId);
                const w = WEAPONS[players[id].weapon];
                if (w && w.laser) {
                    ctx.beginPath();
                    ctx.strokeStyle = 'rgba(239, 68, 68, 0.4)';
                    ctx.lineWidth = 1.5;
                    ctx.moveTo(players[id].x, players[id].y);
                    ctx.lineTo(players[id].x + Math.cos(players[id].angle) * 1500, players[id].y + Math.sin(players[id].angle) * 1500);
                    ctx.stroke();
                }
            }"""
html = html.replace(laser_old, laser_new)

# HUD Display
ammo_old = """        function updateAmmoDisplay() {
            const v = me.ammo[me.weapon];
            document.getElementById('ammo-val').innerText = v === Infinity ? '∞' : v;
        }"""
ammo_new = """        function updateAmmoDisplay() {
            const v = me.ammo[me.weapon];
            let txt = `${me.clip[me.weapon]} / ${v === Infinity ? '∞' : v}`;
            if (me.reloading > 0) txt = "RECARREGANDO...";
            document.getElementById('ammo-val').innerText = txt;
        }"""
html = html.replace(ammo_old, ammo_new)

# HUD html updates
hud_old = """<div class="hud-panel min-w-[80px] text-right flex flex-col justify-center">
                <div id="ammo-val" class="text-3xl font-black text-emerald-400 italic leading-none">∞</div>
            </div>"""
hud_new = """<div class="hud-panel min-w-[80px] text-right flex flex-col justify-center">
                <div id="ammo-val" class="text-2xl font-black text-emerald-400 italic leading-none whitespace-nowrap">12 / ∞</div>
                <div class="text-[10px] text-emerald-400/50 font-black mt-1 uppercase">Munição (R) | Granadas (G): <span id="grenade-val">3</span></div>
            </div>"""
html = html.replace(hud_old, hud_new)
html = html.replace("updateAmmoDisplay();\n        }", "updateAmmoDisplay();\n            document.getElementById('grenade-val').innerText = me.grenades;\n        }")

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Patch 1 applied!")