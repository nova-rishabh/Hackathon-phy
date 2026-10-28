import * as THREE from "three";

/**
 * The page's one WebGL scene, written for RollWatch (no third-party scene code).
 * - A chrome ring holds the RollWatch eye and hangs from a looping wire.
 * - 2,400 points stand for voters. They drift as a field, or gather into the 10 x 10 booth grid,
 *   coloured by each booth's real outcome from /overview, or by a booth's story shares from /stories.
 * Scroll and pointer only set targets; every frame eases toward them, so motion stays smooth.
 */

export type Mode = "field" | "grid" | "story";
export interface Pose { x: number; y: number; z: number; scale: number; spin: number; form: number; spread: number; dim: number; gridX: number }
export interface BoothTint { outcome: string }
export interface StoryTint { shares: { code: string; share: number }[] }

const N = 2400;
const PER_BOOTH = N / 100;

// Colours: greys for the innocent stories, butter yellow for the unexplained part, periwinkle for likely benign.
const C = {
  dim: new THREE.Color("#5d6470"),
  grey: new THREE.Color("#9097a3"),
  soft: new THREE.Color("#c9ced6"),
  white: new THREE.Color("#f2f4f7"),
  yellow: new THREE.Color("#f6d84d"),
  benign: new THREE.Color("#b8c7ff"),
  death: new THREE.Color("#8d939c"),
  dupes: new THREE.Color("#a9aeb6"),
  boundary: new THREE.Color("#c3c7cd"),
  hostel: new THREE.Color("#dde0e4"),
};

const BG_VERT = /* glsl */ `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.9999, 1.0); }`;
const BG_FRAG = /* glsl */ `
  varying vec2 vUv; uniform float uTime; uniform vec2 uAspect; uniform float uDim;
  float hash(vec2 p){ return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
  void main(){
    vec2 p = vUv * uAspect;
    vec3 col = vec3(0.020, 0.024, 0.032);
    float g1 = exp(-2.2 * length(p - vec2(0.08 * uAspect.x, 1.05)));      // cool glow, top left
    float g2 = exp(-3.0 * length(p - vec2(0.85 * uAspect.x, -0.1)));      // faint warm glow, bottom right
    col += vec3(0.16, 0.22, 0.36) * g1 * (0.9 + 0.1 * sin(uTime * 0.3));
    col += vec3(0.20, 0.16, 0.08) * g2 * 0.45;
    col *= 1.0 - 0.35 * uDim;
    col += (hash(vUv * 900.0 + uTime) - 0.5) * 0.018;                     // film grain
    gl_FragColor = vec4(col, 1.0);
  }`;

const PT_VERT = /* glsl */ `
  attribute vec3 aGrid; attribute vec3 aColA; attribute vec3 aColB; attribute float aSize; attribute float aPhase;
  uniform float uTime; uniform float uForm; uniform float uSpread; uniform float uMix; uniform float uPx; uniform float uFocus; uniform float uGridX;
  varying vec3 vCol; varying float vBlur; varying float vA;
  void main(){
    vec3 drift = vec3(sin(uTime * 0.21 + aPhase * 6.0), cos(uTime * 0.17 + aPhase * 4.0), sin(uTime * 0.13 + aPhase * 9.0)) * 0.18;
    vec3 field = position * uSpread + drift;
    vec3 grid = aGrid + vec3(uGridX, 0.0, 0.0) + drift * 0.08;
    float f = smoothstep(0.0, 1.0, clamp(uForm * 1.25 - aPhase * 0.25, 0.0, 1.0));
    vec3 p = mix(field, grid, f);
    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    float depth = -mv.z;
    vBlur = clamp(abs(depth - uFocus) / 6.0, 0.0, 1.0) * (1.0 - f * 0.85);   // out-of-focus points grow into soft bokeh
    gl_PointSize = aSize * uPx * (1.0 + vBlur * 2.4) * (8.0 / depth) * mix(1.0, 1.25, f);
    gl_Position = projectionMatrix * mv;
    vCol = mix(aColA, aColB, uMix);
    vA = mix(0.85, 0.35, vBlur) + uForm * 0.15;
  }`;
const PT_FRAG = /* glsl */ `
  varying vec3 vCol; varying float vBlur; varying float vA; uniform float uDim;
  void main(){
    float d = length(gl_PointCoord - 0.5) * 2.0;
    float core = 1.0 - smoothstep(0.55 - vBlur * 0.45, 1.0, d);
    float rim = smoothstep(0.7, 0.95, d) * (1.0 - smoothstep(0.95, 1.0, d)) * vBlur * 0.6;
    float a = (core + rim) * vA * (1.0 - 0.6 * uDim);
    if (a < 0.01) discard;
    gl_FragColor = vec4(vCol, a);
  }`;

export class Scene {
  private renderer: THREE.WebGLRenderer;
  private scene = new THREE.Scene();
  private camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
  private hero = new THREE.Group();
  private eye?: THREE.Mesh;
  private bg: THREE.ShaderMaterial;
  private pts: THREE.ShaderMaterial;
  private geo = new THREE.BufferGeometry();
  private colA = new Float32Array(N * 3);
  private colB = new Float32Array(N * 3);
  private mixT = 1; // 0..1 progress of the current colour change
  private clock = new THREE.Clock();
  private raf = 0;
  private reduced: boolean;
  private target: Pose = { x: 0, y: 0, z: 0, scale: 1, spin: 0, form: 0, spread: 1, dim: 0, gridX: 0 };
  private pose: Pose = { ...this.target };
  private pointer = new THREE.Vector2();
  private pointerEase = new THREE.Vector2();

  constructor(private canvas: HTMLCanvasElement, onReady?: () => void) {
    this.reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: "high-performance" });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.05;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;

    const pmrem = new THREE.PMREMGenerator(this.renderer);
    // A dark room lit by a few coloured strips: the chrome reads dark with cool and warm edges, not studio silver.
    const room = new THREE.Scene();
    room.add(new THREE.Mesh(new THREE.SphereGeometry(20, 32, 16), new THREE.MeshBasicMaterial({ color: 0x07080b, side: THREE.BackSide })));
    const strip = (hex: string, power: number, x: number, y: number, z: number, w: number, h: number) => {
      const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: new THREE.Color(hex).multiplyScalar(power), side: THREE.DoubleSide }));
      m.position.set(x, y, z); m.lookAt(0, 0, 0); room.add(m);
    };
    strip("#ffffff", 3.5, 0, 9, 4, 10, 1.2);    // soft key from above
    strip("#6f8cff", 5, -9, 2, 2, 3, 9);        // periwinkle, left
    strip("#ffb347", 4, 9, -2, 1, 2.5, 7);      // warm amber, right
    strip("#c46bff", 4, 2, -3, -9, 7, 2);       // violet, behind
    strip("#ffffff", 2, 0, -8, 6, 12, 0.8);     // thin floor bounce
    this.scene.environment = pmrem.fromScene(room as unknown as THREE.Scene, 0.02).texture;
    pmrem.dispose();

    this.camera.position.set(0, 0, 9);

    this.bg = new THREE.ShaderMaterial({
      vertexShader: BG_VERT, fragmentShader: BG_FRAG, depthWrite: false, depthTest: false,
      uniforms: { uTime: { value: 0 }, uAspect: { value: new THREE.Vector2(1, 1) }, uDim: { value: 0 } },
    });
    const bgMesh = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.bg);
    bgMesh.frustumCulled = false; bgMesh.renderOrder = -1;
    this.scene.add(bgMesh);

    this.buildHero(onReady);
    this.pts = this.buildPoints();
    this.setField();
    this.resize();
    window.addEventListener("resize", this.resize);
    window.addEventListener("pointermove", this.onPointer, { passive: true });
    this.loop();
  }

  private chrome() {
    return new THREE.MeshPhysicalMaterial({
      color: 0xffffff, metalness: 1, roughness: 0.14, clearcoat: 1, clearcoatRoughness: 0.08,
      iridescence: 1, iridescenceIOR: 1.7, iridescenceThicknessRange: [180, 820], envMapIntensity: 1.5,
    });
  }

  private buildHero(onReady?: () => void) {
    const mat = this.chrome();
    const ring = new THREE.Mesh(new THREE.TorusGeometry(1, 0.075, 64, 240), mat);
    const inner = new THREE.Mesh(new THREE.TorusGeometry(0.86, 0.012, 16, 200), mat);
    this.hero.add(ring, inner);

    // A looping wire that the ring hangs from, crossing once below it.
    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(0, -1.02, 0), new THREE.Vector3(0.55, -1.9, 0.25), new THREE.Vector3(1.05, -3.3, 0),
      new THREE.Vector3(0.35, -4.6, -0.25), new THREE.Vector3(-0.35, -4.6, 0.25), new THREE.Vector3(-1.05, -3.3, 0),
      new THREE.Vector3(-0.55, -1.9, -0.25),
    ], true, "centripetal");
    this.hero.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 420, 0.016, 10, true), mat));

    new THREE.TextureLoader().load("/logo-mark.png", (tex) => {
      tex.colorSpace = THREE.SRGBColorSpace;
      tex.anisotropy = 8;
      const eye = new THREE.Mesh(
        new THREE.PlaneGeometry(1.62, 1.62),
        new THREE.MeshBasicMaterial({ map: tex, transparent: true, toneMapped: false, depthWrite: false }),
      );
      eye.position.z = 0.01;
      this.eye = eye;
      this.hero.add(eye);
      onReady?.();
    }, undefined, () => onReady?.());
    this.scene.add(this.hero);
  }

  private buildPoints() {
    const pos = new Float32Array(N * 3), grid = new Float32Array(N * 3), size = new Float32Array(N), phase = new Float32Array(N);
    const rnd = mulberry(47);
    for (let i = 0; i < N; i++) {
      // Field: a wide, shallow volume, denser near the centre line.
      pos[i * 3] = (rnd() - 0.5) * 18;
      pos[i * 3 + 1] = (rnd() - 0.5) * 11;
      pos[i * 3 + 2] = -7 + rnd() * 10;
      // Grid: booth b (0..99) at row/col, its PER_BOOTH points in a tight cluster.
      const b = Math.floor(i / PER_BOOTH), r = Math.floor(b / 10), c = b % 10;
      const a = rnd() * Math.PI * 2, rr = Math.sqrt(rnd()) * 0.15;
      grid[i * 3] = (c - 4.5) * 0.44 + Math.cos(a) * rr;
      grid[i * 3 + 1] = (4.5 - r) * 0.44 + Math.sin(a) * rr;
      grid[i * 3 + 2] = (rnd() - 0.5) * 0.12;
      size[i] = 0.6 + Math.pow(rnd(), 3) * 2.6;
      phase[i] = rnd();
    }
    this.geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    this.geo.setAttribute("aGrid", new THREE.BufferAttribute(grid, 3));
    this.geo.setAttribute("aSize", new THREE.BufferAttribute(size, 1));
    this.geo.setAttribute("aPhase", new THREE.BufferAttribute(phase, 1));
    this.geo.setAttribute("aColA", new THREE.BufferAttribute(this.colA, 3));
    this.geo.setAttribute("aColB", new THREE.BufferAttribute(this.colB, 3));
    const mat = new THREE.ShaderMaterial({
      vertexShader: PT_VERT, fragmentShader: PT_FRAG, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      uniforms: { uTime: { value: 0 }, uForm: { value: 0 }, uSpread: { value: 1 }, uMix: { value: 1 }, uPx: { value: 1 },
        uFocus: { value: 9 }, uDim: { value: 0 }, uGridX: { value: 0 } },
    });
    const points = new THREE.Points(this.geo, mat);
    points.frustumCulled = false;
    this.scene.add(points);
    return mat;
  }

  // ---------------------------------------------------------------- colour modes

  /** Start a colour change: whatever is on screen now becomes A, the new colours become B. */
  private recolour(paint: (i: number, out: THREE.Color) => void) {
    const t = this.pts.uniforms.uMix.value as number;
    for (let i = 0; i < N * 3; i++) this.colA[i] = this.colA[i] + (this.colB[i] - this.colA[i]) * t;
    const c = new THREE.Color();
    for (let i = 0; i < N; i++) { paint(i, c); this.colB[i * 3] = c.r; this.colB[i * 3 + 1] = c.g; this.colB[i * 3 + 2] = c.b; }
    (this.geo.getAttribute("aColA") as THREE.BufferAttribute).needsUpdate = true;
    (this.geo.getAttribute("aColB") as THREE.BufferAttribute).needsUpdate = true;
    this.mixT = 0;
    this.pts.uniforms.uMix.value = 0;
  }

  /** Ambient field: mostly soft white, a few warm and cool points. */
  setField() {
    const rnd = mulberry(12);
    this.recolour((_, c) => {
      const r = rnd();
      c.copy(r < 0.06 ? C.yellow : r < 0.12 ? C.benign : r < 0.55 ? C.soft : C.dim);
    });
  }

  /** Booth grid coloured by each booth's real outcome (from /overview). */
  setBooths(booths: BoothTint[], highlight = -1) {
    this.recolour((i, c) => {
      const b = Math.floor(i / PER_BOOTH);
      const o = booths[b]?.outcome ?? "normal";
      if (o === "unusual") c.copy(C.yellow);
      else if (o === "likely_benign") c.copy(C.benign);
      else if (o === "mixed") c.copy(i % 2 ? C.yellow : C.white);
      else c.copy(C.grey);
      if (highlight >= 0 && b !== highlight && o !== "normal") c.lerp(C.dim, 0.55);
    });
  }

  /** One booth's removals: each point takes a story in proportion to the real shares (from /stories). */
  setStory(s: StoryTint) {
    const order = ["death_registered", "duplicate_cleanup", "boundary_change", "hostel_moveout", "unexplained"];
    const col: Record<string, THREE.Color> = {
      death_registered: C.death, duplicate_cleanup: C.dupes, boundary_change: C.boundary, hostel_moveout: C.hostel, unexplained: C.yellow,
    };
    const cum: [number, THREE.Color][] = [];
    let acc = 0;
    for (const code of order) {
      const sh = s.shares.find((x) => x.code === code)?.share ?? 0;
      acc += sh; cum.push([acc, col[code]]);
    }
    const rnd = mulberry(3);
    this.recolour((_, c) => {
      const r = rnd() * acc;
      c.copy((cum.find(([v]) => r <= v) ?? cum[cum.length - 1])[1]);
    });
  }

  // ---------------------------------------------------------------- motion

  setPose(p: Partial<Pose>) { Object.assign(this.target, p); }

  private onPointer = (e: PointerEvent) => {
    this.pointer.set((e.clientX / window.innerWidth) * 2 - 1, -(e.clientY / window.innerHeight) * 2 + 1);
  };

  private resize = () => {
    const w = window.innerWidth, h = window.innerHeight;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    // Keep the scene's width on phones: pull the camera back when the screen is narrow.
    this.camera.position.z = w < h ? 9 * Math.min(1.9, (h / w) * 0.85) : 9;
    this.camera.updateProjectionMatrix();
    this.bg.uniforms.uAspect.value.set(w / h, 1);
    this.pts.uniforms.uPx.value = this.renderer.getPixelRatio() * Math.min(1.4, h / 800) * 3.2;
  };

  private loop = () => {
    this.raf = requestAnimationFrame(this.loop);
    const dt = Math.min(this.clock.getDelta(), 0.05);
    const t = this.reduced ? 0 : this.clock.elapsedTime;
    const k = this.reduced ? 1 : 1 - Math.exp(-dt * 3.2); // frame-rate independent easing
    const P = this.pose, T = this.target;
    (Object.keys(T) as (keyof Pose)[]).forEach((key) => { P[key] += (T[key] - P[key]) * k; });
    this.pointerEase.lerp(this.pointer, this.reduced ? 0 : 1 - Math.exp(-dt * 2.5));

    this.hero.position.set(P.x + this.pointerEase.x * 0.25, P.y + Math.sin(t * 0.6) * 0.06 + this.pointerEase.y * 0.15, P.z);
    this.hero.scale.setScalar(P.scale);
    this.hero.rotation.set(-this.pointerEase.y * 0.18 + Math.sin(t * 0.4) * 0.04, P.spin + this.pointerEase.x * 0.35 + Math.sin(t * 0.3) * 0.12, 0);
    if (this.eye) this.eye.rotation.y = -this.hero.rotation.y * 0.6; // the eye keeps facing the viewer

    this.camera.position.x = this.pointerEase.x * 0.3;
    this.camera.position.y = this.pointerEase.y * 0.2;
    this.camera.lookAt(0, 0, 0);

    if (this.mixT < 1) { this.mixT = Math.min(1, this.mixT + dt / 1.1); this.pts.uniforms.uMix.value = ease(this.mixT); }
    this.pts.uniforms.uTime.value = t;
    this.pts.uniforms.uForm.value = P.form;
    this.pts.uniforms.uSpread.value = P.spread;
    this.pts.uniforms.uDim.value = P.dim;
    this.pts.uniforms.uGridX.value = P.gridX;
    this.bg.uniforms.uTime.value = t;
    this.bg.uniforms.uDim.value = P.dim;
    this.renderer.render(this.scene, this.camera);
  };

  dispose() {
    cancelAnimationFrame(this.raf);
    window.removeEventListener("resize", this.resize);
    window.removeEventListener("pointermove", this.onPointer);
    this.renderer.dispose();
  }
}

function ease(x: number) { return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; }

/** Small seeded random, so the field looks the same on every visit. */
function mulberry(a: number) {
  return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
