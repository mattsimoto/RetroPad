const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const QRCode = require('qrcode');

const PORT = Number(process.env.PORT || 8080);
const VERSION = '0.3.3';
const ROOT = path.join(__dirname, '..', 'public');
const MIME = {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.svg':'image/svg+xml','.png':'image/png'};
const rooms = new Map();

function localIPs(){const out=[];for(const entries of Object.values(os.networkInterfaces()))for(const n of entries||[])if(n.family==='IPv4'&&!n.internal)out.push(n.address);return [...new Set(out)];}
function roomCode(){const a='ABCDEFGHJKLMNPQRSTUVWXYZ23456789';let s='';for(let i=0;i<6;i++)s+=a[crypto.randomInt(a.length)];return s;}
function cleanRoom(v){return String(v||'').toUpperCase().replace(/[^A-Z0-9]/g,'').slice(0,6);}
function getRoom(id){if(!rooms.has(id))rooms.set(id,{peers:new Set(),players:new Map(),created:Date.now()});return rooms.get(id);}

class WSConnection {
  constructor(socket){this.socket=socket;this.buffer=Buffer.alloc(0);this.closed=false;socket.on('data',d=>this._data(d));socket.on('close',()=>this._close());socket.on('error',()=>this._close());}
  send(obj){if(this.closed)return;const payload=Buffer.from(JSON.stringify(obj));let head;if(payload.length<126){head=Buffer.alloc(2);head[1]=payload.length;}else if(payload.length<65536){head=Buffer.alloc(4);head[1]=126;head.writeUInt16BE(payload.length,2);}else{head=Buffer.alloc(10);head[1]=127;head.writeBigUInt64BE(BigInt(payload.length),2);}head[0]=0x81;this.socket.write(Buffer.concat([head,payload]));}
  _frame(op,payload){if(op===0x8){this.socket.end();return this._close();}if(op===0x9){let h=Buffer.from([0x8a,payload.length]);this.socket.write(Buffer.concat([h,payload]));return;}if(op!==0x1)return;try{this.onmessage?.(JSON.parse(payload.toString('utf8')));}catch{}}
  _data(data){this.buffer=Buffer.concat([this.buffer,data]);while(this.buffer.length>=2){let b1=this.buffer[0],b2=this.buffer[1],op=b1&15,masked=!!(b2&128),len=b2&127,off=2;if(len===126){if(this.buffer.length<4)return;len=this.buffer.readUInt16BE(2);off=4;}else if(len===127){if(this.buffer.length<10)return;const n=this.buffer.readBigUInt64BE(2);if(n>BigInt(Number.MAX_SAFE_INTEGER))return this.socket.destroy();len=Number(n);off=10;}const maskLen=masked?4:0;if(this.buffer.length<off+maskLen+len)return;let mask=null;if(masked){mask=this.buffer.subarray(off,off+4);off+=4;}let payload=Buffer.from(this.buffer.subarray(off,off+len));this.buffer=this.buffer.subarray(off+len);if(masked)for(let i=0;i<payload.length;i++)payload[i]^=mask[i%4];this._frame(op,payload);}}
  _close(){if(this.closed)return;this.closed=true;this.onclose?.();}
}
function assignPlayer(room,ws,requested){const wanted=Number(requested);if(wanted>=1&&wanted<=4&&!room.players.has(wanted)){room.players.set(wanted,ws);return wanted;}for(let i=1;i<=4;i++)if(!room.players.has(i)){room.players.set(i,ws);return i;}return 0;}
function release(ws){if(!ws.room||!rooms.has(ws.room))return;const room=rooms.get(ws.room);room.peers.delete(ws);if(ws.role==='controller'&&room.players.get(ws.player)===ws)room.players.delete(ws.player);if(!room.peers.size)rooms.delete(ws.room);else status(ws.room);}
function status(id){const r=rooms.get(id);if(!r)return;const cs=[...r.peers].filter(p=>p.role==='controller'),rs=[...r.peers].filter(p=>p.role==='receiver');const players=cs.map(p=>({player:p.player,profile:p.profile||null,name:p.name||`Player ${p.player}`}));for(const p of r.peers)p.send({type:'status',controllers:cs.length,receivers:rs.length,players});}
function handleMessage(ws,msg){
  if(msg.type==='join'){
    release(ws);const id=cleanRoom(msg.room);if(id.length!==6)return ws.send({type:'error',message:'Invalid room code'});const room=getRoom(id);ws.room=id;ws.role=msg.role==='receiver'?'receiver':'controller';ws.name=String(msg.name||'').slice(0,32);room.peers.add(ws);
    if(ws.role==='controller'){ws.player=assignPlayer(room,ws,msg.player);if(!ws.player){room.peers.delete(ws);return ws.send({type:'error',message:'This room already has four controllers.'});}ws.send({type:'joined',room:id,player:ws.player});}else ws.send({type:'joined',room:id,role:'receiver'});status(id);return;
  }
  if(!ws.room||!rooms.has(ws.room))return;if(msg.type==='profile'&&ws.role==='controller')ws.profile=String(msg.profile||'').slice(0,24);const packet={...msg,player:ws.player||msg.player||0,profile:msg.profile||ws.profile||null};for(const peer of rooms.get(ws.room).peers)if(peer!==ws&&peer.role!==ws.role)peer.send(packet);if(msg.type==='profile')status(ws.room);
}

const server=http.createServer(async(req,res)=>{
  const u=new URL(req.url,`http://${req.headers.host||'localhost'}`);
  if(u.pathname==='/api/new-room'){let id;do{id=roomCode();}while(rooms.has(id));getRoom(id);res.writeHead(200,{'Content-Type':'application/json','Cache-Control':'no-store'});return res.end(JSON.stringify({room:id}));}
  if(u.pathname==='/api/info'){res.writeHead(200,{'Content-Type':'application/json','Cache-Control':'no-store'});return res.end(JSON.stringify({name:'RetroPad',version:VERSION,port:PORT,ips:localIPs(),maxPlayers:4,qr:true}));}
  if(u.pathname==='/api/qr'){
    const text=u.searchParams.get('text')||'';
    if(!text||text.length>1000){res.writeHead(400,{'Content-Type':'text/plain'});return res.end('Invalid QR text');}
    try{
      const svg=await QRCode.toString(text,{type:'svg',margin:4,errorCorrectionLevel:'M'});
      res.writeHead(200,{'Content-Type':'image/svg+xml; charset=utf-8','Cache-Control':'no-store'});return res.end(svg);
    }catch(e){res.writeHead(500,{'Content-Type':'text/plain'});return res.end('QR error');}
  }
  let requestPath=decodeURIComponent(u.pathname);if(requestPath==='/')requestPath='/index.html';const filePath=path.normalize(path.join(ROOT,requestPath));if(!filePath.startsWith(ROOT)){res.writeHead(403);return res.end('Forbidden');}fs.readFile(filePath,(err,data)=>{if(err){res.writeHead(404);return res.end('Not found');}res.writeHead(200,{'Content-Type':MIME[path.extname(filePath)]||'application/octet-stream','Cache-Control':'no-store'});res.end(data);});
});
server.on('upgrade',(req,socket)=>{
  const u=new URL(req.url,`http://${req.headers.host||'localhost'}`);if(u.pathname!=='/ws')return socket.destroy();const key=req.headers['sec-websocket-key'];if(!key)return socket.destroy();const accept=crypto.createHash('sha1').update(key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest('base64');socket.write('HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: '+accept+'\r\n\r\n');const ws=new WSConnection(socket);ws.onmessage=m=>handleMessage(ws,m);ws.onclose=()=>release(ws);
});
server.listen(PORT,'0.0.0.0',()=>{console.log(`RetroPad v${VERSION} running on port ${PORT}`);for(const ip of localIPs())console.log(`Phone:    http://${ip}:${PORT}/`);console.log(`Receiver: http://localhost:${PORT}/receiver.html`);});
