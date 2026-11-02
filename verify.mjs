// index.html を配信し、各バリアントを headless Chrome (CDP) で開いて状態とスクリーンショットを取る。
// 使い方: node verify.mjs [出力ディレクトリ] [ベース URL]
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { createReadStream, mkdirSync, statSync, writeFileSync } from 'node:fs';
import { extname, join, normalize } from 'node:path';

const OUT = process.argv[2] || 'shots';
let BASE = process.argv[3] || '';
const CHROME = process.env.CHROME || 'google-chrome';
const PORT = 8765;
const CDP_PORT = 9333;

const CASES = [
  ['vjs-ja-100', 'variant=vjs&lang=ja&zoom=100&t=12'],
  ['vjs-en-100', 'variant=vjs&lang=en&zoom=100&t=12'],
  ['vjs-off-100', 'variant=vjs&lang=off&zoom=100&t=12'],
  ['vjs-ja-cover', 'variant=vjs&lang=ja&zoom=130&t=12'],
  ['vjs-ja-200', 'variant=vjs&lang=ja&zoom=200&t=12'],
  ['vjs-ja-3lines', 'variant=vjs&lang=ja&zoom=100&t=64'],
  ['vjs-ja-burnedin', 'variant=vjs&lang=ja&zoom=130&t=306'],
  ['vjs-en-burnedin', 'variant=vjs&lang=en&zoom=130&t=306'],
  ['vjsNoNative-ja-200', 'variant=vjsNoNative&lang=ja&zoom=200&t=12'],
  ['native-ja-100', 'variant=native&lang=ja&zoom=100&t=12'],
  ['native-ja-200', 'variant=native&lang=ja&zoom=200&t=12'],
];

mkdirSync(OUT, { recursive: true });
const children = [];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Range 対応の静的サーバー。Range を返さないと Chrome が動画をシーク不可と扱う。
const TYPES = { '.html': 'text/html; charset=utf-8', '.mp4': 'video/mp4', '.vtt': 'text/vtt; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png' };
let server = null;
if (!BASE) {
  server = createServer((req, res) => {
    const url = new URL(req.url, 'http://x');
    const file = normalize(join(process.cwd(), url.pathname === '/' ? 'index.html' : url.pathname));
    let size;
    try { size = statSync(file).size; } catch { res.writeHead(404).end(); return; }
    const type = TYPES[extname(file)] || 'application/octet-stream';
    const range = /^bytes=(\d*)-(\d*)$/.exec(req.headers.range || '');
    if (range) {
      const start = range[1] ? Number(range[1]) : Math.max(0, size - Number(range[2]));
      const end = range[2] && range[1] ? Math.min(Number(range[2]), size - 1) : size - 1;
      res.writeHead(206, { 'Content-Type': type, 'Accept-Ranges': 'bytes', 'Content-Range': `bytes ${start}-${end}/${size}`, 'Content-Length': end - start + 1 });
      createReadStream(file, { start, end }).pipe(res);
    } else {
      res.writeHead(200, { 'Content-Type': type, 'Accept-Ranges': 'bytes', 'Content-Length': size });
      createReadStream(file).pipe(res);
    }
  }).listen(PORT, '127.0.0.1');
  BASE = `http://127.0.0.1:${PORT}/`;
}
children.push(spawn(CHROME, [
  '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--mute-audio',
  '--autoplay-policy=no-user-gesture-required', `--remote-debugging-port=${CDP_PORT}`,
  '--window-size=900,1000', 'about:blank',
], { stdio: 'ignore' }));
await sleep(1500);

async function cdpTarget() {
  const res = await fetch(`http://127.0.0.1:${CDP_PORT}/json/new?about:blank`, { method: 'PUT' });
  return res.json();
}

function connect(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let id = 0;
  const pending = new Map();
  const events = [];
  ws.addEventListener('message', (m) => {
    const msg = JSON.parse(m.data);
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
    else if (msg.method) events.push(msg);
  });
  const send = (method, params = {}) => new Promise((resolve) => {
    const myId = ++id;
    pending.set(myId, resolve);
    ws.send(JSON.stringify({ id: myId, method, params }));
  });
  const open = new Promise((r) => ws.addEventListener('open', r));
  return { send, events, open, close: () => ws.close() };
}

const STATUS_JS = `(() => {
  const t = (id) => document.getElementById(id).textContent;
  const stage = document.getElementById('stage');
  const v = stage.querySelector('video');
  const display = stage.querySelector('.vjs-text-track-display');
  return JSON.stringify({
    cue: t('cue'), renderer: t('renderer'), tracks: t('tracks'),
    currentTime: v && v.currentTime, readyState: v && v.readyState,
    transform: v && v.style.transform,
    vttDisplayText: display ? display.textContent.trim() : null,
    ccButton: !!stage.querySelector('.vjs-subs-caps-button'),
    qr: !!document.querySelector('#qr svg'), shareUrl: document.getElementById('shareUrl').href,
  });
})()`;

let failures = 0;
for (const [name, query] of CASES) {
  const target = await cdpTarget();
  const c = connect(target.webSocketDebuggerUrl);
  await c.open;
  await c.send('Runtime.enable');
  await c.send('Log.enable');
  await c.send('Page.enable');
  await c.send('Emulation.setDeviceMetricsOverride', { width: 900, height: 1000, deviceScaleFactor: 1, mobile: false });
  await c.send('Page.navigate', { url: `${BASE}?${query}` });
  let status = {};
  const expectedLang = new URLSearchParams(query).get('lang');
  for (let i = 0; i < 60; i++) {
    await sleep(250);
    const r = await c.send('Runtime.evaluate', { expression: STATUS_JS, returnByValue: true });
    status = JSON.parse(r.result.result.value);
    const seeked = status.readyState >= 2 && status.tracks && Math.abs(status.currentTime - Number(new URLSearchParams(query).get('t'))) < 1;
    if (seeked && (expectedLang === 'off' || status.cue !== '')) break;
  }
  await sleep(500);
  const r = await c.send('Runtime.evaluate', { expression: STATUS_JS, returnByValue: true });
  status = JSON.parse(r.result.result.value);
  const shot = await c.send('Page.captureScreenshot', { format: 'png' });
  writeFileSync(join(OUT, `${name}.png`), Buffer.from(shot.result.data, 'base64'));
  const errors = c.events
    .filter((e) => e.method === 'Runtime.exceptionThrown' || (e.method === 'Log.entryAdded' && e.params.entry.level === 'error'))
    .map((e) => e.method === 'Runtime.exceptionThrown' ? e.params.exceptionDetails.text + ' ' + (e.params.exceptionDetails.exception?.description || '') : e.params.entry.text);
  const ok = errors.length === 0 && status.qr && status.shareUrl.endsWith('?' + query) && (expectedLang === 'off' ? status.cue === '' : status.cue !== '');
  if (!ok) failures++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}  cue=${JSON.stringify(status.cue)}  tracks=${status.tracks}  t=${status.currentTime?.toFixed(1)}  renderer=${status.renderer}  cc=${status.ccButton}  qr=${status.qr}  share=${status.shareUrl}  vttDisplay=${JSON.stringify(status.vttDisplayText)}  transform=${status.transform}`);
  for (const e of errors) console.log(`     error: ${e}`);
  c.close();
  await c.send;
  await fetch(`http://127.0.0.1:${CDP_PORT}/json/close/${target.id}`).catch(() => {});
}

for (const ch of children) ch.kill();
if (server) server.close();
console.log(failures ? `${failures} case(s) failed` : 'all cases ok');
process.exit(failures ? 1 : 0);
