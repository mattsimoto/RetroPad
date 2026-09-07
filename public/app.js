let ws=null, room='', profiles=[], current=null, player=0, reconnectTimer=null;
const held=new Set(); const $=s=>document.querySelector(s);
function vibrate(){ if(navigator.vibrate) navigator.vibrate(7); }
function socketURL(){ return `${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws`; }
function send(obj){ if(ws?.readyState===1) ws.send(JSON.stringify(obj)); }
function emitButton(name,pressed){
  if(pressed===held.has(name)) return; pressed?held.add(name):held.delete(name); vibrate();
  send({type:'input', inputType:'button', profile:current?.id, button:name, pressed, t:performance.now()});
}
function bindButton(el){
  const name=el.dataset.btn; let activePointer=null;
  const down=e=>{e.preventDefault(); activePointer=e.pointerId; el.setPointerCapture?.(e.pointerId); el.classList.add('pressed'); emitButton(name,true)};
  const up=e=>{if(activePointer!==null && e.pointerId!==activePointer)return; e.preventDefault(); activePointer=null; el.classList.remove('pressed'); emitButton(name,false)};
  el.addEventListener('pointerdown',down,{passive:false}); el.addEventListener('pointerup',up,{passive:false}); el.addEventListener('pointercancel',up,{passive:false});
  el.addEventListener('lostpointercapture',()=>{ if(activePointer!==null){ activePointer=null; el.classList.remove('pressed'); emitButton(name,false); } });
}
function makeButton(name, cls=''){ const b=document.createElement('button'); b.textContent=name.replaceAll('_',' '); b.dataset.btn=name; b.className=[cls,`btn-${name.toLowerCase().replaceAll('_','-')}`].filter(Boolean).join(' '); bindButton(b); return b; }
function makeStick(id, label){
  const wrap=document.createElement('div'); wrap.className='stick-wrap inline-stick'; wrap.innerHTML=`<div class="stick-label">${label}</div><div id="${id}" class="stick"><div class="nub"></div></div>`; return wrap;
}
function bindStick(el, axis){
  const nub=el.querySelector('.nub'); let pointer=null, lastX=0, lastY=0;
  const update=e=>{
    const r=el.getBoundingClientRect(), cx=r.left+r.width/2, cy=r.top+r.height/2, rad=r.width*.36;
    let x=(e.clientX-cx)/rad, y=(e.clientY-cy)/rad; const mag=Math.hypot(x,y); if(mag>1){x/=mag;y/=mag;}
    const dead=.08; if(Math.abs(x)<dead)x=0;if(Math.abs(y)<dead)y=0;
    nub.style.transform=`translate(${x*rad}px,${y*rad}px)`;
    if(Math.abs(x-lastX)>.015||Math.abs(y-lastY)>.015){lastX=x;lastY=y;send({type:'input',inputType:'axis',profile:current?.id,axis,x:+x.toFixed(3),y:+y.toFixed(3),t:performance.now()});}
  };
  const release=e=>{if(pointer!==null && e.pointerId!==pointer)return; pointer=null; nub.style.transform='translate(0,0)';lastX=lastY=0;send({type:'input',inputType:'axis',profile:current?.id,axis,x:0,y:0,t:performance.now()});};
  el.addEventListener('pointerdown',e=>{e.preventDefault();pointer=e.pointerId;el.setPointerCapture?.(e.pointerId);update(e)},{passive:false});
  el.addEventListener('pointermove',e=>{if(pointer===e.pointerId)update(e)}); el.addEventListener('pointerup',release); el.addEventListener('pointercancel',release);
}
function render(p){
  current=p; localStorage.profile=p.id; document.body.dataset.profile=p.id; $('#face').innerHTML=''; p.face.forEach(x=>$('#face').append(makeButton(x)));
  $('#centerBtns').innerHTML=''; p.center.forEach(x=>$('#centerBtns').append(makeButton(x,'smallbtn')));
  $('#leftShoulders').innerHTML=''; $('#rightShoulders').innerHTML='';
  p.shoulders.forEach((x,i)=>(i<Math.ceil(p.shoulders.length/2)?$('#leftShoulders'):$('#rightShoulders')).append(makeButton(x,'shoulder')));
  const left=$('#leftControl'); left.innerHTML='';
  if(p.analog){ const s=makeStick('leftStick','L'); left.append(s); bindStick(s.querySelector('.stick'),'left'); }
  else { left.innerHTML='<div class="dpad"><button class="up" data-btn="UP">▲</button><button class="down" data-btn="DOWN">▼</button><button class="left" data-btn="LEFT">◀</button><button class="right" data-btn="RIGHT">▶</button></div>'; left.querySelectorAll('button').forEach(bindButton); }
  $('#rightStickWrap').classList.toggle('hidden',!p.dualAnalog); if(p.dualAnalog) bindStick($('#rightStick'),'right');
  send({type:'profile',profile:p.id});
}
function releaseAll(){ for(const b of [...held]) emitButton(b,false); }
function connect(code){
  room=code.toUpperCase().replace(/[^A-Z0-9]/g,'').slice(0,6); if(room.length!==6)return; localStorage.room=room;
  if(ws) try{ws.close()}catch{}; clearTimeout(reconnectTimer); ws=new WebSocket(socketURL());
  ws.onopen=()=>{send({type:'join',role:'controller',room,player:player||undefined,name:navigator.platform||'Phone'});$('#status').textContent='Pairing…';};
  ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.type==='joined'&&m.player){player=m.player;$('#playerBadge').textContent=`P${player}`;$('#join').classList.add('hidden');document.body.classList.add('paired');}
    if(m.type==='status') $('#status').textContent=m.receivers>0?'Connected':'Waiting for receiver';
    if(m.type==='error'){alert(m.message);$('#status').textContent='Pairing failed';$('#join').classList.remove('hidden');}};
  ws.onclose=()=>{releaseAll();$('#status').textContent='Disconnected'; if(!$('#join').classList.contains('hidden'))return; reconnectTimer=setTimeout(()=>connect(room),1000);};
}
fetch('/profiles.json').then(r=>r.json()).then(ps=>{profiles=ps;const sel=$('#profile');ps.forEach(p=>{const o=document.createElement('option');o.value=p.id;o.textContent=p.name;sel.append(o)});const id=localStorage.profile||'snes';sel.value=id;render(ps.find(p=>p.id===id)||ps[0]);sel.onchange=()=>render(ps.find(p=>p.id===sel.value));});
$('#joinBtn').onclick=()=>connect($('#room').value.trim()); $('#disconnect').onclick=()=>{document.body.classList.remove('paired');$('#join').classList.remove('hidden');if(ws)ws.close();}; $('#fullscreen').onclick=async()=>{try{if(!document.fullscreenElement)await document.documentElement.requestFullscreen();else await document.exitFullscreen();}catch{}}; $('#room').value=new URLSearchParams(location.search).get('room')||localStorage.room||'';
document.addEventListener('contextmenu',e=>e.preventDefault()); document.addEventListener('visibilitychange',()=>{if(document.hidden)releaseAll()});
window.addEventListener('blur',releaseAll); if('serviceWorker'in navigator)navigator.serviceWorker.register('/sw.js').catch(()=>{});
if($('#room').value.length===6 && new URLSearchParams(location.search).has('room')) connect($('#room').value);
