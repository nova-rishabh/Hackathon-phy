"""Render film.html: `sheet` = stills at given times; `full` = every frame piped to ffmpeg."""
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
DUR, FPS = 33.0, 60


def page_ctx(p):
    b = p.chromium.launch(channel="chrome", args=["--allow-file-access-from-files", "--disable-web-security"])
    pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
    pg.goto((HERE / "film.html").as_uri())
    pg.wait_for_function("document.fonts.ready.then(() => true)")
    pg.wait_for_timeout(400)
    return b, pg


def sheet(times, out="sheet"):
    (HERE / out).mkdir(exist_ok=True)
    with sync_playwright() as p:
        b, pg = page_ctx(p)
        for t in times:
            pg.evaluate(f"seek({t})")
            pg.screenshot(path=str(HERE / out / f"t{t:05.2f}.png"))
        b.close()


def full(out="film_noaudio.mp4", fps=FPS, scale=None):
    vf = ["-vf", f"scale={scale}"] if scale else []
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "png", "-i", "-",
                           *vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", str(HERE / out)],
                          stdin=subprocess.PIPE)
    with sync_playwright() as p:
        b, pg = page_ctx(p)
        n = int(DUR * fps)
        for i in range(n):
            pg.evaluate(f"seek({i / fps})")
            ff.stdin.write(pg.screenshot(type="png"))
            if i % (fps * 3) == 0:
                print(f"{i / fps:.0f}s", flush=True)
        b.close()
    ff.stdin.close()
    ff.wait()


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "sheet":
        sheet([float(x) for x in sys.argv[2:]])
    elif mode == "draft":
        full("draft.mp4", fps=20, scale="960:540")
    else:
        full()
