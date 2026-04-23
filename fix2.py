import re

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. Fix onChildAdded for shots so host ignores their own bot shots
sh_old = """            onChildAdded(ref(db, `v3/rooms/${currentRoomId}/shots`), (snap) => {
                const s = snap.val();
                if (s && s.owner !== myId) createProjectile(s, false);
                remove(ref(db, `v3/rooms/${currentRoomId}/shots/${snap.key}`));
            });"""
sh_new = """            onChildAdded(ref(db, `v3/rooms/${currentRoomId}/shots`), (snap) => {
                const s = snap.val();
                if (s && s.owner !== myId) {
                    const amIHost = (Object.keys(players).sort()[0] === myId);
                    const isMyBotShot = amIHost && s.owner.startsWith('BOT_');
                    if (!isMyBotShot) createProjectile(s, false);
                }
                remove(ref(db, `v3/rooms/${currentRoomId}/shots/${snap.key}`));
            });"""
html = html.replace(sh_old, sh_new)

# 2. Add global HP update loop for bots to actually take damage and die
hp_old = """            if (me.hp > me.targetHp) {
                me.hp -= 0.5;
                if (me.hp <= me.targetHp) me.hp = me.targetHp;
                updateHUD(); // smooth update locally
            } else if (me.hp < me.targetHp) {
                me.hp = me.targetHp;
            }"""
hp_new = """            if (me.hp > me.targetHp) {
                me.hp -= 0.5;
                if (me.hp <= me.targetHp) me.hp = me.targetHp;
                updateHUD(); // smooth update locally
            } else if (me.hp < me.targetHp) {
                me.hp = me.targetHp;
            }
            
            for (let id in players) {
                if (players[id].targetHp !== undefined) {
                    if (players[id].hp > players[id].targetHp) players[id].hp -= 0.5;
                    else if (players[id].hp < players[id].targetHp) players[id].hp = players[id].targetHp;
                }
            }"""
html = html.replace(hp_old, hp_new)

# 3. Improve AI logic and create bot projectiles locally
ai_old = """                        if (nearest) {
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
                        }"""
ai_new = """                        if (nearest) {
                            let ang = Math.atan2(nearest.y - p.y, nearest.x - p.x);
                            
                            if (p.strafeDir === undefined || Math.random() < 0.02) {
                                p.strafeDir = (Math.random() > 0.5 ? 1 : -1) * (Math.PI / 2.5);
                            }
                            
                            let moveAng = ang;
                            if (minDist < 300) moveAng = ang + p.strafeDir;
                            else if (minDist < 150) moveAng = ang + Math.PI;
                            
                            let nx = p.x + Math.cos(moveAng) * 4.5;
                            let ny = p.y + Math.sin(moveAng) * 4.5;
                            let cx = false, cy = false;
                            obstacles.forEach(o => {
                                if (checkCol(o, nx, p.y)) cx = true;
                                if (checkCol(o, p.x, ny)) cy = true;
                            });
                            if (!cx) p.x = nx; else p.y += (Math.random()-0.5)*15;
                            if (!cy) p.y = ny; else p.x += (Math.random()-0.5)*15;
                            
                            p.angle = ang;
                            if (minDist < 600 && Math.random() < 0.06) {
                                const shot = { owner: id, x: p.x, y: p.y, angle: p.angle + (Math.random()-0.5)*0.3, weapon: p.weapon };
                                push(ref(db, `v3/rooms/${currentRoomId}/shots`), shot);
                                createProjectile(shot, true); // Host generates damage for bots
                            }
                            fbUpdate(ref(db, `v3/rooms/${currentRoomId}/players/${id}`), { x: p.x, y: p.y, angle: p.angle });
                        }"""
html = html.replace(ai_old, ai_new)

# 4. Fix Projectile hit logic for remote players
hit_old = """                let hitPlayer = false;
                if (p.local) {
                    for (let id in players) {
                        if (id !== myId && players[id].hp > 0 && Math.hypot(p.x - players[id].x, p.y - players[id].y) < 30) {
                            hitPlayer = true;
                            if (!w.isAoE) {
                                damage(id, p.damage, me.x, me.y);
                                return false;
                            }
                        }
                    }
                }"""
hit_new = """                let hitPlayer = false;
                for (let id in players) {
                    if (id !== p.owner && players[id].hp > 0 && Math.hypot(p.x - players[id].x, p.y - players[id].y) < 30) {
                        hitPlayer = true;
                        if (!w.isAoE) {
                            if (p.local) damage(id, p.damage, p.x, p.y);
                            return false;
                        }
                    }
                }"""
html = html.replace(hit_old, hit_new)

# 5. Fix AoE (Grenades) hit logic
aoe_old = """                        if (p.local) {
                            for (let id in players) {
                                if (players[id].hp > 0) {
                                    const dist = Math.hypot(p.x - players[id].x, p.y - players[id].y);
                                    if (dist < 150) {
                                        const dmg = p.damage * (1 - dist / 150);
                                        if (id !== myId) damage(id, dmg, me.x, me.y);
                                        else me.targetHp = Math.max(0, me.targetHp - dmg); // Self damage
                                    }
                                }
                            }
                        }"""
aoe_new = """                        if (p.local) {
                            for (let id in players) {
                                if (players[id].hp > 0) {
                                    const dist = Math.hypot(p.x - players[id].x, p.y - players[id].y);
                                    if (dist < 150) {
                                        const dmg = p.damage * (1 - dist / 150);
                                        if (id !== p.owner) damage(id, dmg, p.x, p.y);
                                        else if (p.owner === myId) me.targetHp = Math.max(0, me.targetHp - dmg);
                                    }
                                }
                            }
                        }"""
html = html.replace(aoe_old, aoe_new)

gren_aoe_old = """                        if (p.local) {
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
                        }"""
gren_aoe_new = """                        if (p.local) {
                            for (let id in players) {
                                if (players[id].hp > 0) {
                                    const dist = Math.hypot(p.x - players[id].x, p.y - players[id].y);
                                    if (dist < 200) {
                                        const dmg = 150 * (1 - dist / 200);
                                        if (id !== p.owner) damage(id, dmg, p.x, p.y);
                                        else if (p.owner === myId) me.targetHp = Math.max(0, me.targetHp - dmg);
                                    }
                                }
                            }
                        }"""
html = html.replace(gren_aoe_old, gren_aoe_new)

# 6. Remove Snow
snow_old = """            // Weather (Snow)
            ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
            for (let i = 0; i < 200; i++) {
                ctx.fillRect(camera.x - canvas.width/2 + Math.random()*canvas.width, camera.y - canvas.height/2 + ((Date.now()/10 + i*100) % canvas.height), 2, 2);
            }"""
html = html.replace(snow_old, "")

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Fix 2 applied")
