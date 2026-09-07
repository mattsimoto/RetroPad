#!/usr/bin/env python3
import argparse, json, platform, sys, time, urllib.request
from pathlib import Path

try:
    import websocket
except ImportError:
    print('Missing websocket-client. Run: pip install -r receiver/requirements.txt', file=sys.stderr); sys.exit(2)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from drivers import create_driver


def http_json(url):
    with urllib.request.urlopen(url, timeout=3) as r:
        return json.loads(r.read().decode('utf-8'))


def main():
    ap=argparse.ArgumentParser(description='RetroPad native receiver')
    ap.add_argument('--host', default='127.0.0.1:8080', help='RetroPad server host:port')
    ap.add_argument('--room', help='6-character pairing code. Omit to create one.')
    ap.add_argument('--driver', default='auto', choices=['auto','keyboard','macos-hid','linux-uinput','windows-vgamepad'])
    args=ap.parse_args()
    base=f'http://{args.host}'
    room=(args.room or http_json(base+'/api/new-room')['room']).upper()
    driver=create_driver(args.driver)
    print(f'RetroPad native receiver')
    print(f'Platform: {platform.system()} {platform.machine()}')
    print(f'Driver:   {driver.name}')
    print(f'Room:     {room}')
    print(f'Phone:    {base}/?room={room}')
    print('Press Ctrl+C to stop.\n')

    ws_url=('wss://' if args.host.startswith('https://') else 'ws://') + args.host.replace('http://','').replace('https://','') + '/ws'

    def on_open(ws): ws.send(json.dumps({'type':'join','role':'receiver','room':room,'name':driver.name}))
    def on_message(ws, raw):
        try: m=json.loads(raw)
        except Exception: return
        if m.get('type')=='status':
            players=', '.join(f"P{x.get('player')} {x.get('profile') or ''}" for x in m.get('players',[])) or 'none'
            print(f'Controllers: {players}', flush=True); return
        if m.get('type')=='profile':
            driver.set_profile(int(m.get('player') or 1), m.get('profile') or 'generic'); return
        if m.get('type')!='input': return
        p=int(m.get('player') or 1)
        if m.get('profile'): driver.set_profile(p,m['profile'])
        if m.get('inputType')=='button': driver.button(p, m.get('button',''), bool(m.get('pressed')))
        elif m.get('inputType')=='axis': driver.axis(p, m.get('axis','left'), float(m.get('x',0)), float(m.get('y',0)))
    def on_error(ws, err): print(f'Connection error: {err}', file=sys.stderr)
    def on_close(ws, *args): driver.release_all()

    app=websocket.WebSocketApp(ws_url,on_open=on_open,on_message=on_message,on_error=on_error,on_close=on_close)
    try:
        while True:
            app.run_forever(ping_interval=15,ping_timeout=5)
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        driver.close()

if __name__=='__main__': main()
