// index.html を配信し、各バリアントを headless Chrome (CDP) で開いて状態とスクリーンショットを取る。
// 使い方: node verify.mjs [出力ディレクトリ] [ベース URL]
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const OUT = process.argv[2] || 'shots';
let BASE = process.argv[3] || '';
const CHROME = process.env.CHROME || 'google-chrome';
const PORT = 8765;
const CDP_PORT = 9333;

const CASES = [
  ['vjs-ja-100', 'variant=vjs&lang=ja&zoom=100&t=12'],
  ['vjs-en-100', 'variant=vjs&lang=en&zoom=100&t=12'],
  ['vjs-off-100', 'variant=vjs&lang=off&zoom=100&t=12'],
  ['vjs-ja-200', 'variant=vjs&lang=ja&zoom=200&t=12'],
  ['vjs-ja-long', 'variant=vjs&lang=ja&zoom=100&t=16'],
  ['vjsNoNative-ja-200', 'variant=vjsNoNative&lang=ja&zoom=200&t=12'],
  ['native-ja-100', 'variant=native&lang=ja&zoom=100&t=12'],
  ['native-ja-200', 'variant=native&lang=ja&zoom=200&t=12'],
];

mkdirSync(OUT, { recursive: true });
const children = [];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

if (!BASE) {
  children.push(spawn('python3', ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1'], { stdio: 'ignore' }));
  BASE = `http://127.0.0.1:${PORT}/`;
  await sleep(800);
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
  for (let i = 0; i < 40; i++) {
    await sleep(250);
    const r = await c.send('Runtime.evaluate', { expression: STATUS_JS, returnByValue: true });
    status = JSON.parse(r.result.result.value);
    if (status.readyState >= 2 && status.tracks && Math.abs(status.currentTime - Number(new URLSearchParams(query).get('t'))) < 1) break;
  }
  await sleep(500);
  const r = await c.send('Runtime.evaluate', { expression: STATUS_JS, returnByValue: true });
  status = JSON.parse(r.result.result.value);
  const shot = await c.send('Page.captureScreenshot', { format: 'png' });
  writeFileSync(join(OUT, `${name}.png`), Buffer.from(shot.result.data, 'base64'));
  const errors = c.events
    .filter((e) => e.method === 'Runtime.exceptionThrown' || (e.method === 'Log.entryAdded' && e.params.entry.level === 'error'))
    .map((e) => e.method === 'Runtime.exceptionThrown' ? e.params.exceptionDetails.text + ' ' + (e.params.exceptionDetails.exception?.description || '') : e.params.entry.text);
  const expectedLang = new URLSearchParams(query).get('lang');
  const ok = errors.length === 0 && (expectedLang === 'off' ? status.cue === '' : status.cue !== '');
  if (!ok) failures++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}  cue=${JSON.stringify(status.cue)}  tracks=${status.tracks}  t=${status.currentTime?.toFixed(1)}  renderer=${status.renderer}  cc=${status.ccButton}  vttDisplay=${JSON.stringify(status.vttDisplayText)}  transform=${status.transform}`);
  for (const e of errors) console.log(`     error: ${e}`);
  c.close();
  await c.send;
  await fetch(`http://127.0.0.1:${CDP_PORT}/json/close/${target.id}`).catch(() => {});
}

for (const ch of children) ch.kill();
console.log(failures ? `${failures} case(s) failed` : 'all cases ok');
process.exit(failures ? 1 : 0);
