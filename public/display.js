let ws=null,pc=null,room='';
const $=s=>document.querySelector(s);
const stage=$('#stage'),video=$('#game'),status=$('#status'),code=$('#code'),qr=$('#qr');
function wsURL(){return `${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws`;}
function send(obj){if(ws?.readyState===1)ws.send(JSON.stringify(obj));}
async function makeRoom(){
  if(ws)try{ws.close()}catch{}
  if(pc){try{pc.close()}catch{};pc=null}
  stage.classList.remove('connected');video.srcObject=null;
  const r=await fetch('/api/new-room',{cache:'no-store'}).then(x=>x.json());room=r.room;code.textContent=room;
  const info=await fetch('/api/info',{cache:'no-store'}).then(x=>x.json());
  const host=(info.ips&&info.ips[0])||location.hostname;
  const pair=`retropad://pair?host=${encodeURIComponent(host)}&port=${encodeURIComponent(info.port)}&room=${encodeURIComponent(room)}`;
  qr.src=`/api/qr?text=${encodeURIComponent(pair)}`;status.textContent='Waiting for Android phone…';
  connectSignal();
}
function connectSignal(){
  ws=new WebSocket(wsURL());
  ws.onopen=()=>send({type:'join',role:'display',room,name:navigator.userAgent.slice(0,50)});
  ws.onmessage=async e=>{
    const m=JSON.parse(e.data);
    if(m.type==='status'){status.textContent=m.androids? 'Phone connected — starting stream…':'Waiting for Android phone…';return;}
    if(m.type==='offer'){
      await ensurePeer();
      await pc.setRemoteDescription(m.sdp);
      const answer=await pc.createAnswer();await pc.setLocalDescription(answer);
      send({type:'answer',sdp:pc.localDescription});return;
    }
    if(m.type==='ice'&&m.candidate){try{await pc?.addIceCandidate(m.candidate)}catch(err){console.warn(err)}return;}
    if(m.type==='stream-meta'){status.textContent=m.label||'Streaming';}
  };
  ws.onclose=()=>{if(!stage.classList.contains('connected'))status.textContent='Signaling disconnected';};
}
async function ensurePeer(){
  if(pc)return pc;
  pc=new RTCPeerConnection({iceServers:[]});
  pc.onicecandidate=e=>{if(e.candidate)send({type:'ice',candidate:e.candidate});};
  pc.ontrack=e=>{video.srcObject=e.streams[0];stage.classList.add('connected');status.textContent='Connected';video.play().catch(()=>{});};
  pc.onconnectionstatechange=()=>{if(['failed','disconnected','closed'].includes(pc.connectionState)){stage.classList.remove('connected');status.textContent=`Connection ${pc.connectionState}`;}};
  return pc;
}
$('#newRoom').onclick=makeRoom;
$('#fullscreen').onclick=async()=>{try{if(!document.fullscreenElement)await document.documentElement.requestFullscreen();else await document.exitFullscreen()}catch{}};
makeRoom().catch(err=>{console.error(err);status.textContent='Could not create pairing room';});
