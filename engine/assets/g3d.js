/* 3D scenes for hindi-shorts-maker (three.js r159, UMD build in assets/vendor/three.min.js).
   A storyboard visual {"type":"3d", "preset": "...", ...} or {"type":"3d", "code": "..."} becomes a
   960x530 WebGL canvas. Every frame is a pure function of time, so renders are repeatable.
   frame(t, lt, step, sp): t = video time, lt = time since scene start, step = beat index in the
   scene, sp = seconds since that beat started. */
window.G3D = (function () {
  const C = { pink:'#ff4d8d', amber:'#ffb020', green:'#2bd67b', cyan:'#22d3ee', blue:'#3b82f6',
              purple:'#a78bfa', red:'#ff5a4e', white:'#ffffff', orange:'#ff8a3d', yellow:'#ffd54a' };
  const col = c => C[c] || c || '#ffffff';
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, p) => a + (b - a) * p;
  const eIO = p => { p = clamp(p); return p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2; };
  function rng(seed) { let a = seed >>> 0 || 1; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

  /* ---------- helpers given to presets and custom code (H) ---------- */
  function makeH(THREE, scene, camera, beats, sceneStart) {
    const H = { THREE, col, clamp, lerp, eIO, rng };
    // value for the current step, eased from the previous step's value over `dur` seconds
    H.stepVal = (arr, step, sp, dur = .8) => {
      if (!Array.isArray(arr)) return arr;
      const i = Math.min(step, arr.length - 1), j = Math.max(0, i - 1);
      return i === 0 ? arr[0] : lerp(arr[j], arr[i], eIO(sp / dur));
    };
    // integral of a per-step speed over scene time: smooth "phase" that never jumps
    H.phase = (lt, speeds) => {
      if (!Array.isArray(speeds)) return lt * (speeds == null ? 1 : speeds);
      let ph = 0;
      for (let k = 0; k < beats.length; k++) {
        const a = (k === 0 ? 0 : beats[k].start - sceneStart), b = k + 1 < beats.length ? beats[k + 1].start - sceneStart : 1e9;
        if (lt <= a) break;
        ph += (Math.min(lt, b) - a) * speeds[Math.min(k, speeds.length - 1)];
      }
      return ph;
    };
    H.lights = (o = {}) => {
      const d = new THREE.DirectionalLight(0xffffff, o.sun ?? 2.6); d.position.set(...(o.dir || [4, 3, 5])); scene.add(d);
      const h = new THREE.HemisphereLight(0x9ec9ff, 0x1a1030, o.fill ?? .55); scene.add(h); return { sun: d, fill: h };
    };
    H.stars = (n = 500, r = 40, seed = 7) => {
      const R = rng(seed), p = new Float32Array(n * 3);
      for (let i = 0; i < n; i++) { const u = R() * 2 - 1, th = R() * 6.283, s = Math.sqrt(1 - u * u), rr = r * (.6 + .4 * R());
        p.set([rr * s * Math.cos(th), rr * u, rr * s * Math.sin(th)], i * 3); }
      const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3));
      const m = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffffff, size: .09, transparent: true, opacity: .8, depthWrite: false }));
      scene.add(m); return m;
    };
    H.canvasTex = (w, h, draw) => { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
      const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t; };
    H.glow = (color, size = 2, strength = 1) => {
      const t = H.canvasTex(128, 128, (g, w) => { const r = g.createRadialGradient(64, 64, 0, 64, 64, 64);
        r.addColorStop(0, 'rgba(255,255,255,1)'); r.addColorStop(.25, 'rgba(255,255,255,.55)'); r.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = r; g.fillRect(0, 0, w, w); });
      const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, color: new THREE.Color(col(color)), transparent: true, opacity: strength, blending: THREE.AdditiveBlending, depthWrite: false }));
      s.scale.set(size, size, 1); return s;
    };
    H.label = (text, o = {}) => {
      const fs = 64, pad = 24, c = document.createElement('canvas'), g = c.getContext('2d');
      g.font = `700 ${fs}px Poppins, sans-serif`; const w = Math.ceil(g.measureText(text).width) + pad * 2; c.width = w; c.height = fs + pad * 1.6;
      g.font = `700 ${fs}px Poppins, sans-serif`; g.fillStyle = o.bg || 'rgba(10,12,20,.72)';
      const r = c.height / 2; g.beginPath(); g.roundRect(0, 0, w, c.height, r); g.fill();
      g.fillStyle = col(o.color || 'white'); g.textBaseline = 'middle'; g.fillText(text, pad, c.height / 2 + 2);
      const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
      const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, transparent: true, depthTest: false }));
      const hgt = o.size || .42; s.scale.set(hgt * w / c.height, hgt, 1); s.renderOrder = 10; return s;
    };
    H.rim = (radius, color, power = 2.6, strength = 1.2) => new THREE.Mesh(new THREE.SphereGeometry(radius, 64, 32),
      new THREE.ShaderMaterial({ uniforms: { c: { value: new THREE.Color(col(color)) }, p: { value: power }, k: { value: strength } },
        vertexShader: 'varying vec3 vN; varying vec3 vV; void main(){ vec4 mv=modelViewMatrix*vec4(position,1.); vN=normalize(normalMatrix*normal); vV=normalize(-mv.xyz); gl_Position=projectionMatrix*mv; }',
        fragmentShader: 'uniform vec3 c; uniform float p; uniform float k; varying vec3 vN; varying vec3 vV; void main(){ float f=pow(1.-max(dot(vN,vV),0.),p)*k; gl_FragColor=vec4(c*f,f); }',
        transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
    // seamless planet texture from 3D value noise
    H.planetTex = (o = {}) => {
      const R = rng(o.seed || 3), N = 64, tab = new Float32Array(N * N * N); for (let i = 0; i < tab.length; i++) tab[i] = R();
      const hs = (x, y, z) => tab[((x & 63) * N + (y & 63)) * N + (z & 63)], sm = t => t * t * (3 - 2 * t);
      const vn = (x, y, z) => { const X = Math.floor(x), Y = Math.floor(y), Z = Math.floor(z), fx = sm(x - X), fy = sm(y - Y), fz = sm(z - Z);
        const L = (a, b, t) => a + (b - a) * t;
        return L(L(L(hs(X, Y, Z), hs(X + 1, Y, Z), fx), L(hs(X, Y + 1, Z), hs(X + 1, Y + 1, Z), fx), fy),
                 L(L(hs(X, Y, Z + 1), hs(X + 1, Y, Z + 1), fx), L(hs(X, Y + 1, Z + 1), hs(X + 1, Y + 1, Z + 1), fx), fy), fz); };
      const fbm = (x, y, z) => { let s = 0, a = .5, f = 1; for (let i = 0; i < 5; i++) { s += a * vn(x * f + 17, y * f + 31, z * f + 7); a *= .5; f *= 2.03; } return s; };
      return H.canvasTex(512, 256, (g, w, h) => {
        const im = g.createImageData(w, h), d = im.data, sea = o.sea ?? .5;
        for (let j = 0; j < h; j++) { const lat = (.5 - j / h) * Math.PI, cy = Math.sin(lat), cr = Math.cos(lat);
          for (let i = 0; i < w; i++) { const lon = i / w * 2 * Math.PI, x = cr * Math.cos(lon), z = cr * Math.sin(lon);
            const n = fbm(x * 2.2 + 3, cy * 2.2 + 3, z * 2.2 + 3), k = (j * w + i) * 4, ice = Math.abs(lat) > 1.22;
            let r, gg, b;
            if (o.clouds) { const a = clamp((n - .5) * 3.2); r = gg = b = 255; d[k + 3] = a * 235; d[k] = r; d[k + 1] = gg; d[k + 2] = b; continue; }
            if (ice) { r = 235; gg = 244; b = 255; }
            else if (n < sea) { const q = n / sea; r = 10 + 20 * q; gg = 50 + 70 * q; b = 120 + 90 * q; }
            else { const q = clamp((n - sea) / .22); r = lerp(70, 150, q); gg = lerp(150, 120, q); b = lerp(60, 70, q); if (q > .8) { r = 170; gg = 150; b = 130; } }
            d[k] = r; d[k + 1] = gg; d[k + 2] = b; d[k + 3] = 255; } }
        g.putImageData(im, 0, 0); });
    };
    H.env = (renderer, o = {}) => {
      const tex = H.canvasTex(512, 256, (g, w, h) => { const gr = g.createLinearGradient(0, 0, 0, h);
        gr.addColorStop(0, o.top || '#dfe9ff'); gr.addColorStop(.48, o.mid || '#7d8aa8'); gr.addColorStop(.52, '#3a3f52'); gr.addColorStop(1, o.bottom || '#141622');
        g.fillStyle = gr; g.fillRect(0, 0, w, h); g.fillStyle = 'rgba(255,255,255,.95)'; g.fillRect(w * .18, h * .14, w * .16, h * .1); g.fillRect(w * .62, h * .2, w * .1, h * .08); });
      tex.mapping = THREE.EquirectangularReflectionMapping;
      const pm = new THREE.PMREMGenerator(renderer); scene.environment = pm.fromEquirectangular(tex).texture; pm.dispose(); };
    H.ring = (radius, color, opacity = .35) => { const pts = []; for (let i = 0; i <= 128; i++) { const a = i / 128 * 6.2832; pts.push(new THREE.Vector3(Math.cos(a) * radius, 0, Math.sin(a) * radius)); }
      return new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: col(color), transparent: true, opacity })); };
    return H;
  }

  /* ---------- presets ---------- */
  const PRESETS = {
    // rotating Earth with clouds, atmosphere glow, optional sunlight rays and scattered blue light
    earth(THREE, scene, camera, v, H) {
      camera.position.set(0, .3, 5.4); camera.lookAt(0, 0, 0); H.stars(600);
      const L = H.lights({ dir: v.sunDir || [-5, 1.5, 3], sun: 3, fill: .35 });
      const earth = new THREE.Mesh(new THREE.SphereGeometry(1.5, 96, 48), new THREE.MeshStandardMaterial({ map: H.planetTex({ seed: 5 }), roughness: .85, metalness: 0 }));
      const clouds = new THREE.Mesh(new THREE.SphereGeometry(1.53, 96, 48), new THREE.MeshStandardMaterial({ map: H.planetTex({ seed: 11, clouds: true }), transparent: true, depthWrite: false }));
      const atmo = H.rim(1.62, v.atmosphere || '#5fb4ff', 2.4, 1.4);
      const tilt = new THREE.Group(); tilt.rotation.z = .41; tilt.add(earth, clouds); scene.add(tilt, atmo);
      let rays = null, dots = [];
      if (v.rays) { // white sunlight streaming in from the left; part of it turns blue and scatters at the atmosphere
        rays = new THREE.Group(); scene.add(rays); const R = H.rng(9);
        for (let i = 0; i < 46; i++) { const m = new THREE.Mesh(new THREE.SphereGeometry(.035, 8, 8), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true }));
          m.userData = { y: (R() - .5) * 2.6, z: (R() - .5) * 1.2, off: R(), sc: R() < .5, ang: R() * 6.283, el: (R() - .5) * 2 }; rays.add(m); dots.push(m); }
      }
      const extra = v.labels ? v.labels.map(l => { const s = H.label(l.text, l); s.position.set(...l.at); s.userData.step = l.step || 0; scene.add(s); return s; }) : [];
      return (t, step, sp, lt) => {
        tilt.rotation.y = H.phase(lt, v.spin ?? .22); clouds.rotation.y = lt * .03;
        const sunset = v.sunsetStep != null && step >= v.sunsetStep ? eIO(sp / 2) : 0;
        atmo.material.uniforms.c.value.set(col(v.atmosphere || '#5fb4ff')).lerp(new THREE.Color('#ff7a2e'), sunset);
        L.sun.intensity = 3 - 1.2 * sunset;
        camera.position.x = Math.sin(lt * .12) * .35; camera.lookAt(0, 0, 0);
        if (rays) { const scat = v.scatterStep == null || step >= v.scatterStep;
          dots.forEach(m => { const u = m.userData, p = (lt * .45 + u.off) % 1, x = lerp(-6.5, -1.55, p), pHit = (6.5 - 2.0) / 4.95;
            if (scat && u.sc && p > pHit) { const q = (p - pHit) / (1 - pHit); m.material.color.set('#4aa8ff');
              m.position.set(-2.0 + Math.cos(u.ang) * q * 2.2, u.y + Math.sin(u.ang) * q * 2.2, u.z + u.el * q); m.material.opacity = clamp(1 - q); }
            else { m.material.color.set('#fff6d0'); m.position.set(x, u.y, u.z); m.material.opacity = 1; } }); }
        extra.forEach(s => s.material.opacity = step >= s.userData.step ? clamp((step > s.userData.step ? 1 : sp / .5)) : 0);
      };
    },

    // particles in a box; speed and colour per step (heat), optional boiling: some escape upward
    molecules(THREE, scene, camera, v, H) {
      camera.position.set(0, 1.2, 6.4); camera.lookAt(0, 0, 0); H.lights({ dir: [3, 5, 4] });
      const W = 3.8, Ht = 2.4, D = 2.2, box = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(W, Ht, D)), new THREE.LineBasicMaterial({ color: 0x9fb3ff, transparent: true, opacity: .45 }));
      const grp = new THREE.Group(); grp.add(box); scene.add(grp);
      const N = v.count || 46, R = H.rng(21), P = [], geo = new THREE.SphereGeometry(.11, 20, 14);
      for (let i = 0; i < N; i++) { const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: col(v.colors ? v.colors[0] : '#4aa8ff'), roughness: .35, emissive: 0x000000 }));
        m.userData = { p: [R() * W, R() * Ht, R() * D], v: [R() - .5, R() - .5, R() - .5].map(x => x * 2), esc: R() }; grp.add(m); P.push(m); }
      const tri = (x, L) => { x = ((x % (2 * L)) + 2 * L) % (2 * L); return x < L ? x : 2 * L - x; };
      const speeds = v.speeds || [1], cols = (v.colors || ['#4aa8ff']).map(c => new THREE.Color(col(c)));
      return (t, step, sp, lt) => {
        const ph = H.phase(lt, speeds) * .9, c = cols[Math.min(step, cols.length - 1)], c0 = cols[Math.max(0, Math.min(step, cols.length - 1) - 1)], cm = c0.clone().lerp(c, eIO(sp / .8));
        const escOn = v.escapeStep != null && step >= v.escapeStep, frac = v.escapeFraction ?? .3;
        P.forEach(m => { const u = m.userData; let x = tri(u.p[0] + u.v[0] * ph, W) - W / 2, y = tri(u.p[1] + u.v[1] * ph, Ht) - Ht / 2, z = tri(u.p[2] + u.v[2] * ph, D) - D / 2;
          if (escOn && u.esc < frac) { const e = Math.max(0, sp - u.esc * 2); y += e * 1.4; m.material.opacity = clamp(1 - e / 2.2); m.material.transparent = true; }
          m.position.set(x, y, z); m.material.color.copy(cm); });
        grp.rotation.y = Math.sin(lt * .25) * .35 - .2; grp.rotation.x = .12;
      };
    },

    // Sun, Earth and Moon on their orbits (seasons, moon phases, day/night)
    orbit(THREE, scene, camera, v, H) {
      camera.position.set(0, 4.2, 7.2); camera.lookAt(0, 0, 0); H.stars(500);
      const sun = new THREE.Mesh(new THREE.SphereGeometry(.85, 48, 32), new THREE.MeshBasicMaterial({ color: 0xffc640 }));
      const glow = H.glow('#ffb020', 4.2, .9); sun.add(glow); scene.add(sun);
      const pl = new THREE.PointLight(0xffffff, 3.2, 0, 0); scene.add(pl); scene.add(new THREE.AmbientLight(0xffffff, .08));
      const ER = v.earthOrbit || 3.3, earthPivot = new THREE.Group(); scene.add(earthPivot, H.ring(ER, '#8fb0ff'));
      const earth = new THREE.Mesh(new THREE.SphereGeometry(.34, 48, 32), new THREE.MeshStandardMaterial({ map: H.planetTex({ seed: 5 }), roughness: .9 }));
      earth.position.x = ER; earthPivot.add(earth); earth.add(H.rim(.37, '#5fb4ff', 2.4, 1));
      const moonPivot = new THREE.Group(); earth.add(moonPivot); moonPivot.add(H.ring(.8, '#cfd6e6', .25));
      const moon = new THREE.Mesh(new THREE.SphereGeometry(.1, 32, 20), new THREE.MeshStandardMaterial({ color: 0xd9dbe2, roughness: 1 })); moon.position.x = .8; moonPivot.add(moon);
      const labs = (v.labels !== false) ? [['Sun', sun, [0, 1.25, 0]], ['Earth', earth, [0, .62, 0]], ['Moon', moon, [0, .3, 0]]].map(([t, o, at]) => { const s = H.label(v.names?.[t] || t, { size: .3 }); s.position.set(...at); o.add(s); return s; }) : [];
      return (t, step, sp, lt) => {
        earthPivot.rotation.y = -H.phase(lt, v.earthSpeed ?? .25); earth.rotation.y = lt * 1.2; moonPivot.rotation.y = -H.phase(lt, v.moonSpeed ?? 1.4);
        const f = v.focusStep != null && step >= v.focusStep ? eIO(sp / 1.6) : 0;
        const ep = new THREE.Vector3(); earth.getWorldPosition(ep);
        camera.position.set(lerp(Math.sin(lt * .1) * 1.2, ep.x * 1.0 + 1.6, f), lerp(4.2, 1.3, f), lerp(7.2, ep.z + 2.4, f));
        camera.lookAt(lerp(0, ep.x, f), 0, lerp(0, ep.z, f));
        glow.material.opacity = .8 + .15 * Math.sin(t * 2); labs.forEach(l => l.material.opacity = 1 - f);
      };
    },

    // atom: nucleus of protons/neutrons, electrons racing on tilted orbits
    atom(THREE, scene, camera, v, H) {
      camera.position.set(0, .4, 6); camera.lookAt(0, 0, 0); H.lights({ dir: [3, 4, 5] });
      const nuc = new THREE.Group(), R = H.rng(4), n = v.nucleons || 12; scene.add(nuc);
      for (let i = 0; i < n; i++) { const p = new THREE.Mesh(new THREE.SphereGeometry(.2, 24, 16), new THREE.MeshStandardMaterial({ color: i % 2 ? 0xff5a4e : 0x9aa4b8, roughness: .4 }));
        const u = R() * 2 - 1, a = R() * 6.283, r = .32 * Math.cbrt(R()); p.position.set(r * Math.sqrt(1 - u * u) * Math.cos(a), r * u, r * Math.sqrt(1 - u * u) * Math.sin(a)); nuc.add(p); }
      nuc.add(H.glow('#ff8a3d', 1.6, .35));
      const orbs = [], k = v.shells || 3;
      for (let i = 0; i < k; i++) { const g = new THREE.Group(); g.rotation.set(i * 1.05 + .3, i * .7, 0); const rr = 1.5 + i * .35; g.add(H.ring(rr, '#22d3ee', .4));
        const e = new THREE.Mesh(new THREE.SphereGeometry(.08, 16, 12), new THREE.MeshBasicMaterial({ color: 0x9ff3ff })); e.add(H.glow('#22d3ee', .55, .9)); e.userData.r = rr; g.add(e); scene.add(g); orbs.push(e); }
      return (t, step, sp, lt) => {
        const ph = H.phase(lt, v.speeds || [1.6]);
        orbs.forEach((e, i) => { const a = ph * (1 + i * .3) + i * 2; e.position.set(Math.cos(a) * e.userData.r, 0, Math.sin(a) * e.userData.r); });
        nuc.rotation.y = lt * .4; nuc.rotation.x = Math.sin(lt * .3) * .3;
      };
    },

    // ripples on a surface: sound waves, water waves, vibrations
    waves(THREE, scene, camera, v, H) {
      camera.position.set(0, 3.4, 5.4); camera.lookAt(0, -.2, 0); H.lights({ dir: [2, 6, 3], fill: .6 });
      const geo = new THREE.PlaneGeometry(9, 6, 140, 94); geo.rotateX(-Math.PI / 2);
      const base = geo.attributes.position.array.slice(), cA = new THREE.Color(col(v.color || '#22d3ee')), cB = new THREE.Color(col(v.color2 || '#a78bfa'));
      const colors = new Float32Array(base.length); geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
      const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: .35, metalness: .1, side: THREE.DoubleSide })); scene.add(mesh);
      const src = new THREE.Mesh(new THREE.SphereGeometry(.16, 20, 14), new THREE.MeshBasicMaterial({ color: 0xffffff })); src.add(H.glow(v.color || '#22d3ee', 1.2, .8)); scene.add(src);
      const tmp = new THREE.Color();
      return (t, step, sp, lt) => {
        const A = H.stepVal(v.amplitude || [.25], step, sp), ph = H.phase(lt, v.speeds || [3]), k = v.wavelength ? 6.283 / v.wavelength : 4.2, flat = v.source === 'line';
        const p = geo.attributes.position.array;
        for (let i = 0; i < p.length; i += 3) { const x = base[i], z = base[i + 2], r = flat ? (x + 4.5) : Math.hypot(x, z);
          const y = A * Math.sin(k * r - ph) * Math.exp(-r * (v.damping ?? .18)); p[i + 1] = y;
          tmp.copy(cA).lerp(cB, clamp(.5 + y / (2 * Math.max(A, .01)))); colors[i] = tmp.r; colors[i + 1] = tmp.g; colors[i + 2] = tmp.b; }
        geo.attributes.position.needsUpdate = true; geo.attributes.color.needsUpdate = true; geo.computeVertexNormals();
        src.position.set(flat ? -4.5 : 0, .25 + .05 * Math.sin(ph * 2), 0); mesh.rotation.y = Math.sin(lt * .15) * .15;
      };
    },
  };

  function create(canvas, v, s) {
    if (!window.THREE) throw new Error('3d visual: three.js did not load');
    const THREE = window.THREE;
    const r = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: true });
    r.setPixelRatio(1); r.setSize(960, 530, false); r.outputColorSpace = THREE.SRGBColorSpace;
    r.toneMapping = THREE.ACESFilmicToneMapping; r.toneMappingExposure = v.exposure || 1.1;
    const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera(v.fov || 38, 960 / 530, .05, 300);
    const H = makeH(THREE, scene, camera, s._t.beats, s._t.start);
    const space = ['earth', 'orbit'].includes(v.preset);
    if (v.env === true || (v.env !== false && !space)) H.env(r);
    let upd;
    if (v.code) upd = new Function('THREE', 'scene', 'camera', 'v', 'H', v.code)(THREE, scene, camera, v, H);
    else { const P = PRESETS[v.preset]; if (!P) throw new Error('3d visual: unknown preset ' + v.preset + ' (use ' + Object.keys(PRESETS).join(', ') + ' or code)'); upd = P(THREE, scene, camera, v, H); }
    if (typeof upd !== 'function') throw new Error('3d visual: code must return an update function (t, step, sp, lt) => {}');
    return { frame(t, lt, step, sp) { upd(t, step, sp, lt); r.render(scene, camera); } };
  }
  return { create, presets: () => Object.keys(PRESETS) };
})();
