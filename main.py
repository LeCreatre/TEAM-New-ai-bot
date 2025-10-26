<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no"/>
<title>TEAMmy's Run</title>
<meta name="theme-color" content="#132766">
<style>
  :root{ --blue:#132766; --red:#C9301F; --bg1:#F6F7FB; --bg2:#EAEFFC; --ink:#101225; }
  *{box-sizing:border-box}
  html,body{height:100%;margin:0;background:linear-gradient(180deg,var(--bg1),var(--bg2));
    color:var(--ink);font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,Arial;}
  body{overscroll-behavior:none}
  .wrap{position:fixed;inset:0;display:grid;place-items:center}
  canvas{width:100vw;height:100vh;display:block;touch-action:manipulation;background:transparent}
  .hud{position:fixed;left:12px;top:12px;display:flex;gap:10px;z-index:3}
  .card{background:#fff;padding:10px 14px;border-radius:14px;
    box-shadow:0 6px 24px rgba(0,0,0,.08),0 2px 6px rgba(0,0,0,.06);
    font-weight:700;font-size:14px;letter-spacing:.2px;color:var(--blue);display:flex;align-items:center;gap:8px}
  .card .val{color:var(--ink);min-width:64px;text-align:right;font-variant-numeric:tabular-nums}
  .overlay{position:fixed;inset:0;display:grid;place-items:center;z-index:4}
  .panel{width:min(92vw,560px);background:#fff;border-radius:20px;padding:22px 22px;
    box-shadow:0 20px 60px rgba(19,39,102,.25),0 2px 10px rgba(0,0,0,.08);text-align:center}
  .title{font-weight:900;font-size:28px;color:var(--blue);margin:4px 0 6px}
  .subtitle{opacity:.85;margin:0 0 14px;font-size:14px;line-height:1.35}
  .kbd{display:inline-block;padding:3px 8px;border-radius:8px;background:#F3F4F8;border:1px solid #E6E8F2;font-weight:700}
  .btn{margin-top:12px;background:linear-gradient(180deg,#fff,#F6F8FF);border:1px solid #E5E8F5;
    padding:10px 14px;border-radius:14px;cursor:pointer;font-weight:800;color:var(--blue);
    display:inline-flex;gap:8px;align-items:center;box-shadow:0 6px 18px rgba(19,39,102,.12)}
  .btn:active{transform:translateY(1px)}
  .badge{font-size:12px;font-weight:800;color:#fff;background:var(--red);padding:4px 8px;border-radius:999px}
  .foot{margin-top:10px;font-size:12px;opacity:.7}
  .muted{opacity:.7}
</style>
</head>
<body>
  <div class="hud" aria-hidden="true">
    <div class="card">Счёт: <span id="score" class="val">0</span></div>
    <div class="card">Рекорд: <span id="best" class="val">0</span></div>
  </div>

  <div class="overlay" id="overlay">
    <div class="panel" id="panel">
      <div class="badge">Новая игра</div>
      <div class="title">TEAMmy’s Run</div>
      <p class="subtitle">Прыгай маскотом через препятствия и беги как можно дольше!<br>
        Управление: <span class="kbd">Пробел</span> или <span class="kbd">Тап</span>.</p>
      <button class="btn" id="startBtn">Старт</button>
      <div class="foot muted">Цвета: <b style="color:#132766">#132766</b> • <b style="color:#C9301F">#C9301F</b></div>
    </div>
  </div>

  <div class="wrap"><canvas id="game" aria-label="Полотно игры"></canvas></div>

<script>
/* ===========================
   TEAMmy’s Run — single-file
   одинаковая сложность на всех устройствах, спрайт mascot.png
   =========================== */

// ----- Canvas & DPI: физика в CSS-пикселях, рендер масштабируем по DPR -----
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
let DPR = Math.max(1, Math.min(3, window.devicePixelRatio || 1));
let W = innerWidth, H = innerHeight;  // логические размеры для физики

function resize(){
  DPR = Math.max(1, Math.min(3, window.devicePixelRatio || 1));
  W = innerWidth; H = innerHeight;
  canvas.width  = Math.floor(W * DPR);
  canvas.height = Math.floor(H * DPR);
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0); // всё рисуем в CSS-пикселях
}
addEventListener('resize', resize, {passive:true});
resize();

// ----- UI -----
const overlay = document.getElementById('overlay');
const startBtn = document.getElementById('startBtn');
const scoreEl = document.getElementById('score');
const bestEl  = document.getElementById('best');
const BEST_KEY = 'teammy_best';
let best = +localStorage.getItem(BEST_KEY) || 0;
bestEl.textContent = best;

// ----- WebAudio SFX -----
let audioCtx;
function ensureAudio(){ if(!audioCtx){ audioCtx = new (window.AudioContext||window.webkitAudioContext)(); } }
function beep({type='sine',freq=600,dur=0.1,vol=0.22,attack=0.005,decay=0.06}={}){
  if(!audioCtx) return;
  const o=audioCtx.createOscillator(), g=audioCtx.createGain();
  o.type=type; o.frequency.value=freq; g.gain.value=0;
  o.connect(g); g.connect(audioCtx.destination);
  const t=audioCtx.currentTime;
  g.gain.linearRampToValueAtTime(vol,t+attack);
  g.gain.exponentialRampToValueAtTime(0.0001,t+Math.max(dur,attack+decay));
  o.start(t); o.stop(t+dur);
}
function noise(d=0.12,v=0.25){
  if(!audioCtx) return;
  const b=audioCtx.createBuffer(1, d*audioCtx.sampleRate*2, audioCtx.sampleRate);
  const data=b.getChannelData(0); for(let i=0;i<data.length;i++) data[i]=(Math.random()*2-1)*0.6;
  const s=audioCtx.createBufferSource(); s.buffer=b;
  const g=audioCtx.createGain(); g.gain.value=v; s.connect(g); g.connect(audioCtx.destination);
  const t=audioCtx.currentTime; s.start(t); g.gain.exponentialRampToValueAtTime(0.0001,t+d);
}
const sfx={ jump(){beep({type:'triangle',freq:720,dur:0.12,vol:0.28});},
            step(){beep({type:'square',freq:220,dur:0.04,vol:0.12});},
            milestone(){beep({type:'sine',freq:880,dur:0.08,vol:0.22}); setTimeout(()=>beep({type:'sine',freq:1175,dur:0.08,vol:0.22}),70);},
            crash(){noise(0.18,0.35); beep({type:'sawtooth',freq:140,dur:0.15,vol:0.25});} };

// ----- Game state -----
const G={ running:false, gameOver:false, t:0,
  speed:7, gravity:2000, groundH:120,
  score:0, milestoneStep:100, nextMilestone:100,
  spawnMin:0.9, spawnMax:1.8, lastSpawn:0, rng:(Math.random()*1e9)|0
};
function xr(){ let x=G.rng^=G.rng<<13; x^=x>>>17; x^=x<<5; return (x>>>0)/4294967295; }

// ----- Player -----
const player={ x:160, y:0, vy:0, w:64, h:64, onGround:true, legT:0,
  cBody:'#132766', cAcc:'#C9301F' };

// ===== МАСКОТ (PNG-спрайт) =====
const MASCOT_IMG = new Image();
MASCOT_IMG.src = 'mascot.png';   // файл рядом с index.html
let mascotReady = false;
MASCOT_IMG.onload = ()=>{ mascotReady = true; };
// подгон хитбокса под картинку (можно поменять после визуальной проверки)
player.w = 90; player.h = 100;

// ----- Obstacles -----
const obstacles=[];
function spawnObstacle(){
  const type = xr()<0.5 ? 'cone' : (xr()<0.5 ? 'backpack' : 'barrier');
  const baseH = (type==='cone')? 40 : (type==='backpack'? 50 : 45);
  const baseW = (type==='cone')? 36 : (type==='backpack'? 40 : 72);
  const y = H - G.groundH - baseH;
  const x = W + 40;
  obstacles.push({x,y,w:baseW,h:baseH,type,passed:false});
}

// ----- Input -----
let wantJump=false;
function queueJump(){ wantJump=true; }
addEventListener('keydown', e=>{
  if(e.code==='Space'){ e.preventDefault(); ensureAudio(); if(!G.running) start(); else queueJump(); }
},{passive:false});
addEventListener('pointerdown', ()=>{ ensureAudio(); if(!G.running) start(); else queueJump(); },{passive:true});

// ----- Start / Reset -----
startBtn.addEventListener('click', ()=>{ ensureAudio(); start(); });
function reset(){
  G.running=false; G.gameOver=false; G.t=0;
  G.speed=7; G.score=0; G.nextMilestone=G.milestoneStep; G.lastSpawn=0; obstacles.length=0;
  player.y = H - G.groundH - player.h; player.vy=0; player.onGround=true; player.legT=0;
}
function start(){ overlay.style.display='none'; reset(); G.running=true; }

// ----- Update -----
let lastTS=0;
function update(dt){
  // растущая сложность (одинаково на всех устройствах)
  G.speed = 7 + Math.min(18, G.score*0.006);
  const world = G.speed * 100; // px/s

  // спавн препятствий
  G.lastSpawn -= dt;
  if(G.lastSpawn<=0){
    spawnObstacle();
    const gap = G.spawnMin + xr()*(G.spawnMax-G.spawnMin);
    const tight = Math.min(0.55, G.score/2000);
    G.lastSpawn = (gap - tight) / (G.speed/7);
  }

  // движение препятствий
  for(const o of obstacles){
    o.x -= world*dt;
    if(!o.passed && (o.x + o.w) < player.x){ o.passed=true; G.score+=10; if((G.score/10)%4===0) sfx.step(); }
  }
  while(obstacles.length && obstacles[0].x + obstacles[0].w < -50) obstacles.shift();

  // прыжок
  if(wantJump && player.onGround){ player.vy = -Math.max(820, 740 + G.speed*8); player.onGround=false; sfx.jump(); }
  wantJump=false;

  // гравитация
  if(!player.onGround){
    player.vy += G.gravity*dt; player.y += player.vy*dt;
    const floor = H - G.groundH - player.h;
    if(player.y>=floor){ player.y=floor; player.vy=0; player.onGround=true; }
  }

  // беговая анимация
  player.legT += dt*(player.onGround? (8 + G.speed*0.25) : 0);

  // столкновения (чуть «добрый» хитбокс)
  for(const o of obstacles){
    const inset=10;
    const ax=player.x+inset, ay=player.y+inset, aw=player.w-2*inset, ah=player.h-2*inset;
    const bx=o.x+inset, by=o.y+inset, bw=o.w-2*inset, bh=o.h-2*inset;
    if(ax<bx+bw && ax+aw>bx && ay<by+bh && ay+ah>by){ end(); break; }
  }

  if(G.score>=G.nextMilestone){ sfx.milestone(); G.nextMilestone+=G.milestoneStep; }
}

// ----- End & overlay -----
function end(){
  if(G.gameOver) return;
  G.gameOver=true; G.running=false; sfx.crash();
  let isNew=false; if(G.score>best){ best=G.score; isNew=true; localStorage.setItem(BEST_KEY,best); }
  bestEl.textContent=best;

  const p=document.getElementById('panel');
  p.innerHTML=`
    <div class="badge">${isNew?'Новый рекорд!':'Игра окончена'}</div>
    <div class="title">Счёт: ${G.score}</div>
    <p class="subtitle">Рекорд: <b>${best}</b><br>
      Нажмите <span class="kbd">Пробел</span> или <span class="kbd">Тап</span>, чтобы сыграть снова.</p>
    <button class="btn" id="againBtn">Сыграть ещё</button>
    <div class="foot muted">Подсказка: скорость растёт — подбирай тайминг прыжка.</div>
  `;
  overlay.style.display='grid';
  document.getElementById('againBtn').addEventListener('click', ()=>{ ensureAudio(); start(); });

  // если открыто как Telegram Mini App — отправим результат
  try{ if(window.Telegram && Telegram.WebApp){
    Telegram.WebApp.sendData(JSON.stringify({score:G.score, ts:Date.now()}));
    // Telegram.WebApp.close(); // можно закрыть по желанию
  } }catch(_){}
}

// ----- Draw helpers -----
function rr(x,y,w,h,r,fill=true){
  ctx.beginPath();
  ctx.moveTo(x+r,y); ctx.arcTo(x+w,y,x+w,y+h,r); ctx.arcTo(x+w,y+h,x,y+h,r);
  ctx.arcTo(x,y+h,x,y,r); ctx.arcTo(x,y,x+w,y,r); if(fill) ctx.fill(); else ctx.stroke();
}
function drawObstacle(o){
  if(o.type==='cone'){
    ctx.save(); ctx.translate(o.x,o.y);
    ctx.fillStyle='#C9301F'; ctx.beginPath();
    ctx.moveTo(0.1*o.w,o.h); ctx.lineTo(0.5*o.w,0); ctx.lineTo(0.9*o.w,o.h); ctx.closePath(); ctx.fill();
    ctx.fillStyle='#fff'; ctx.fillRect(0.28*o.w,0.45*o.h,0.44*o.w,0.12*o.h); ctx.fillRect(0.22*o.w,0.70*o.h,0.56*o.w,0.12*o.h);
    ctx.fillStyle='rgba(0,0,0,.25)'; ctx.fillRect(-0.05*o.w,o.h,1.1*o.w,0.08*o.h); ctx.restore();
  } else if(o.type==='backpack'){
    ctx.save(); ctx.translate(o.x,o.y);
    ctx.fillStyle='#132766'; rr(0,0.1*o.h,o.w,0.9*o.h,8,true);
    ctx.fillStyle='#1c3a95'; rr(0.18*o.w,0.55*o.h,0.64*o.w,0.34*o.h,6,true);
    ctx.strokeStyle='#1c3a95'; ctx.lineWidth=6;
    ctx.beginPath(); ctx.moveTo(0.3*o.w,0.1*o.h); ctx.bezierCurveTo(0.5*o.w,-0.18*o.h,0.5*o.w,-0.18*o.h,0.7*o.w,0.1*o.h); ctx.stroke();
    ctx.restore();
  } else {
    ctx.save(); ctx.translate(o.x,o.y);
    ctx.fillStyle='#C9301F'; rr(0,0,o.w,o.h*0.7,8,true);
    ctx.fillStyle='#fff'; for(let i=0;i<5;i++) ctx.fillRect(0.06*o.w+i*0.18*o.w,0.18*o.h,0.10*o.w,0.18*o.h);
    ctx.fillStyle='rgba(0,0,0,.25)'; ctx.fillRect(0.08*o.w,0.7*o.h,0.14*o.w,0.12*o.h); ctx.fillRect(0.78*o.w,0.7*o.h,0.14*o.w,0.12*o.h);
    ctx.restore();
  }
}
const MASCOT_IMG = new Image();
MASCOT_IMG.src = mascot.png
// ----- Mascot draw -----
function drawMascot(x, y, legT, isJump){
  // тень
  const shadowY = H - G.groundH - 6;
  const k = isJump ? 0.65 : 1.0;
  ctx.fillStyle='rgba(0,0,0,0.14)'; ctx.beginPath();
  ctx.ellipse(x + player.w*0.25, shadowY, 28*k, 6*k, 0, 0, Math.PI*2); ctx.fill();

  // лёгкая «болтанка»
  const bob = isJump ? -4 : Math.sin(legT*6)*1.2;

  if(mascotReady){
    const drawW = player.w, drawH = player.h + 20;
    const dx = x - 10, dy = y - (drawH - player.h) + bob;
    ctx.drawImage(MASCOT_IMG, dx, dy, drawW, drawH);
  }else{
    ctx.fillStyle='#132766'; ctx.fillRect(x, y, player.w, player.h); // заглушка
  }
}

// ----- Background -----
function drawClouds(){
  const t=G.t*0.03, w=W, h=H, base=h*0.18;
  function cloud(x,y,wx,hy){ ctx.save(); ctx.fillStyle='rgba(255,255,255,0.92)'; ctx.beginPath();
    ctx.ellipse(x,y,wx,hy,0,0,Math.PI*2); ctx.ellipse(x-wx*0.5,y+hy*0.1,wx*0.5,hy*0.7,0,0,Math.PI*2);
    ctx.ellipse(x+wx*0.4,y+hy*0.05,wx*0.6,hy*0.8,0,0,Math.PI*2); ctx.fill(); ctx.restore(); }
  for(let i=0;i<4;i++){ const sp=(20+i*8), x=(w-((G.t*sp)%w))+i*w*0.25, y=base+Math.sin(t+i)*22;
    cloud(x,y,120,28); cloud(x-w*0.5,y+6,150,32); }
}
function drawCity(){
  const w=W, h=H, y=h*0.62, sp=40, off=(G.t*sp)%w;
  ctx.save(); ctx.translate(-off,0); for(let x=0;x<w*2;x+=160) cityBlock(x,y); ctx.restore();
  function cityBlock(x,y){ ctx.fillStyle='rgba(19,39,102,0.12)';
    const hs=[80,110,95,130,75,100,85];
    for(let i=0;i<hs.length;i++){ const bw=50,bh=hs[i]; ctx.fillRect(x+i*bw*0.9, y-bh, bw, bh); } }
}
function drawCampus(){
  const w=W, h=H, y=h*0.70, sp=80, off=(G.t*sp)%w;
  ctx.save(); ctx.translate(-off,0); for(let x=0;x<w*2;x+=220) campus(x,y); ctx.restore();
  function campus(x,y){ ctx.fillStyle='rgba(19,39,102,0.25)'; const bw=120,bh=80; ctx.fillRect(x,y-bh,bw,bh);
    ctx.fillStyle='rgba(255,255,255,0.75)'; for(let r=0;r<2;r++) for(let c=0;c<4;c++)
      ctx.fillRect(x+12+c*26, y-bh+12+r*28, 18, 16);
    ctx.fillStyle='#C9301F'; ctx.fillRect(x+bw*0.66, y-bh-10, 10, 30); }
}
function drawGround(){
  const w=W, h=H, gh=G.groundH;
  ctx.fillStyle='rgba(83,174,122,0.38)'; ctx.fillRect(0,h-gh-8,w,12);
  ctx.fillStyle='rgba(19,39,102,0.08)'; ctx.fillRect(0,h-gh,w,gh);
  const sp=160, off=(G.t*sp)%(40);
  ctx.strokeStyle='rgba(19,39,102,0.22)'; ctx.lineWidth=4; ctx.setLineDash([28,22]); ctx.lineDashOffset=-off;
  ctx.beginPath(); ctx.moveTo(0,h-gh+24); ctx.lineTo(w,h-gh+24); ctx.stroke(); ctx.setLineDash([]);
}

// ----- Frame loop -----
function draw(){
  ctx.clearRect(0,0,W,H);
  drawClouds(); drawCity(); drawCampus(); drawGround();
  for(const o of obstacles) drawObstacle(o);
  drawMascot(player.x, player.y, player.legT, !player.onGround);
  // ghost HUD
  ctx.save(); ctx.globalAlpha=0.06; ctx.fillStyle='#000'; ctx.font = `36px sans-serif`; ctx.textAlign='right';
  ctx.fillText(G.score.toString().padStart(2,'0'), W-24, 48); ctx.restore();
}
function loop(ts){
  if(!lastTS) lastTS=ts;
  const dt=Math.min(0.033,(ts-lastTS)/1000); lastTS=ts;
  if(G.running && !G.gameOver){
    G.t+=dt; update(dt); draw(); G.score += Math.floor(40*dt); scoreEl.textContent=G.score.toString();
  }else{ G.t+=dt*0.6; draw(); }
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);

// ----- Instant restart from overlay -----
addEventListener('keydown', e=>{ if(e.code==='Space' && !G.running){ e.preventDefault(); ensureAudio(); start(); }},{passive:false});
addEventListener('pointerdown', ()=>{ if(!G.running){ ensureAudio(); start(); }},{passive:true});

// ----- Telegram Mini App nicety -----
try{ if(window.Telegram && Telegram.WebApp){ Telegram.WebApp.expand(); } }catch(_){}
</script>
</body>
</html>
