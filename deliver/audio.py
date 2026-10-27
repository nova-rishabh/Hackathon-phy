"""Original score + synthesized UI sounds for the RollWatch film. 120 BPM, A minor, drop at 12.0 s."""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

SR, DUR, BPM = 44100, 33.0, 120
B = 60 / BPM
N = int(SR * DUR)
mix = np.zeros((N, 2))
rng = np.random.default_rng(7)
tt = lambda d: np.arange(int(SR * d)) / SR


def put(sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N:
        return
    s = sig[: N - i] * gain
    mix[i:i + len(s), 0] += s * (1 - pan) ** 0.5
    mix[i:i + len(s), 1] += s * (1 + pan) ** 0.5


def lp(x, f):
    b, a = butter(2, f / (SR / 2))
    return lfilter(b, a, x)


def hp(x, f):
    b, a = butter(2, f / (SR / 2), "high")
    return lfilter(b, a, x)


def env(n, a=0.005, d=0.3):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)


hz = lambda m: 440 * 2 ** ((m - 69) / 12)

# ---------- drums
def kick(g=1.0):
    t = tt(0.45)
    f = 45 + 110 * np.exp(-t * 32)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) * g


def hat(d=0.05):
    n = rng.standard_normal(int(SR * d))
    return hp(n, 7000) * env(len(n), 0.001, d / 4)


def snare():
    t = tt(0.25)
    return (hp(rng.standard_normal(len(t)), 1500) * 0.7 + np.sin(2 * np.pi * 190 * t) * 0.5) * np.exp(-t * 18)


def clap():
    s = np.zeros(int(SR * 0.3))
    for k, o in enumerate((0, 0.011, 0.022)):
        n = hp(rng.standard_normal(int(SR * 0.2)), 1200) * env(int(SR * 0.2), 0.001, 0.05 if k < 2 else 0.12)
        i = int(o * SR)
        s[i:i + len(n)] += n
    return s


# ---------- tonal
CHORDS = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G


def saw(f, d):
    t = tt(d)
    return sum(np.sin(2 * np.pi * f * k * t + rng.uniform(0, 6)) / k for k in range(1, 8))


def pad(ch, d):
    s = sum(saw(hz(m), d) + saw(hz(m) * 1.004, d) for m in ch) / 10
    e = np.minimum(1, tt(d) / 0.4) * np.minimum(1, (d - tt(d)) / 0.3)
    return lp(s, 1800) * e


def pluck(m, d=0.35):
    t = tt(d)
    s = np.sin(2 * np.pi * hz(m) * t) + 0.4 * np.sin(2 * np.pi * hz(m) * 2 * t)
    return s * env(len(t), 0.002, 0.12)


def bass(m, d):
    t = tt(d)
    s = np.sign(np.sin(2 * np.pi * hz(m) * t)) * 0.5 + np.sin(2 * np.pi * hz(m) * t)
    return lp(s, 420) * env(len(t), 0.004, 0.25)


music = np.zeros(N)
side = np.ones(N)


def m_put(sig, t0, g=1.0):
    i = int(t0 * SR)
    if i >= N:
        return
    s = sig[: N - i] * g
    music[i:i + len(s)] += s


def duck(t0, depth=0.65, rel=0.22):
    i = int(t0 * SR)
    n = min(int(SR * rel), N - i)
    if n > 0:
        side[i:i + n] = np.minimum(side[i:i + n], 1 - depth * (1 - np.arange(n) / n))


# pads: whole piece except the break
for bar in range(16):
    t0 = bar * 4 * B
    if 28.0 <= t0 < 29.5:
        continue
    g = 0.35 if t0 < 12 else 0.42
    m_put(pad(CHORDS[bar % 4], 4 * B + 0.3), t0, g)
# arpeggio plucks (8ths) from 2 s, 16ths after the drop
for i in range(int(28 / (B / 2))):
    t0 = i * B / 2
    if t0 < 2 or 28 <= t0:
        continue
    ch = CHORDS[int(t0 // (4 * B)) % 4]
    m_put(pluck(ch[i % 3] + 12 + (12 if (i // 3) % 2 and t0 >= 12 else 0)), t0, 0.16 if t0 < 12 else 0.2)

drums = np.zeros(N)


def d_put(sig, t0, g=1.0):
    i = int(t0 * SR)
    if i >= N:
        return
    s = sig[: N - i] * g
    drums[i:i + len(s)] += s


# intro: kick on 1 and 3 from 6 s
for beat in range(int(DUR / B)):
    t0 = beat * B
    if 6 <= t0 < 10 and beat % 2 == 0:
        d_put(kick(0.8), t0); duck(t0, 0.4)
    if 12 <= t0 < 28:
        d_put(kick(1.0), t0); duck(t0)
        if beat % 2 == 1:
            d_put(clap(), t0, 0.5)
        m_put(bass(CHORDS[int(t0 // (4 * B)) % 4][0] - 24, B / 2), t0 + B / 2, 0.45)
    if 2 <= t0 < 28:
        d_put(hat(), t0 + B / 2, 0.18)
    if 12 <= t0 < 28:
        d_put(hat(0.03), t0 + B / 4, 0.09); d_put(hat(0.03), t0 + 3 * B / 4, 0.09)
# snare build 10-12: 8ths -> 16ths -> 32nds
for k, (a, b, step) in enumerate(((10.0, 11.0, B / 2), (11.0, 11.5, B / 4), (11.5, 12.0, B / 8))):
    for t0 in np.arange(a, b, step):
        d_put(snare(), t0, 0.2 + 0.35 * (t0 - 10) / 2)
# riser into the drop
r = rng.standard_normal(int(SR * 2.0)); rt = tt(2.0)
riser = np.zeros_like(r)
for j in range(0, len(r), 2048):
    f = 300 + 6000 * (j / len(r)) ** 2
    riser[j:j + 2048] = hp(r[j:j + 2048], f)
put(riser * (rt / 2.0) ** 2, 10.0, 0.18)
# drop impact
put(kick(1.4) + lp(rng.standard_normal(int(SR * 0.45)), 900) * np.exp(-tt(0.45) * 8) * 0.6, 12.0, 0.9)
# break 28-29.5: reverse swell
sw = pad(CHORDS[0], 1.5) * np.linspace(0, 1, int(SR * 1.5)) ** 2
m_put(sw, 28.0, 0.5)
# slams 29.5, 30.25, 30.5, 30.75 then final chord 31.0
for t0, g in ((29.5, 1.2), (30.25, 0.8), (30.5, 0.9), (30.75, 1.0)):
    d_put(kick(g), t0); d_put(clap(), t0, 0.4 * g)
d_put(kick(1.3), 31.0)
fin = pad([45, 57, 60, 64, 69], 2.0) * np.exp(-tt(2.0) * 0.9)
m_put(fin, 31.0, 0.6)
for m, o in ((69, 0), (72, 0.12), (76, 0.24), (81, 0.36)):
    m_put(pluck(m, 1.2), 31.0 + o, 0.22)

music *= side
put(music, 0, 0.55); put(drums, 0, 0.55)

# ---------- UI sound design (placed on the picture's event times)
def tick(f=2400, d=0.025):
    t = tt(d)
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 180)


def click():
    t = tt(0.06)
    return (np.sin(2 * np.pi * 1800 * t) * 0.6 + hp(rng.standard_normal(len(t)), 3000) * 0.4) * np.exp(-t * 90)


def whoosh(d=0.35, up=True):
    n = rng.standard_normal(int(SR * d)); out = np.zeros_like(n)
    for j in range(0, len(n), 1024):
        k = j / len(n)
        f = 400 + 3500 * (k if up else 1 - k)
        out[j:j + 1024] = lp(n[j:j + 1024], f)
    return out * np.sin(np.pi * np.linspace(0, 1, len(n)))


def thump():
    t = tt(0.3)
    return np.sin(2 * np.pi * (70 + 90 * np.exp(-t * 40)) * t) * np.exp(-t * 14) + hp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 60) * 0.3


FWD_LEN = 72
for i in range(FWD_LEN):
    put(tick(2000 + rng.uniform(-300, 300)), 0.55 + 2.6 * i / FWD_LEN, 0.12, rng.uniform(-0.3, 0.3))
for i in range(18):
    put(tick(2600), 21.9 + 0.6 * i / 18, 0.1)
for t0 in (5.45, 20.2, 23.55):
    put(click(), t0, 0.5)
for t0, up in ((3.3, True), (5.5, True), (11.9, False), (16.0, True), (18.5, True), (19.55, True), (21.4, True), (25.4, True), (28.4, False)):
    put(whoosh(0.4, up), t0 - 0.12, 0.22)
for t0 in (7.0, 8.0, 9.0, 17.4, 19.0, 20.55, 23.1):
    put(thump(), t0, 0.45)
for t0 in (6.5, 7.5, 8.5):
    put(whoosh(0.25), t0 - 0.05, 0.12)
for i in range(12):  # odometer rolls
    put(tick(3200, 0.015), 7.0 + i * 0.06, 0.08)
for i in range(18):
    put(tick(3000, 0.015), 25.9 + i * 0.06, 0.07)
for r_ in range(19):  # tile cascade on the diagonal
    put(tick(1500 + r_ * 60, 0.02), 12.35 + r_ * 0.035, 0.06, -0.5 + r_ / 18)
# Listen: a soft voice-like hum under the waveform
vt = tt(1.4)
voice = np.sin(2 * np.pi * (180 + 30 * np.sin(2 * np.pi * 3 * vt)) * vt) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 4.5 * vt))) * np.minimum(1, vt / 0.05) * np.minimum(1, (1.4 - vt) / 0.2)
put(lp(voice, 1200), 23.6, 0.12)

# master: gentle limiter and fade
peak = np.max(np.abs(mix))
mix = np.tanh(mix / peak * 1.6) * 0.89
fade = np.ones(N); fade[-int(SR * 0.6):] = np.linspace(1, 0, int(SR * 0.6))
mix *= fade[:, None]
wavfile.write("score.wav", SR, (mix * 32767).astype(np.int16))
print("wrote score.wav", mix.shape, "peak", float(np.max(np.abs(mix))))
