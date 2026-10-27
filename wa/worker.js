// RollWatch WhatsApp worker: keeps a WhatsApp Web session on this machine and makes only OUTBOUND
// calls to the API (long-poll /wa/outbox, /wa/heartbeat, /wa/inbound). No phone numbers in logs.
import { fileURLToPath } from "node:url";
import path from "node:path";
import fs from "node:fs";
import dotenv from "dotenv";
import pino from "pino";
import qrcodeTerminal from "qrcode-terminal";
import QRCode from "qrcode";
import makeWASocket, { useMultiFileAuthState, DisconnectReason, downloadMediaMessage, Browsers }
  from "@whiskeysockets/baileys";

const HERE = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.join(HERE, "..", ".env"), quiet: true });
const API = (process.env.API_BASE || "http://localhost:8000").replace(/\/$/, "");
const SECRET = process.env.WA_WORKER_SECRET || "";
if (!SECRET) { console.error("WA_WORKER_SECRET is not set (repo-root .env or env)."); process.exit(1); }
const H = { "Content-Type": "application/json", "X-WA-Secret": SECRET };
const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);
const quiet = pino({ level: "silent" });

let sock = null;
let state = "connecting";
let myNumber = null;
let pairing = false;

async function call(method, route, body, ms = 30000) {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), ms);
  try {
    const r = await fetch(API + route, { method, headers: H, body: body ? JSON.stringify(body) : undefined, signal: ctl.signal });
    if (!r.ok) throw new Error(`${route} -> HTTP ${r.status}`);
    return await r.json();
  } finally { clearTimeout(t); }
}

async function heartbeat() {
  try { await call("POST", "/wa/heartbeat", { state, number: myNumber }); }
  catch (e) { log("heartbeat failed:", e.message); }
}
setInterval(heartbeat, 15000);

const jidOf = (e164) => e164.replace(/\D/g, "") + "@s.whatsapp.net";

async function outboxLoop() {
  for (;;) {
    if (state !== "connected") { await new Promise((r) => setTimeout(r, 2000)); await heartbeat(); continue; }
    try {
      const { messages } = await call("GET", "/wa/outbox?wait=20", null, 40000);
      for (const m of messages) {
        try { await sock.sendMessage(jidOf(m.to), { text: m.text }); log("sent outbox message", m.id); }
        catch (e) { log("send failed", m.id, e.message); }
      }
    } catch (e) { log("outbox poll failed:", e.message); await new Promise((r) => setTimeout(r, 3000)); }
  }
}

async function onMessage(msg) {
  const jid = msg.key.remoteJid || "";
  if (msg.key.fromMe || !jid || jid.endsWith("@g.us") || jid === "status@broadcast" || jid.endsWith("@newsletter")) return;
  const m = msg.message || {};
  const img = m.imageMessage;
  const voice = m.audioMessage;
  const text = m.conversation || m.extendedTextMessage?.text || img?.caption || "";
  let image_b64 = null, audio_b64 = null;
  if (img || voice) {
    try {
      const b64 = (await downloadMediaMessage(msg, "buffer", {})).toString("base64");
      if (img) image_b64 = b64; else audio_b64 = b64;
    } catch (e) { log("media download failed:", e.message); }
  }
  if (!text && !image_b64 && !audio_b64) return;
  log("inbound", img ? "image" : voice ? "voice" : "text");
  try {
    await sock.sendPresenceUpdate(audio_b64 ? "recording" : "composing", jid);
    const { replies } = await call("POST", "/wa/inbound", { from: jid.split("@")[0], text, image_b64, audio_b64 }, 120000);
    for (const r of replies) {
      if (r.audio_b64) await sock.sendMessage(jid, { audio: Buffer.from(r.audio_b64, "base64"), mimetype: r.audio_mime, ptt: !!r.ptt });
      else if (r.image_b64) await sock.sendMessage(jid, { image: Buffer.from(r.image_b64, "base64"), caption: r.text || undefined });
      else if (r.text) await sock.sendMessage(jid, { text: r.text });
    }
    log("replied", replies.length);
  } catch (e) { log("inbound failed:", e.message); }
}

async function start() {
  const { state: auth, saveCreds } = await useMultiFileAuthState(path.join(HERE, ".auth"));
  sock = makeWASocket({ auth, logger: quiet, browser: Browsers.ubuntu("RollWatch"), markOnlineOnConnect: false });
  sock.ev.on("creds.update", saveCreds);
  sock.ev.on("connection.update", async (u) => {
    if (u.qr) {
      state = "qr";
      // WA_PAIR_NUMBER (digits with country code) links by an 8-character code instead of the fast-rotating QR.
      const pairNo = (process.env.WA_PAIR_NUMBER || "").replace(/\D/g, "");
      if (pairNo && !auth.creds.registered && !pairing) {
        pairing = true;
        try {
          const code = await sock.requestPairingCode(pairNo);
          fs.writeFileSync(path.join(HERE, "pair-code.txt"), code + "\n");
          log("pairing code ready in wa/pair-code.txt: WhatsApp > Linked devices > Link a device > Link with phone number instead");
        } catch (e) { pairing = false; log("pairing code failed:", e.message); }
      } else if (!pairNo) {
        qrcodeTerminal.generate(u.qr, { small: true });
        await QRCode.toFile(path.join(HERE, "qr.png"), u.qr, { margin: 2, width: 360 });
        log("scan the QR (also saved to wa/qr.png): WhatsApp > Linked devices > Link a device");
      }
      heartbeat();
    }
    if (u.connection === "open") {
      state = "connected";
      myNumber = "+" + (sock.user?.id || "").split(":")[0].split("@")[0];
      log("connected");
      heartbeat();
    }
    if (u.connection === "close") {
      const code = u.lastDisconnect?.error?.output?.statusCode;
      state = "connecting";
      heartbeat();
      if (code === DisconnectReason.loggedOut) {
        log("logged out: delete wa/.auth and run again to pair");
        process.exit(1);
      }
      log("connection closed (", code, "), reconnecting");
      setTimeout(start, 2000);
    }
  });
  sock.ev.on("messages.upsert", ({ messages, type }) => {
    if (type !== "notify") return;
    for (const msg of messages) onMessage(msg);
  });
}

log("RollWatch WhatsApp worker; API", API);
heartbeat();
start();
outboxLoop();
