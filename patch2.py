import re

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Bushes and Blood arrays
html = html.replace("let players = {}, projectiles = [], particles = [], obstacles = [], items = {}, explosions = [];",
                    "let players = {}, projectiles = [], particles = [], obstacles = [], items = {}, explosions = [], bushes = [], blood = [];")

# Add to draw
draw_old = """            ctx.fillStyle = '#1e293b'; obstacles.forEach(o => ctx.fillRect(o.x, o.y, o.w, o.h));"""
draw_new = """            ctx.fillStyle = '#1e293b'; obstacles.forEach(o => ctx.fillRect(o.x, o.y, o.w, o.h));
            ctx.fillStyle = 'rgba(34, 197, 94, 0.3)'; bushes.forEach(b => ctx.fillRect(b.x, b.y, b.w, b.h));
            ctx.fillStyle = 'rgba(185, 28, 28, 0.6)'; blood.forEach(b => { ctx.beginPath(); ctx.arc(b.x, b.y, 10, 0, Math.PI*2); ctx.fill(); });
"""
html = html.replace(draw_old, draw_new)

# Generate bushes
gen_old = """        function generateObstacles(seedStr) {
            obstacles = [];
            const rnd = mulberry32(hashCode(seedStr || "default"));
            for (let i = 0; i < 30; i++) {
                obstacles.push({ 
                    x: (rnd() - 0.5) * MAP_SIZE * 1.8, 
                    y: (rnd() - 0.5) * MAP_SIZE * 1.8, 
                    w: 80 + rnd() * 100, 
                    h: 80 + rnd() * 100 
                });
            }
        }"""
gen_new = """        function generateObstacles(seedStr) {
            obstacles = []; bushes = [];
            const rnd = mulberry32(hashCode(seedStr || "default"));
            for (let i = 0; i < 30; i++) {
                obstacles.push({ x: (rnd() - 0.5) * MAP_SIZE * 1.8, y: (rnd() - 0.5) * MAP_SIZE * 1.8, w: 80 + rnd() * 100, h: 80 + rnd() * 100 });
            }
            for (let i = 0; i < 20; i++) {
                bushes.push({ x: (rnd() - 0.5) * MAP_SIZE * 1.8, y: (rnd() - 0.5) * MAP_SIZE * 1.8, w: 120 + rnd() * 100, h: 120 + rnd() * 100 });
            }
        }"""
html = html.replace(gen_old, gen_new)

# Blood in damage
dmg_old = "const newTarget = Math.max(0, currentTarget - dmg);"
dmg_new = """const newTarget = Math.max(0, currentTarget - dmg);
                push(ref(db, `v3/rooms/${currentRoomId}/blood`), {x: p.x, y: p.y});"""
html = html.replace(dmg_old, dmg_new)

# Listen to blood
net_old = """            onChildAdded(ref(db, `v3/rooms/${currentRoomId}/shots`), (snap) => {
                const s = snap.val();
                if (s && s.owner !== myId) createProjectile(s, false);
                remove(ref(db, `v3/rooms/${currentRoomId}/shots/${snap.key}`));
            });"""
net_new = """            onChildAdded(ref(db, `v3/rooms/${currentRoomId}/shots`), (snap) => {
                const s = snap.val();
                if (s && s.owner !== myId) createProjectile(s, false);
                remove(ref(db, `v3/rooms/${currentRoomId}/shots/${snap.key}`));
            });
            onChildAdded(ref(db, `v3/rooms/${currentRoomId}/blood`), (snap) => {
                blood.push(snap.val());
            });"""
html = html.replace(net_old, net_new)

# Draw soldier opacity
sol_old = "ctx.save(); ctx.translate(p.x, p.y);"
sol_new = "ctx.save(); ctx.translate(p.x, p.y); if (p.inBush && !isMe) ctx.globalAlpha = 0.2;"
html = html.replace(sol_old, sol_new)

# Check bush state
shoot_up_old = "fbUpdate(ref(db, `v3/rooms/${currentRoomId}/players/${myId}`), { x: me.x, y: me.y, angle: me.angle, hp: me.hp, weapon: me.weapon });"
shoot_up_new = """            let inBush = false;
            for (let b of bushes) if (me.x > b.x && me.x < b.x+b.w && me.y > b.y && me.y < b.y+b.h) inBush = true;
            fbUpdate(ref(db, `v3/rooms/${currentRoomId}/players/${myId}`), { x: me.x, y: me.y, angle: me.angle, hp: me.hp, weapon: me.weapon, inBush });"""
html = html.replace(shoot_up_old, shoot_up_new)

# Gas zone + Minimap
draw_end_old = """            explosions = explosions.filter(e => {
                e.r += 10;
                e.alpha -= 0.05;
                if (e.alpha <= 0) return false;
                ctx.beginPath();
                ctx.arc(e.x, e.y, e.r, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(251, 191, 36, ${e.alpha})`; // color matching bazooka
                ctx.fill();
                return true;
            });

            ctx.restore();
        }"""
draw_end_new = """            explosions = explosions.filter(e => {
                e.r += 10;
                e.alpha -= 0.05;
                if (e.alpha <= 0) return false;
                ctx.beginPath();
                ctx.arc(e.x, e.y, e.r, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(251, 191, 36, ${e.alpha})`;
                ctx.fill();
                return true;
            });
            
            // Draw Zone
            let zoneRadius = MAP_SIZE * 2;
            if (roomStartTime) {
                const elapsed = Date.now() - roomStartTime;
                zoneRadius = Math.max(200, MAP_SIZE * 1.5 - (elapsed / 1000) * 2);
                ctx.beginPath();
                ctx.arc(0, 0, zoneRadius, 0, Math.PI * 2);
                ctx.strokeStyle = '#ef4444'; ctx.lineWidth = 10; ctx.stroke();
                ctx.fillStyle = 'rgba(239, 68, 68, 0.1)';
                ctx.fillRect(-MAP_SIZE*2, -MAP_SIZE*2, MAP_SIZE*4, MAP_SIZE*4);
                ctx.globalCompositeOperation = 'destination-out';
                ctx.fill();
                ctx.globalCompositeOperation = 'source-over';
                
                if (active && Math.hypot(me.x, me.y) > zoneRadius && Math.random() < 0.1) {
                    me.targetHp -= 1; // Gas damage
                }
            }
            
            // Weather (Snow)
            ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
            for (let i = 0; i < 200; i++) {
                ctx.fillRect(camera.x - canvas.width/2 + Math.random()*canvas.width, camera.y - canvas.height/2 + ((Date.now()/10 + i*100) % canvas.height), 2, 2);
            }

            ctx.restore();
            
            // Draw Minimap
            ctx.save();
            ctx.translate(canvas.width - 170, 20);
            ctx.fillStyle = 'rgba(15, 23, 42, 0.8)';
            ctx.fillRect(0, 0, 150, 150);
            ctx.strokeStyle = '#10b981'; ctx.strokeRect(0, 0, 150, 150);
            ctx.scale(150 / (MAP_SIZE * 2), 150 / (MAP_SIZE * 2));
            ctx.translate(MAP_SIZE, MAP_SIZE);
            ctx.fillStyle = '#475569';
            obstacles.forEach(o => ctx.fillRect(o.x, o.y, o.w, o.h));
            ctx.fillStyle = '#10b981';
            ctx.fillRect(me.x - 50, me.y - 50, 100, 100);
            for (let id in players) {
                if (id !== myId && players[id].hp > 0 && !players[id].inBush) {
                    ctx.fillStyle = '#ef4444';
                    ctx.fillRect(players[id].x - 50, players[id].y - 50, 100, 100);
                }
            }
            if (zoneRadius < MAP_SIZE*2) {
                ctx.beginPath(); ctx.arc(0, 0, zoneRadius, 0, Math.PI*2);
                ctx.strokeStyle = '#ef4444'; ctx.lineWidth = 40; ctx.stroke();
            }
            ctx.restore();
        }"""
html = html.replace(draw_end_old, draw_end_new)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Patch 2 applied!")
