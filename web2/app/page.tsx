"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { Scene, type Pose } from "@/scene/Scene";
import { get, useApi, type Overview, type Story } from "@/lib/api";
import Loader from "@/components/Loader";
import { CHAPTERS, Note, Progress, TopBar } from "@/components/Chrome";
import { Ask, Audit, ClaimCourt, Connect, Hero, Problem, Scale, Tested, WhichStory, Why } from "@/components/Chapters";

/** Where the ring and the voter points sit in each chapter. Between chapters the scene eases from one to the next. */
const POSES: Pose[] = [
  { x: 2.3, y: 0.55, z: 0, scale: 1, spin: 0, form: 0, spread: 1, dim: 0, gridX: 0 },          // hero
  { x: 2.7, y: 1.1, z: -1, scale: 0.8, spin: 0.7, form: 0, spread: 1.1, dim: 0.1, gridX: 0 },  // rumour
  { x: 8.5, y: 2.6, z: -3, scale: 0.55, spin: 1.4, form: 1, spread: 1, dim: 0.15, gridX: 2.1 }, // audit: points become the booth grid
  { x: 3.0, y: 0.3, z: -1, scale: 0.85, spin: 2.2, form: 0, spread: 0.85, dim: 0.1, gridX: 0 }, // which story fits
  { x: 3.4, y: -0.6, z: -2, scale: 0.7, spin: 3.0, form: 0, spread: 1, dim: 0.35, gridX: 0 },   // claim court
  { x: 3.3, y: 0.8, z: -2, scale: 0.7, spin: 3.6, form: 0, spread: 1, dim: 0.35, gridX: 0 },    // ask
  { x: 3.6, y: 0.2, z: -3, scale: 0.65, spin: 4.4, form: 0, spread: 1.3, dim: 0.3, gridX: 0 },  // tested
  { x: 0, y: 0.6, z: -5, scale: 0.5, spin: 5.2, form: 0, spread: 2.3, dim: 0.3, gridX: 0 },     // scale: the field spreads wide
  { x: 0, y: 1.6, z: -4, scale: 0.6, spin: 6.0, form: 0, spread: 1.5, dim: 0.45, gridX: 0 },    // three questions
  { x: 0, y: 1.0, z: 0, scale: 1, spin: 6.6, form: 0, spread: 1, dim: 0, gridX: 0 },            // connect: back to the start
];

function lerpPose(a: Pose, b: Pose, t: number, narrow: boolean): Pose {
  const o = {} as Pose;
  (Object.keys(a) as (keyof Pose)[]).forEach((k) => { o[k] = a[k] + (b[k] - a[k]) * t; });
  if (narrow) { o.x *= 0.12; o.gridX = 0; o.dim = Math.max(o.dim, 0.35); o.y += 1.5; o.scale *= 0.72; } // on phones the scene sits above and behind the text
  return o;
}
const smooth = (t: number) => t * t * (3 - 2 * t);

export default function Home() {
  const canvas = useRef<HTMLCanvasElement>(null);
  const scene = useRef<Scene | null>(null);
  const [loaded, setLoaded] = useState(0); // fonts, eye texture, first API answer
  const [ready, setReady] = useState(false);
  const [active, setActive] = useState(0);
  const [frac, setFrac] = useState(0);
  const story = useRef<Story | null>(null);
  const ov = useApi<Overview>(() => get("/overview"));
  const activeRef = useRef(-1);

  // Scene and loader inputs.
  useEffect(() => {
    if (!canvas.current) return;
    const cap = setTimeout(() => setLoaded((n) => Math.max(n, 3)), 5000); // a sleeping server must not hold the page
    try { scene.current = new Scene(canvas.current, () => setLoaded((n) => n + 1)); }
    catch { setLoaded((n) => n + 1); } // no WebGL: the page still reads fine over the plain background
    document.fonts.ready.then(() => setLoaded((n) => n + 1));
    return () => { clearTimeout(cap); scene.current?.dispose(); };
  }, []);
  useEffect(() => { if (ov.data || ov.error) setLoaded((n) => n + 1); }, [ov.data, ov.error]);

  // Colour the points for the chapter on screen.
  const paint = useCallback((i: number) => {
    const s = scene.current;
    if (!s) return;
    const id = CHAPTERS[i]?.id;
    if (id === "audit" && ov.data) s.setBooths(ov.data.booths.slice().sort((a, b) => a.booth_id.localeCompare(b.booth_id)));
    else if (id === "story" && story.current) s.setStory({ shares: story.current.stories });
    else s.setField();
  }, [ov.data]);

  const onStory = useCallback((d: Story) => {
    story.current = d;
    if (CHAPTERS[activeRef.current]?.id === "story") scene.current?.setStory({ shares: d.stories });
  }, []);

  // Scroll drives the scene: find the chapter at mid-screen and how far through it we are.
  useEffect(() => {
    const secs = CHAPTERS.map((c) => document.getElementById(c.id)).filter(Boolean) as HTMLElement[];
    const onScroll = () => {
      const mid = window.innerHeight * 0.5;
      let i = 0;
      secs.forEach((el, j) => { if (el.getBoundingClientRect().top <= mid) i = j; });
      const r = secs[i].getBoundingClientRect();
      const t = Math.min(1, Math.max(0, (mid - r.top) / r.height));
      const narrow = window.innerWidth < 820;
      // Hold the chapter's pose through its middle, move to the next pose over its last third.
      const move = smooth(Math.min(1, Math.max(0, (t - 0.62) / 0.38)));
      scene.current?.setPose(lerpPose(POSES[i], POSES[Math.min(i + 1, POSES.length - 1)], move, narrow));
      setFrac(t);
      if (i !== activeRef.current) { activeRef.current = i; setActive(i); paint(i); }
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => { window.removeEventListener("scroll", onScroll); window.removeEventListener("resize", onScroll); };
  }, [paint]);

  // Re-paint when the booth outcomes arrive while the audit chapter is already on screen.
  useEffect(() => { if (activeRef.current >= 0) paint(activeRef.current); }, [paint]);

  // Text rises in as each chapter comes into view.
  useEffect(() => {
    if (!ready) return;
    const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && e.target.classList.add("in")), { threshold: 0.18 });
    document.querySelectorAll(".chapter").forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, [ready]);

  return (
    <>
      <canvas ref={canvas} className="gl" aria-hidden="true" />
      <Loader done={Math.min(loaded, 3)} total={3} onFinish={() => setReady(true)} />
      <TopBar active={active} />
      <Progress active={active} frac={frac} />
      <Note />
      <main className="page">
        <Hero ov={ov.data} />
        <Problem ov={ov.data} />
        <Audit ov={ov.data} />
        <WhichStory onStory={onStory} />
        <ClaimCourt visible={active >= 3} />
        <Ask />
        <Tested />
        <Scale />
        <Why />
        <Connect />
      </main>
    </>
  );
}
