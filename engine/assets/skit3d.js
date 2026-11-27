/* Real-time 3D look for skits ("look": "3d" in a skit storyboard). three.js r159 (assets/vendor/three.min.js).
   Rigged, code-built cast (round toy/Pixar-like style) that turns a full 360 degrees, walks in, blinks,
   lip-syncs and acts the existing pose names; 3D sets; one continuous camera that glides between
   framings and keeps every character either fully in frame or out of it (no half bodies).
   Everything is a pure function of time t, so frames render the same every time.
   skit.html calls S3D.render(t) each frame and S3D.screen(id) for stickers/fx/overlays. */
window.S3D = (function () {
  const T = THREE, W = 1080, H = 1920, D = Math.PI / 180;
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x)), lerp = (a, b, p) => a + (b - a) * p;
  const eIO = p => { p = clamp(p); return p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; };
  const eOut = p => 1 - Math.pow(1 - clamp(p), 3);
  const hash = s => { let h = 2166136261; for (const c of String(s)) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return (h >>> 0) / 4294967296; };
  const rng = seed => { let a = (seed * 4294967296) >>> 0 || 1; return () => { a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; };
  const MAT = {};
  const mat = (c, o = {}) => { const k = c + JSON.stringify(o); if (!MAT[k]) MAT[k] = new T.MeshStandardMaterial(Object.assign({ color: c, roughness: .72, metalness: 0 }, o)); return MAT[k]; };
  const mesh = (g, m, cast = true) => { const x = new T.Mesh(g, m); x.castShadow = cast; x.receiveShadow = true; return x; };
  const grp = () => new T.Group();
  const at = (o, x, y, z) => { o.position.set(x, y, z); return o; };

  /* ------------------------------------------------------------------ cast look */
  const SPEC = {
    golu: { skin: '#E3A97C', shirt: '#BFDFFF', pants: '#22314F', shorts: true, hair: 'spiky', scale: .86, tie: true, kid: true },
    mummy: { skin: '#C98B62', shirt: '#E2B33C', saree: '#8A1F52', border: '#E2B33C', hair: 'bun', bindi: true, scale: .96, fem: true, lips: '#a8424f' },
    papa: { skin: '#B97A4C', shirt: '#F4F1E6', kurta: true, pants: '#D9D4C4', hair: 'bald', mooch: true, specsUp: true, scale: 1, belly: true },
    dadi: { skin: '#C68E64', shirt: '#F3EFE4', saree: '#F7F3EA', border: '#2F6BD8', hair: 'greybun', specs: true, stick: true, scale: .9, fem: true, brow: '#bdb8b0' },
    pinky: { skin: '#D9A07A', shirt: '#FF7AA8', pants: '#3B5BA9', hair: 'ponytail', phone: true, scale: .93, fem: true, lips: '#c4505f' },
    bunty: { skin: '#E0A77A', shirt: '#FFFFFF', pants: '#22314F', hair: 'neat', tie: true, specs: true, scale: .86, kid: true },
    dadaji: { skin: '#BF865C', shirt: '#F7F3EA', kurta: true, pants: '#EDE8DA', hair: 'whiteside', mooch: true, moochC: '#ECE8E0', specs: true, shawl: '#8A5A3C', scale: .95, brow: '#e6e2da' },
    chutki: { skin: '#E6AE82', shirt: '#FF6FA0', frock: true, frockC: '#FF6FA0', hair: 'pigtails', scale: .72, kid: true, fem: true, lips: '#d0606e' },
    gupta: { skin: '#C48A5E', shirt: '#F2A23A', pants: '#5A4632', hair: 'cap', capC: '#2F6BD8', mooch: true, belly: true, chain: true, checks: true, scale: 1 },
    raju: { skin: '#C99068', shirt: '#3C8C7A', pants: '#2B3A55', hair: 'messy', beard: true, headphones: true, hoodie: true, scale: .98 },
    aunty: { skin: '#C98B62', shirt: '#3BAA6A', saree: '#E8418A', border: '#3BAA6A', hair: 'curly', bindi: true, bigBindi: true, scale: .98, belly: true, fem: true, lips: '#b03a52' },
    masterji: { skin: '#C68E64', shirt: '#F4F1E6', vest: '#7A4A2A', pants: '#5B4636', hair: 'bald', hairC: '#3a2a22', mooch: true, specs: true, scale: 1.02, belly: true },
  };
  const HAIR = '#1f1612';

  function checksTex(c) {
    const cv = document.createElement('canvas'); cv.width = cv.height = 64; const g = cv.getContext('2d');
    g.fillStyle = c; g.fillRect(0, 0, 64, 64); g.fillStyle = 'rgba(120,40,10,.35)';
    for (let i = 0; i < 4; i++) { g.fillRect(i * 16, 0, 5, 64); g.fillRect(0, i * 16, 64, 5); }
    const t = new T.CanvasTexture(cv); t.wrapS = t.wrapT = T.RepeatWrapping; t.repeat.set(4, 3); t.colorSpace = T.SRGBColorSpace; return t;
  }

  // place a face feature on the head sphere: elevation el, azimuth az (radians), at radius r
  function onHead(o, R, el, az, r = 1) {
    const d = new T.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), Math.cos(az) * Math.cos(el));
    o.position.copy(d.clone().multiplyScalar(R * r));
    o.quaternion.setFromUnitVectors(new T.Vector3(0, 0, 1), d); return o;
  }
  function tube(pts, r, m) { return mesh(new T.TubeGeometry(new T.CatmullRomCurve3(pts.map(p => new T.Vector3(...p))), 20, r, 8, false), m); }
  function capsule(r, len, m) { const x = mesh(new T.CapsuleGeometry(r, len, 6, 14), m); return x; }

  function buildChar(id) {
    const S = SPEC[id] || SPEC.golu, k = S.scale || 1, kid = !!S.kid;
    const OWN = {}; const mat = (c, o = {}) => { const key = c + JSON.stringify(o); if (!OWN[key]) OWN[key] = new T.MeshStandardMaterial(Object.assign({ color: c, roughness: .72, metalness: 0 }, o)); return OWN[key]; };
    const legL = kid ? .6 * k : .74 * k, torso = kid ? .5 * k : .6 * k, R = kid ? .34 * (.6 + .4 * k) * 1.08 : .32 * (.6 + .4 * k);
    const shW = (S.fem ? .19 : .22) * (kid ? k * 1.05 : k), hipW = .095 * k * (kid ? 1.1 : 1), limb = (kid ? .06 : .068) * (kid ? 1.05 : k);
    const armU = .33 * k, armL = .30 * k;
    const skin = mat(S.skin, { roughness: .55 }), cloth = mat(S.shirt, { roughness: .85 }), pantsM = mat(S.pants || S.shirt, { roughness: .85 });
    const hairM = mat(S.hairC || (S.hair === 'greybun' ? '#cfcac2' : S.hair === 'whiteside' ? '#eeeae2' : HAIR), { roughness: .5 });
    const shirtM = S.checks ? new T.MeshStandardMaterial({ map: checksTex(S.shirt), roughness: .85 }) : cloth;
    const root = grp(), body = grp(); root.add(body);
    const hips = grp(); hips.position.y = legL; body.add(hips);
    // legs
    const legs = [];
    for (const s of [1, -1]) {
      const th = grp(); th.position.set(s * hipW, 0, 0); hips.add(th);
      const longLeg = S.shorts ? skin : pantsM;
      const tm = capsule(limb * 1.28, legL * .5 - limb, S.shorts ? pantsM : pantsM); tm.position.y = -legL * .25; th.add(tm);
      const kn = grp(); kn.position.y = -legL * .5; th.add(kn);
      const sm = capsule(limb * 1.1, legL * .5 - limb * 1.2, S.shorts || S.frock ? skin : longLeg); sm.position.y = -legL * .25; kn.add(sm);
      if (S.shorts || S.frock) { const sock = mesh(new T.CylinderGeometry(limb * 1.15, limb * 1.15, .08, 14), mat('#f4f4f4')); sock.position.y = -legL * .45; kn.add(sock); }
      const shoe = mesh(new T.SphereGeometry(1, 20, 12), mat(S.fem && !kid ? '#7a4a2a' : '#2a2a30', { roughness: .45 }));
      shoe.scale.set(limb * 1.45, limb * .95, limb * 2.3); shoe.position.set(0, -legL * .5 + limb * .55, limb * .9); kn.add(shoe);
      legs.push({ th, kn, s });
    }
    // torso
    const spine = grp(); hips.add(spine);
    const bw = S.belly ? 1.18 : 1, prof = [[.001, -.02], [.17 * k * bw * .95, 0], [.175 * k * bw, torso * .3], [.18 * k * (S.fem ? .95 : 1), torso * .62], [.17 * k, torso * .86], [.10 * k, torso * .98], [.055 * k, torso * 1.02]];
    const tor = mesh(new T.LatheGeometry(prof.map(p => new T.Vector2(p[0] * (kid ? 1.05 : 1), p[1])), 28), S.vest ? mat(S.vest, { roughness: .9 }) : shirtM);
    tor.scale.z = .78; spine.add(tor);
    if (S.vest) { const col = mesh(new T.CylinderGeometry(.06 * k, .1 * k, .1, 16), cloth); col.position.y = torso * .97; spine.add(col); }
    // lower garments that hang from the hips
    const skirtProf = (top, bot, len, flare) => mesh(new T.LatheGeometry([[top, 0], [lerp(top, bot, .5) * flare, -len * .5], [bot, -len], [bot * .98, -len - .01]].reverse().map(p => new T.Vector2(p[0], p[1])), 28), null);
    let skirt = null;
    if (S.saree || S.kurta || S.frock) {
      const len = S.saree ? legL * .97 : S.kurta ? legL * .62 : legL * .45, top = .17 * k * bw, bot = S.saree ? .22 * k : S.kurta ? .23 * k * bw : .27 * k;
      skirt = skirtProf(top, bot, len, 1.02); skirt.material = S.saree ? mat(S.saree, { roughness: .8 }) : S.frock ? mat(S.frockC, { roughness: .85 }) : cloth;
      skirt.scale.z = .85; skirt.position.y = S.kurta ? torso * .05 : 0; hips.add(skirt); skirt.castShadow = true;
      if (S.saree && S.border) { const b = mesh(new T.TorusGeometry(bot * 1.0, .018, 8, 40), mat(S.border)); b.rotation.x = Math.PI / 2; b.scale.y = .85; b.position.y = -len + .03; hips.add(b); }
      if (S.saree) { // pallu across the chest, right hip to left shoulder
        const p = tube([[-.14 * k, .02, .13 * k], [-.02, torso * .4, .17 * k], [.1 * k, torso * .78, .14 * k], [.16 * k, torso * .95, .02], [.12 * k, torso * .85, -.12 * k]], .05 * k, mat(S.saree, { roughness: .8 }));
        p.scale.z = 1; spine.add(p);
      }
    }
    if (S.tie) { const tie = mesh(new T.BoxGeometry(.05 * k, torso * .45, .02), mat('#d2413a')); tie.position.set(0, torso * .65, .15 * k); tie.rotation.x = -.15; spine.add(tie); }
    if (S.hoodie) { const hood = mesh(new T.TorusGeometry(.1 * k, .045 * k, 10, 24), cloth); hood.position.set(0, torso * .97, -.05); hood.rotation.x = Math.PI / 2.4; spine.add(hood);
      const pk = mesh(new T.BoxGeometry(.2 * k, .09 * k, .03), mat('#2f7363')); pk.position.set(0, torso * .28, .155 * k); spine.add(pk); }
    if (S.shawl) { const sh = mesh(new T.TorusGeometry(.15 * k, .06 * k, 10, 28), mat(S.shawl, { roughness: .95 })); sh.rotation.x = Math.PI / 2; sh.scale.set(1.15, 1, 1); sh.position.y = torso * .9; spine.add(sh);
      for (const s of [1, -1]) { const e = capsule(.05 * k, torso * .35, mat(S.shawl, { roughness: .95 })); e.position.set(s * .08 * k, torso * .62, .13 * k); spine.add(e); } }
    if (S.chain) { const c = mesh(new T.TorusGeometry(.1 * k, .012, 8, 30), mat('#f2c335', { metalness: .8, roughness: .25 })); c.position.set(0, torso * .86, .06); c.rotation.x = Math.PI / 2.6; spine.add(c); }
    // arms
    const arms = [];
    for (const s of [1, -1]) {
      const sh = grp(); sh.position.set(s * shW * .95, torso * .88, 0); sh.rotation.order = 'ZXY'; spine.add(sh);
      const fullSleeve = S.kurta || S.hoodie || S.vest;
      const um = capsule(limb, armU - limb, (S.vest ? cloth : (S.saree ? mat(S.shirt) : shirtM))); um.position.y = -armU * .5; sh.add(um);
      const el = grp(); el.position.y = -armU; el.rotation.order = 'ZXY'; sh.add(el);
      const fm = capsule(limb * .9, armL - limb, fullSleeve ? (S.vest ? cloth : shirtM) : skin); fm.position.y = -armL * .5; el.add(fm);
      if (S.bangles || S.fem && !kid) { const bg = mesh(new T.TorusGeometry(limb * 1.0, .012, 6, 18), mat('#e8b93c', { metalness: .7, roughness: .3 })); bg.rotation.x = Math.PI / 2; bg.position.y = -armL * .85; el.add(bg); }
      const hand = grp(); hand.position.y = -armL; el.add(hand);
      const hm = mesh(new T.SphereGeometry(limb * 1.3, 16, 12), skin); hm.scale.set(1, 1.1, .8); hm.position.y = -limb * .9; hand.add(hm);
      const thumb = capsule(limb * .42, limb * .7, skin); thumb.position.set(-s * limb * 1.05, -limb * .55, limb * .5); thumb.rotation.z = s * .5; hand.add(thumb);
      const finger = capsule(limb * .38, limb * 1.6, skin); finger.position.set(0, -limb * 2.6, limb * .25); finger.visible = false; hand.add(finger);
      arms.push({ sh, el, hand, finger, s });
    }
    // neck + head
    const neck = grp(); neck.position.y = torso; spine.add(neck);
    const nm = mesh(new T.CylinderGeometry(.055 * k, .06 * k, .1, 14), skin); nm.position.y = .03; neck.add(nm);
    const head = grp(); head.position.y = .04 + R * .9; neck.add(head);
    const hs = mesh(new T.SphereGeometry(R, 40, 28), skin); hs.scale.set(1, 1.04, .96); head.add(hs);
    for (const s of [1, -1]) { const ear = mesh(new T.SphereGeometry(R * .2, 14, 10), skin); ear.scale.set(.6, 1, .8); onHead(ear, R, 0, s * 1.5, .96); head.add(ear); }
    const nose = mesh(new T.SphereGeometry(R * .11, 16, 12), mat(S.skin, { roughness: .5 })); nose.scale.set(1.1, .85, 1); onHead(nose, R, -.15, 0, .96); head.add(nose);
    if (kid || S.fem) for (const s of [1, -1]) { const ck = mesh(new T.CircleGeometry(R * .14, 20), new T.MeshStandardMaterial({ color: '#ff6f7a', transparent: true, opacity: .28, roughness: 1 }), false); onHead(ck, R, -.2, s * .55, 1.005); head.add(ck); }
    // eyes
    const eyes = [], re = R * (kid ? .3 : .26);
    const scl = mat('#fbfaf6', { roughness: .15 }), iris = new T.MeshStandardMaterial({ color: '#4a2c16', roughness: .3 }), pup = new T.MeshBasicMaterial({ color: '#0d0806' }), glint = new T.MeshBasicMaterial({ color: '#ffffff' });
    for (const s of [1, -1]) {
      const eg = grp(); onHead(eg, R, .02, s * .38, .84); head.add(eg);
      const flat = grp(); flat.scale.z = .62; eg.add(flat);
      flat.add(mesh(new T.SphereGeometry(re, 24, 18), scl, false));
      const up = mesh(new T.SphereGeometry(re * 1.1, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), skin, false); flat.add(up);
      const lo = mesh(new T.SphereGeometry(re * 1.08, 24, 12, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), skin, false); flat.add(lo);
      const ir = grp(); ir.position.z = re * .63; eg.add(ir);
      ir.add(new T.Mesh(new T.CircleGeometry(re * .6, 28), iris));
      const p = new T.Mesh(new T.CircleGeometry(re * .33, 20), pup); p.position.z = .001; ir.add(p);
      const g1 = new T.Mesh(new T.CircleGeometry(re * .16, 12), glint); g1.position.set(re * .2, re * .22, .002); ir.add(g1); const g2 = new T.Mesh(new T.CircleGeometry(re * .07, 10), glint); g2.position.set(-re * .18, -re * .15, .002); ir.add(g2);
      eyes.push({ eg, up, lo, ir, s });
    }
    const browM = mat(S.brow || (S.hair === 'whiteside' ? '#e6e2da' : '#2a1a12'), { roughness: .6 });
    const brows = [1, -1].map(s => { const b = grp(); onHead(b, R, .4, s * .37, 1.0); head.add(b);
      const c = capsule(R * .055, R * .24, browM); c.rotation.z = Math.PI / 2; b.add(c); return { b, c, s }; });
    // mouth
    const mouth = grp(); onHead(mouth, R, -.36, 0, .99); head.add(mouth);
    const lineM = mat('#5a2418', { roughness: .6 });
    const arcPts = (w, d) => [[-w, d, 0], [-w * .5, d * .25 - d * .6, .006], [0, -d * .2, .008], [w * .5, d * .25 - d * .6, .006], [w, d, 0]];
    const lines = {
      smile: tube(arcPts(R * .22, R * .08), R * .026, lineM), flat: tube([[-R * .14, 0, 0], [0, -R * .01, .006], [R * .14, 0, 0]], R * .022, lineM),
      frown: tube(arcPts(R * .16, -R * .06), R * .022, lineM), smirk: tube([[-R * .14, -R * .01, 0], [0, -R * .02, .006], [R * .17, R * .06, 0]], R * .022, lineM),
    };
    for (const k2 in lines) { lines[k2].castShadow = false; mouth.add(lines[k2]); }
    const cav = new T.Mesh(new T.CircleGeometry(1, 28), new T.MeshStandardMaterial({ color: '#4a1416', roughness: .8 })); mouth.add(cav);
    const dsh = new T.Shape(); dsh.moveTo(-1, .35); dsh.lineTo(1, .35); dsh.absarc(0, .35, 1, 0, -Math.PI, true);
    const cavD = new T.Mesh(new T.ShapeGeometry(dsh, 20), cav.material); mouth.add(cavD);
    const tongue = new T.Mesh(new T.CircleGeometry(1, 20), new T.MeshStandardMaterial({ color: '#e0626a', roughness: .7 })); tongue.position.z = .002; mouth.add(tongue);
    const teeth = new T.Mesh(new T.PlaneGeometry(1, 1), new T.MeshStandardMaterial({ color: '#ffffff', roughness: .3 })); teeth.position.z = .003; mouth.add(teeth);
    // facial hair, specs, hair styles, accessories
    if (S.mooch) { const mc = mat(S.moochC || '#2a1a12', { roughness: .7 }); for (const s of [1, -1]) { const m = capsule(R * .07, R * .2, mc); onHead(m, R, -.25, s * .12, 1.0); m.rotateZ(s * (Math.PI / 2 - .35)); head.add(m); } }
    if (S.beard) { const b = mesh(new T.SphereGeometry(R * 1.012, 32, 16, 0, Math.PI * 2, Math.PI * .62, Math.PI * .3), new T.MeshStandardMaterial({ color: '#3a2618', transparent: true, opacity: .16, roughness: 1 }), false); b.rotation.x = -.5; head.add(b); }
    if (S.bindi) { const bi = new T.Mesh(new T.CircleGeometry(R * (S.bigBindi ? .07 : .045), 16), mat('#c8102e')); onHead(bi, R, .26, 0, 1.004); head.add(bi); }
    if (S.lips) lineM.color.set(S.lips);
    const specM = mat('#2a2a2a', { metalness: .4, roughness: .35 });
    if (S.specs || S.specsUp) {
      const sp = grp(); head.add(sp);
      for (const s of [1, -1]) { const r = mesh(new T.TorusGeometry(re * 1.35, R * .025, 8, 28), specM); onHead(r, R, .06, s * .36, 1.04); sp.add(r); }
      const br = mesh(new T.CylinderGeometry(R * .02, R * .02, R * .18, 8), specM); onHead(br, R, .1, 0, 1.06); br.rotateZ(Math.PI / 2); sp.add(br);
      for (const s of [1, -1]) { const a = mesh(new T.CylinderGeometry(R * .018, R * .018, R * .85, 6), specM); a.rotation.x = Math.PI / 2; a.position.set(s * R * .74, R * .08, R * .3); sp.add(a); }
      if (S.specsUp) { sp.rotation.x = -.55; sp.position.y = R * .05; }
    }
    const cap = (tilt = .45, thMax = 1.25, m = hairM, r = 1.08) => { const c = mesh(new T.SphereGeometry(R * r, 36, 20, 0, Math.PI * 2, 0, thMax), m); c.rotation.x = -tilt; head.add(c); return c; };
    const ball = (r, el, az, rr, m = hairM) => { const b = mesh(new T.SphereGeometry(R * r, 18, 14), m); onHead(b, R, el, az, rr); head.add(b); return b; };
    switch (S.hair) {
      case 'spiky': cap(.5, 1.3); for (let i = 0; i < 9; i++) { const c = mesh(new T.ConeGeometry(R * .16, R * .45, 10), hairM); onHead(c, R, .75 + (i % 3) * .18, -1.1 + i * .27, 1.0); c.rotateX(Math.PI / 2); head.add(c); } break;
      case 'neat': cap(.5, 1.32); ball(.32, .62, -.45, .82); break;
      case 'bun': case 'greybun': cap(.42, 1.35); ball(.36, .35, Math.PI, 1.05); break;
      case 'bald': { const f = mesh(new T.TorusGeometry(R * .93, R * .13, 10, 30, Math.PI * 1.3), hairM); f.rotation.x = -Math.PI / 2; const fg = grp(); fg.add(f); fg.rotation.y = -.468; fg.position.y = -R * .05; head.add(fg); break; }
      case 'whiteside': for (const s of [1, -1]) ball(.3, .18, s * 1.25, .9); ball(.25, .9, Math.PI, .8); break;
      case 'pigtails': cap(.45, 1.3); for (const s of [1, -1]) { ball(.34, .1, s * 1.45, 1.15); const rb = mesh(new T.TorusGeometry(R * .1, R * .045, 8, 16), mat('#ff3d7f')); onHead(rb, R, .2, s * 1.3, 1.05); head.add(rb); } break;
      case 'ponytail': { cap(.45, 1.35); const p = capsule(R * .18, R * .7, hairM); p.position.set(0, -R * .15, -R * 1.05); p.rotation.x = .3; head.add(p); break; }
      case 'cap': { cap(.15, 1.15, mat(S.capC || '#2F6BD8', { roughness: .7 }), 1.07); const br = mesh(new T.CylinderGeometry(R * .7, R * .7, R * .05, 28, 1, false, -Math.PI * .5, Math.PI), mat(S.capC || '#2F6BD8')); br.scale.z = .9; br.position.set(0, R * .5, R * .55); br.rotation.x = .12; head.add(br); break; }
      case 'messy': cap(.5, 1.3); for (let i = 0; i < 10; i++) { const r2 = rng(hash(id + i)); ball(.18 + r2() * .08, .7 + r2() * .55, -1.4 + r2() * 2.8, 1.0); } break;
      case 'curly': cap(.4, 1.35); for (let i = 0; i < 16; i++) ball(.16, .35 + (i % 4) * .28, -1.6 + (i * 0.42) % 3.2, 1.02); break;
      default: cap();
    }
    if (S.headphones) { const hm = mat('#1c1c22', { roughness: .4 }); const band = mesh(new T.TorusGeometry(.12 * k, .025, 8, 24), hm); band.rotation.x = Math.PI / 2; band.position.y = torso * 1.0 + .02; spine.add(band);
      for (const s of [1, -1]) { const cup = mesh(new T.CylinderGeometry(.06, .06, .05, 18), mat('#e8213a', { roughness: .4 })); cup.rotation.z = Math.PI / 2; cup.position.set(s * .13 * k, torso * .98, .04); spine.add(cup); } }
    // props held in a hand
    const props = {};
    if (S.phone) { const ph = mesh(new T.BoxGeometry(.07, .13, .012), mat('#222', { roughness: .3 })); ph.position.set(0, -limb * 2, limb * .9); arms[1].hand.add(ph); props.phone = ph; }
    if (S.stick) { const st = mesh(new T.CylinderGeometry(.018, .018, legL + torso * .3, 8), mat('#7a4a2a')); st.position.set(0, -(legL + torso * .3) / 2 + .05, 0); arms[1].hand.add(st); props.stick = st; }
    if (id === 'masterji') { const st = mesh(new T.CylinderGeometry(.012, .016, .9, 8), mat('#a0703a')); st.position.set(0, -limb * 1.2, .35); st.rotation.x = Math.PI / 2.2; arms[1].hand.add(st); props.stick = st; }
    root.traverse(o => { if (o.isMesh && o.castShadow === undefined) o.castShadow = true; });
    const height = legL + torso + .06 + R * 1.95;
    const mats = new Set(); root.traverse(o => { if (o.isMesh) [].concat(o.material).forEach(m => mats.add(m)); });
    return { id, S, root, body, hips, spine, neck, head, legs, arms, eyes, brows, mouth, lines, cav, cavD, tongue, teeth, R, re, legL, torso, height, props, skirt, mats: [...mats] };
  }

  /* ------------------------------------------------------------------ poses (degrees) */
  // arm: [forward swing, abduct out, elbow bend, elbow in]; L = character's left (screen right when facing camera)
  const P = {
    idle: { sp: [2, 0], hd: [0, 0, 0], L: [4, 9, 12, 0], R: [4, 9, 12, 0], face: ['n', 'smile'] },
    talk: { sp: [3, 0], hd: [0, 0, 0], L: [6, 10, 20, 0], R: [28, 16, 70, 8], face: ['n', 'smile'] },
    shock: { sp: [-7, 0], hd: [-8, 0, 0], L: [12, 128, 38, 0], R: [12, 128, 38, 0], face: ['wide', 'O', [1, 0]], knee: 10 },
    happy: { sp: [-5, 0], hd: [-10, 0, 0], L: [18, 148, 16, 0], R: [18, 148, 16, 0], face: ['happy', 'D', [.8, 0]] },
    laugh: { sp: [-12, 0], hd: [-18, 0, 7], L: [35, 14, 92, 38], R: [35, 14, 92, 38], face: ['closed', 'D', [.6, 0]] },
    angry: { sp: [4, 0], hd: [6, 0, 0], L: [-14, 44, 0, 105], R: [-14, 44, 0, 105], face: ['angry', 'frown', [-.4, 1]] },
    sad: { sp: [12, 0], hd: [20, 0, 4], L: [0, 3, 6, 0], R: [0, 3, 6, 0], face: ['sad', 'frown', [.5, -1]] },
    point: { sp: [3, 0], hd: [0, 0, 0], L: [4, 9, 12, 0], R: [82, 12, 4, 0], face: ['n', 'smile', [.3, 0]], finger: 'R' },
    hand: { sp: [-4, 0], hd: [-14, 0, 0], L: [4, 9, 12, 0], R: [168, 12, 6, 0], face: ['wide', 'open', [.7, 0]], finger: 'R' },
    think: { sp: [3, 0], hd: [-6, 0, 10], L: [28, -4, 100, 32], R: [62, -14, 148, 0], face: ['up', 'flat', [.5, .5]] },
    sly: { sp: [2, 0], hd: [4, 0, -9], L: [42, -8, 95, 22], R: [42, -8, 95, 22], face: ['sly', 'smirk', [.2, .6]] },
    dance: { sp: [0, 0], hd: [-6, 0, 0], L: [0, 140, 45, 0], R: [0, 60, 95, 0], face: ['happy', 'D', [.6, 0]], knee: 18 },
    facepalm: { sp: [8, 0], hd: [16, 0, 0], L: [4, 9, 12, 0], R: [88, -18, 158, 0], face: ['closed', 'frown', [-.2, 0]] },
    hold: { sp: [2, 0], hd: [6, 0, 0], L: [52, 12, 78, 0], R: [52, 12, 78, 0], face: ['n', 'flat'] },
    wave: { sp: [0, 0], hd: [-6, 0, 6], L: [4, 9, 12, 0], R: [8, 150, 42, 0], face: ['happy', 'open', [.6, 0]], wave: 1 },
  };
  const EYE = { n: [-1.05, 1.0, 0], wide: [-1.35, 1.25, 0], happy: [-.15, .35, 0], closed: [1.45, .9, 0], angry: [-.25, 1.0, 0], sad: [-.45, 1.0, 0], up: [-1.1, 1.0, .6], sly: [.05, .75, 0] }; // [upper lid, lower lid, look up]
  const poseVec = (p) => P[p] || P.idle;
  const mixArr = (a, b, q) => a.map((v, i) => lerp(v, b[i] === undefined ? v : b[i], q));

  /* ------------------------------------------------------------------ sets */
  let RENDERER, SCENE, CAM, SETS = {}, CH = {}, LIGHT = {}, LAYOUT = null, BOARD_TEX = {};
  function plane(w, h, m) { return mesh(new T.PlaneGeometry(w, h), m, false); }
  function box(w, h, d, m, x = 0, y = 0, z = 0, cast = true) { const b = mesh(new T.BoxGeometry(w, h, d), m, cast); b.position.set(x, y, z); return b; }
  function canvasTex(w, h, draw, rep) { const cv = document.createElement('canvas'); cv.width = w; cv.height = h; draw(cv.getContext('2d'), w, h); const t = new T.CanvasTexture(cv); t.colorSpace = T.SRGBColorSpace; if (rep) { t.wrapS = t.wrapT = T.RepeatWrapping; t.repeat.set(rep[0], rep[1]); } t.anisotropy = 4; return t; }
  const woodTex = () => canvasTex(256, 256, (g, w, h) => { g.fillStyle = '#b98a5c'; g.fillRect(0, 0, w, h); for (let i = 0; i < 8; i++) { g.fillStyle = i % 2 ? '#ad7f52' : '#c29466'; g.fillRect(0, i * 32, w, 30); g.fillStyle = 'rgba(90,55,25,.35)'; g.fillRect(0, i * 32 + 30, w, 2); g.fillRect((i * 97) % w, i * 32, 2, 32); } }, [16, 20]);
  const tileTex = (c1, c2) => canvasTex(128, 128, (g) => { g.fillStyle = c1; g.fillRect(0, 0, 128, 128); g.strokeStyle = c2; g.lineWidth = 3; for (let i = 0; i <= 4; i++) { g.beginPath(); g.moveTo(i * 32, 0); g.lineTo(i * 32, 128); g.stroke(); g.beginPath(); g.moveTo(0, i * 32); g.lineTo(128, i * 32); g.stroke(); } }, [10, 4]);

  function noiseTex(base, opts = {}) { // painted surface: base colour, soft noise, optional panel lines / grid
    return canvasTex(512, 512, (g, w, h) => { g.fillStyle = base; g.fillRect(0, 0, w, h); const r = rng(hash(base + JSON.stringify(opts)));
      for (let i = 0; i < 1400; i++) { g.fillStyle = `rgba(${r() < .5 ? '0,0,0' : '255,255,255'},${(r() * .05).toFixed(3)})`; const x = r() * w, y = r() * h, s2 = 2 + r() * 10; g.fillRect(x, y, s2, s2); }
      if (opts.panels) { g.strokeStyle = 'rgba(0,0,0,.18)'; g.lineWidth = 4; for (let x = 0; x <= w; x += w / opts.panels) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); }
        g.fillStyle = 'rgba(0,0,0,.25)'; for (let x = 0; x < w; x += w / opts.panels) for (const y of [24, h - 24]) { g.beginPath(); g.arc(x + 14, y, 4, 0, 7); g.fill(); g.beginPath(); g.arc(x + w / opts.panels - 14, y, 4, 0, 7); g.fill(); } }
      if (opts.grid) { g.strokeStyle = opts.gridC || 'rgba(0,0,0,.2)'; g.lineWidth = 3; for (let i = 0; i <= w; i += w / opts.grid) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, h); g.stroke(); g.beginPath(); g.moveTo(0, i); g.lineTo(w, i); g.stroke(); } }
      if (opts.ribs) { g.fillStyle = 'rgba(0,0,0,.12)'; for (let y = 0; y < h; y += 16) g.fillRect(0, y, w, 6); }
    }, opts.rep || [4, 2]); }
  function fan(x, y, z, m) { const f = grp(); f.position.set(x, y, z); f.add(box(.06, .3, .06, mat('#777'), 0, .15, 0)); const bl = grp(); f.add(bl); for (let i = 0; i < 3; i++) { const b = box(.9, .015, .16, m || mat('#8d6e52')); b.position.x = .45; const a = grp(); a.rotation.y = i * 2.094; a.add(b); bl.add(a); } bl.add(mesh(new T.CylinderGeometry(.09, .09, .08, 16), mat('#666'))); f.userData.spin = bl; return f; }
  function tree(h, c, m2) { const g = grp(); g.add(at(mesh(new T.CylinderGeometry(.08 * h, .12 * h, h * .5, 8), mat('#6b4a2e')), 0, h * .25, 0));
    for (let i = 0; i < 3; i++) { const s = mesh(new T.SphereGeometry(h * (.38 - i * .06), 14, 10), m2 || mat(c, { roughness: .9 })); s.position.set((i - 1) * h * .15, h * (.62 + i * .18), (i % 2) * h * .1); g.add(s); } return g; }
  function windowHole(wall, cx, cy, ww, wh, W2, H2, z, m) { // wall with a rectangular hole, as 4 boxes
    const left = cx - ww / 2, right = cx + ww / 2, top = cy + wh / 2, bot = cy - wh / 2;
    return [[(-W2 + left) / 2, H2 / 2, left + W2, H2], [(right + W2) / 2, H2 / 2, W2 - right, H2], [cx, (top + H2) / 2, ww, H2 - top], [cx, bot / 2, ww, bot]];
  }
  function wallWithWindows(wins, W2, H2, z, m, frameM) { // wins: [[cx,cy,w,h],...] sorted by x
    const g = grp(); let xs = -W2; const pieces = [];
    for (const [cx, cy, w, h] of wins) { const l = cx - w / 2; if (l > xs) pieces.push([(xs + l) / 2, H2 / 2, l - xs, H2]); pieces.push([cx, (cy + h / 2 + H2) / 2, w, H2 - (cy + h / 2)]); pieces.push([cx, (cy - h / 2) / 2, w, cy - h / 2]); xs = cx + w / 2;
      const fr = grp(); for (const [a, b, c, d] of [[cx, cy + h / 2, w + .12, .08], [cx, cy - h / 2, w + .12, .08], [cx - w / 2, cy, .08, h], [cx + w / 2, cy, .08, h]]) fr.add(box(c, d, .14, frameM, a, b, z + .04)); g.add(fr); }
    pieces.push([(xs + W2) / 2, H2 / 2, W2 - xs, H2]);
    for (const [x, y, w, h] of pieces) if (w > .001 && h > .001) g.add(box(w, h, .12, m, x, y, z, false));
    return g;
  }

  function buildSet(name, night) {
    const g = grp(), u = { anim: [] }; g.userData = u;
    const floor = (m, w = 30, d = 40) => { const f = mesh(new T.PlaneGeometry(w, d), m, false); f.rotation.x = -Math.PI / 2; f.position.z = d / 2 - 2; f.receiveShadow = true; g.add(f); return f; };
    u.bg = night ? '#0b1430' : '#9fd4ff';
    if (name === 'train') {
      floor(new T.MeshStandardMaterial({ map: noiseTex('#7d838c', { ribs: true, rep: [20, 26] }), roughness: .85 }));
      const wallM = new T.MeshStandardMaterial({ map: noiseTex('#7fb6a6', { panels: 3, rep: [6, 1] }), roughness: .8 }), frameM = mat('#9aa0a8', { metalness: .6, roughness: .35 });
      const wins = [[-2.1, 1.75, 1.5, 1.05], [0, 1.75, 1.5, 1.05], [2.1, 1.75, 1.5, 1.05]];
      g.add(wallWithWindows(wins, 8, 3.4, -1.55, wallM, frameM));
      g.add(box(16, .9, .14, mat('#5d8f80'), 0, .45, -1.5));
      for (const [cx] of wins) { // blinds rolled up + seat under each window
        g.add(box(1.5, .14, .1, mat('#3a3f52'), cx, 2.35, -1.45));
      }
      const seatM = new T.MeshStandardMaterial({ map: noiseTex('#2f6b9a', { grid: 8, gridC: 'rgba(0,0,0,.25)', rep: [16, 1] }), roughness: .55 });
      g.add(box(16, .14, .55, seatM, 0, .62, -1.2)); g.add(box(16, .6, .14, seatM, 0, .98, -1.45));
      for (let x = -7.5; x < 8; x += .75) { const c = capsule(.07, .5, mat('#2a5f8a', { roughness: .5 })); c.rotation.x = Math.PI / 2; c.position.set(x, .7, -1.17); g.add(c); }
      for (const [cx] of wins) { const gl = mesh(new T.PlaneGeometry(1.5, 1.05), new T.MeshStandardMaterial({ color: '#cfe6ff', transparent: true, opacity: .08, roughness: .05, metalness: .3 }), false); gl.position.set(cx, 1.75, -1.5); g.add(gl); }
      for (const x of [-3.2, 3.2]) { const pst = box(.7, .9, .02, mat(x < 0 ? '#ffd54a' : '#ff7aa8'), x, 1.75, -1.48); g.add(pst); g.add(box(.5, .08, .021, mat('#1E1620'), x, 2.0, -1.47)); g.add(box(.4, .05, .021, mat('#1E1620'), x, 1.6, -1.47)); }
      for (const x of [-3.5, -1.05, 1.05, 3.5]) g.add(box(.08, .6, .5, mat('#555'), x, .3, -1.2));

      g.add(box(16, .06, .5, mat('#8a8f98', { metalness: .5 }), 0, 2.75, -1.25)); // luggage rack
      for (const x of [-2.4, 2.4]) { const f = fan(x, 3.4, .2); g.add(f); u.anim.push(t => { f.userData.spin.rotation.y = t * 9; }); }
      for (const x of [-1.2, 1.2]) { const l = box(1.1, .05, .1, new T.MeshStandardMaterial({ color: '#fff8e0', emissive: '#fff4cc', emissiveIntensity: 1.4 }), x, 3.38, -.6, false); g.add(l); }
      const straps = []; for (let i = 0; i < 7; i++) { const s = grp(); s.position.set(-3 + i, 3.3, .6); s.add(box(.02, .4, .02, mat('#444'), 0, -.2, 0)); const r = mesh(new T.TorusGeometry(.07, .015, 8, 16), mat('#f2c335')); r.position.y = -.45; s.add(r); g.add(s); straps.push(s); }
      u.anim.push(t => straps.forEach((s, i) => { s.rotation.z = Math.sin(t * 2.2 + i) * .08; }));
      // outside: ground, trees and poles rushing past; the moon (or sun) far away stays put
      const out = grp(); g.add(out);
      const gm = mesh(new T.PlaneGeometry(200, 60), mat(night ? '#1c3324' : '#7fb35e', { roughness: 1 }), false); gm.rotation.x = -Math.PI / 2; gm.position.set(0, .2, -32); out.add(gm);
      const trees = []; const r = rng(.37);
      for (let i = 0; i < 26; i++) { const tr = tree(1.6 + r() * 1.4, night ? (i % 2 ? '#24452f' : '#1b3a26') : (i % 2 ? '#4f9a4a' : '#3e8a3c')); tr.userData = { x0: r() * 30 - 15, z: -3.2 - r() * 5 }; tr.position.set(0, .2, tr.userData.z); out.add(tr); trees.push(tr); }
      const poles = []; for (let i = 0; i < 4; i++) { const p = box(.08, 2.6, .08, mat('#555'), 0, 1.4, -2.4); p.userData.x0 = i * 7.5; out.add(p); poles.push(p); }
      u.anim.push(t => { trees.forEach(tr => { const d = -tr.userData.z; tr.position.x = ((tr.userData.x0 - t * 7 * (3.2 / d) * 1.4) % 30 + 45) % 30 - 15; });
        poles.forEach(p => { p.position.x = ((p.userData.x0 - t * 14) % 30 + 45) % 30 - 15; }); });
      if (night) {
        const moon = mesh(new T.SphereGeometry(5.5, 32, 24), new T.MeshBasicMaterial({ color: '#f6f1dc' }), false); moon.position.set(22, 14, -100); out.add(moon);
        const glow = mesh(new T.SphereGeometry(8, 24, 16), new T.MeshBasicMaterial({ color: '#f6f1dc', transparent: true, opacity: .14 }), false); glow.position.copy(moon.position); out.add(glow);
        const sg = new T.BufferGeometry(), pts = []; const rs = rng(.71); for (let i = 0; i < 400; i++) pts.push(rs() * 300 - 150, 8 + rs() * 80, -120 - rs() * 20);
        sg.setAttribute('position', new T.Float32BufferAttribute(pts, 3)); out.add(new T.Points(sg, new T.PointsMaterial({ color: '#ffffff', size: .7, sizeAttenuation: true })));
      } else { const sun = mesh(new T.SphereGeometry(5, 24, 16), new T.MeshBasicMaterial({ color: '#fff0a0' }), false); sun.position.set(30, 24, -100); out.add(sun); }
      u.rock = true; u.interior = true;
    } else if (name === 'classroom') {
      floor(new T.MeshStandardMaterial({ map: noiseTex('#c9b48e', { grid: 4, gridC: 'rgba(90,60,30,.18)', rep: [12, 16] }), roughness: .8 }));
      const wallM = new T.MeshStandardMaterial({ map: noiseTex('#f2e6c9', { rep: [3, 1] }), roughness: .9 });
      g.add(wallWithWindows([[3.0, 1.9, 1.3, 1.2]], 8, 3.6, -1.6, wallM, mat('#8a5c38')));
      g.add(box(3.2, 1.4, .06, mat('#8a5c38'), -.7, 2.05, -1.5));
      const bt = canvasTex(1024, 448, (c, w, h) => { c.fillStyle = '#2e5c47'; c.fillRect(0, 0, w, h); c.fillStyle = 'rgba(255,255,255,.08)'; c.fillRect(0, 0, w, h); c.fillStyle = '#f4f1e6'; c.font = '700 64px Kalam, Poppins'; c.textAlign = 'center'; c.fillText(name === 'classroom' ? (BOARD_TEX.text || '') : '', w / 2, h / 2 + 20); });
      u.board = plane(3.0, 1.28, new T.MeshStandardMaterial({ map: bt, roughness: .9 })); u.board.position.set(-.7, 2.05, -1.46); g.add(u.board); u.boardTex = bt;
      g.add(box(1.4, .08, .7, mat('#8a5c38'), 2.2, .8, -.9)); g.add(box(1.3, .75, .6, mat('#7a4c2a'), 2.2, .38, -.9));
      const globe = mesh(new T.SphereGeometry(.18, 24, 16), mat('#3b82f6', { roughness: .5 })); globe.position.set(2.0, 1.1, -.9); g.add(globe); u.anim.push(t => { globe.rotation.y = t * .8; });
      g.add(box(.04, .3, .04, mat('#444'), 2.0, .92, -.9));
      for (const x of [-3.4, 3.6]) { g.add(box(1.0, .06, .6, mat('#b5835a'), x, .75, .6)); g.add(box(.9, .7, .05, mat('#7a4c2a'), x, .38, .85)); }
      const clock = mesh(new T.CylinderGeometry(.22, .22, .05, 28), mat('#ffffff')); clock.rotation.x = Math.PI / 2; clock.position.set(1.4, 3.0, -1.5); g.add(clock);
      const hand = box(.02, .16, .01, mat('#222'), 0, .08, 0); const hp = grp(); hp.position.set(1.4, 3.0, -1.46); hp.add(hand); g.add(hp); u.anim.push(t => { hp.rotation.z = -t * 1.2; });
      const sky = plane(40, 20, new T.MeshBasicMaterial({ color: '#9fd4ff' })); sky.position.set(0, 3, -8); g.add(sky); g.add(at(tree(2.4, '#4f9a4a'), 3.6, 0, -4));
      u.interior = true;
    } else if (name === 'kitchen') {
      floor(new T.MeshStandardMaterial({ map: tileTex('#d8c7a8', '#bfae8e'), roughness: .8 }));
      g.add(wallWithWindows([[-2.6, 2.0, 1.2, 1.0]], 8, 3.6, -1.6, new T.MeshStandardMaterial({ map: tileTex('#eef3f5', '#c9d3d8'), roughness: .5 }), mat('#ffffff')));
      g.add(box(5.5, .9, .7, mat('#8a5c38'), .6, .45, -1.2)); g.add(box(5.6, .06, .76, mat('#d8d2c8', { roughness: .3 }), .6, .93, -1.2));
      const stove = box(.8, .06, .5, mat('#2a2a2a'), 0, .99, -1.2); g.add(stove);
      const cook = grp(); cook.position.set(0, 1.02, -1.2); g.add(cook);
      cook.add(at(mesh(new T.CylinderGeometry(.2, .2, .3, 24), mat('#c0c6cf', { metalness: .7, roughness: .3 })), 0, .15, 0));
      const wh = mesh(new T.CylinderGeometry(.03, .04, .1, 12), mat('#222')); wh.position.y = .36; cook.add(wh); u.anim.push(t => { wh.position.y = .36 + Math.max(0, Math.sin(t * 3)) * .03; });
      const steam = []; for (let i = 0; i < 4; i++) { const s = mesh(new T.SphereGeometry(.08, 10, 8), new T.MeshBasicMaterial({ color: '#fff', transparent: true, opacity: .5 }), false); cook.add(s); steam.push(s); }
      u.anim.push(t => steam.forEach((s, i) => { const q = (t * .6 + i / 4) % 1; s.position.set(Math.sin(t * 2 + i) * .05, .45 + q * .9, 0); s.scale.setScalar(.6 + q * 1.6); s.material.opacity = .45 * (1 - q); }));
      g.add(box(1.0, 2.3, .8, mat('#eef3f8', { roughness: .4 }), 3.3, 1.15, -1.1)); g.add(box(.05, .5, .05, mat('#8a8f98', { metalness: .6 }), 2.86, 1.5, -.68));
      g.add(box(2.4, .06, .35, mat('#8a5c38'), -.3, 2.4, -1.4)); [['#ffb020', -1.2], ['#d2413a', -.7], ['#7fbf6a', -.2], ['#ffd54a', .3]].forEach(([c, x]) => g.add(at(mesh(new T.CylinderGeometry(.11, .11, .26, 16), mat(c)), x, 2.56, -1.4)));
      const sky = plane(30, 20, new T.MeshBasicMaterial({ color: night ? '#1d2a5a' : '#bfe3ff' })); sky.position.set(-2, 3, -6); g.add(sky);
      u.interior = true;
    } else if (['park', 'market', 'tapri', 'terrace'].includes(name)) {
      floor(mat(name === 'park' ? '#7fbf5a' : name === 'terrace' ? '#d9c7a8' : '#b8b0a2', { roughness: 1 }), 80, 60);
      if (name !== 'park') { const road = mesh(new T.PlaneGeometry(80, 3), mat('#8f8a84', { roughness: .9 }), false); road.rotation.x = -Math.PI / 2; road.position.set(0, .005, -4); g.add(road); }
      const r = rng(hash(name)); const tr = [];
      for (let i = 0; i < 9; i++) { const t2 = tree(2.4 + r() * 1.5, i % 2 ? '#4f9a4a' : '#3e8a3c'); t2.position.set(-12 + i * 3 + r(), 0, -6 - r() * 6); g.add(t2); tr.push(t2); }
      u.anim.push(t => tr.forEach((x, i) => { x.rotation.z = Math.sin(t * 1.1 + i) * .02; }));
      const clouds = []; for (let i = 0; i < 5; i++) { const c = grp(); for (let j = 0; j < 3; j++) { const s = mesh(new T.SphereGeometry(1.2 - j * .25, 14, 10), new T.MeshBasicMaterial({ color: '#ffffff' }), false); s.position.set(j * 1.1, j % 2 * .3, 0); c.add(s); } c.position.set(-20 + i * 9, 10 + (i % 2) * 2, -30); g.add(c); clouds.push(c); }
      u.anim.push(t => clouds.forEach((c, i) => { c.position.x = ((-20 + i * 9 + t * .6) % 45 + 45) % 45 - 22; }));
      if (name === 'park') { // swing set and bench
        const sw = grp(); sw.position.set(-3.2, 0, -2.6); g.add(sw); const fm = mat('#d2413a', { metalness: .3, roughness: .5 });
        for (const x of [-.8, .8]) { const l = box(.08, 2.4, .08, fm, x, 1.2, 0); sw.add(l); } sw.add(box(1.8, .08, .08, fm, 0, 2.4, 0));
        const seat = grp(); seat.position.y = 2.4; sw.add(seat); seat.add(box(.02, 1.8, .02, mat('#555'), -.25, -.9, 0)); seat.add(box(.02, 1.8, .02, mat('#555'), .25, -.9, 0)); seat.add(box(.6, .05, .25, mat('#ffd54a'), 0, -1.8, 0));
        u.anim.push(t => { seat.rotation.x = Math.sin(t * 2.2) * .35; });
        g.add(box(1.6, .08, .45, mat('#8a5c38'), 3.0, .45, -2.2)); g.add(box(1.6, .5, .06, mat('#8a5c38'), 3.0, .75, -2.42));
      } else { // stall with awning (tapri/market/terrace)
        const st = grp(); st.position.set(2.4, 0, -2.4); g.add(st);
        st.add(box(2.2, 1.0, .9, mat('#8a5c38'), 0, .5, 0)); st.add(box(2.4, .08, 1.1, mat('#d2413a'), 0, 2.2, .1)); for (const x of [-1.1, 1.1]) st.add(box(.06, 2.2, .06, mat('#6b4a2e'), x, 1.1, .45));
        const k = mesh(new T.CylinderGeometry(.18, .18, .3, 20), mat('#c0c6cf', { metalness: .7, roughness: .3 })); k.position.set(-.5, 1.15, 0); st.add(k);
        for (let i = 0; i < 4; i++) st.add(at(mesh(new T.CylinderGeometry(.05, .045, .1, 12), mat('#fff8e6')), .2 + i * .16, 1.06, .1));
      }
      u.bg = night ? '#0b1430' : '#8fd0ff';
    } else { // livingroom (also bedroom)
      floor(new T.MeshStandardMaterial({ map: woodTex(), roughness: .6 }));
      const wallM = new T.MeshStandardMaterial({ map: noiseTex(name === 'bedroom' ? '#d8ccef' : '#f3dcb8', { rep: [3, 1] }), roughness: .95 });
      g.add(wallWithWindows([[2.4, 1.9, 1.3, 1.2]], 8, 3.6, -1.6, wallM, mat('#ffffff')));
      g.add(box(16, .14, .1, mat('#e8c99a'), 0, .07, -1.52));
      const sky = plane(30, 20, new T.MeshBasicMaterial({ color: night ? '#1d2a5a' : '#bfe3ff' })); sky.position.set(2, 3, -6); g.add(sky);
      if (night) { const m = mesh(new T.SphereGeometry(.4, 20, 14), new T.MeshBasicMaterial({ color: '#f3efe4' }), false); m.position.set(3.0, 3.6, -5.8); g.add(m); }
      for (const s of [-1, 1]) g.add(box(.35, 1.6, .06, mat('#d2413a', { roughness: .95 }), 2.4 + s * .85, 1.95, -1.48));
      const sofa = grp(); sofa.position.set(-1.9, 0, -1.05); g.add(sofa); const sm = mat('#5e7ce2', { roughness: .85 });
      sofa.add(box(2.4, .45, .9, sm, 0, .28, 0)); sofa.add(box(2.4, .7, .25, sm, 0, .7, -.35)); for (const x of [-1.25, 1.25]) sofa.add(box(.22, .6, .9, sm, x, .4, 0));
      for (const x of [-.55, .55]) { const c = capsule(.17, .7, mat('#ffd54a', { roughness: .9 })); c.rotation.z = Math.PI / 2; c.position.set(x, .62, .05); sofa.add(c); }
      const cat = grp(); cat.position.set(.6, .6, .1); sofa.add(cat); const cm = mat('#e0a050'); const cb = mesh(new T.SphereGeometry(.17, 18, 12), cm); cb.scale.set(1.4, .8, 1); cat.add(cb); const chd = mesh(new T.SphereGeometry(.1, 16, 12), cm); chd.position.set(.22, .04, .02); cat.add(chd);
      u.anim.push(t => { cb.scale.y = .8 + Math.sin(t * 2) * .03; });
      g.add(box(1.6, .5, .45, mat('#6b4a2e'), 2.6, .25, -1.25)); g.add(box(1.2, .7, .06, mat('#1c1c22', { roughness: .3 }), 2.6, .95, -1.3));
      const pot = mesh(new T.CylinderGeometry(.22, .17, .4, 18), mat('#b5563a')); pot.position.set(-3.6, .2, -1.1); g.add(pot); for (let i = 0; i < 5; i++) { const l = mesh(new T.SphereGeometry(.2, 12, 10), mat('#3e8a3c', { roughness: .9 })); l.scale.set(.6, 1.3, .6); l.position.set(-3.6 + Math.sin(i * 1.3) * .15, .7 + (i % 2) * .2, -1.1 + Math.cos(i * 1.3) * .12); l.rotation.z = Math.sin(i) * .5; g.add(l); }
      const rug = mesh(new T.CircleGeometry(1.8, 40), mat('#c0504d', { roughness: 1 }), false); rug.rotation.x = -Math.PI / 2; rug.position.set(0, .005, .4); rug.scale.y = .55; g.add(rug);
      const f = fan(0, 3.5, 0); g.add(f); u.anim.push(t => { f.userData.spin.rotation.y = t * 7; });
      const fr = box(.9, .7, .05, mat('#8a5c38'), -.6, 2.3, -1.5); g.add(fr); g.add(box(.8, .6, .02, mat('#ffd54a'), -.6, 2.3, -1.47));

      u.interior = true;
    }
    if (u.interior) { const wm = mat(name === 'train' ? '#7fb6a6' : name === 'kitchen' ? '#eef3f5' : name === 'classroom' ? '#f2e6c9' : name === 'bedroom' ? '#d8ccef' : '#f3dcb8', { roughness: .95 });
      for (const sx of [-8, 8]) g.add(box(.12, 3.6, 30, wm, sx, 1.8, 13, false));
      g.add(box(16.2, .1, 30, new T.MeshStandardMaterial({ color: name === 'train' ? '#d9dde3' : '#f7efe2', emissive: name === 'train' ? '#8a8f96' : '#8f887c', roughness: .9 }), 0, name === 'train' ? 3.45 : 3.65, 13, false)); }
    return g;
  }

  /* ------------------------------------------------------------------ stage layout (positions over time) */
  // consecutive shots in the same set form one continuous stage: characters keep their spot, newcomers
  // walk in from the nearer side, and the camera glides instead of cutting.
  const SPACING = 1.15;
  function buildLayout() {
    const segs = []; let cur = null;
    SB.scenes.forEach((s, i) => { const key = (s.set || 'classroom') + (s.night ? ':n' : '');
      if (!cur || cur.key !== key) { cur = { key, set: s.set || 'classroom', night: !!s.night, shots: [] }; segs.push(cur); } cur.shots.push(i); });
    const shotSeg = {};
    for (const sg of segs) {
      const first = SB.scenes[sg.shots[0]]; const order = first.cast.slice().sort((a, b) => a.x - b.x).map(c => c.id); const enterAt = {};
      const n = order.length, pos = {};
      order.forEach((id, i) => { const X = (i - (n - 1) / 2) * SPACING; pos[id] = { x: X, z: -.28 * Math.pow(X / 1.6, 2) + (i % 2 ? -.12 : 0) }; });
      for (const si of sg.shots.slice(1)) for (const c of SB.scenes[si].cast) if (!order.includes(c.id)) {
        const mates = SB.scenes[si].cast.filter(q => q.id !== c.id && pos[q.id]); const m = mates.sort((a2, b2) => Math.abs(a2.x - c.x) - Math.abs(b2.x - c.x))[0];
        const side = m ? Math.sign(c.x - m.x) || -1 : (c.x < 540 ? -1 : 1);
        pos[c.id] = m ? { x: pos[m.id].x + side * SPACING * .8, z: pos[m.id].z + .75 } : { x: side * (n / 2 + .5) * SPACING, z: 0 };
        order.push(c.id); enterAt[c.id] = si; }
      sg.order = order; sg.pos = pos; sg.enterAt = enterAt; sg.shots.forEach(si => shotSeg[si] = sg);
    }
    return { segs, shotSeg };
  }
  const WALK = 1.15;
  function charState(id, si, t) { // world position, presence and walking phase
    const sg = LAYOUT.shotSeg[si]; if (!sg.order.includes(id)) return null;
    const p = sg.pos[id], e = sg.enterAt[id];
    if (e !== undefined) { if (si < e) return null; const side = p.x < 0 ? -1 : 1, sx = side * 4.2;
      const ex = sg.shots.find(k => k > e && !SB.scenes[k].cast.some(c => c.id === id));   // newcomers leave when a later shot no longer has them
      if (ex !== undefined && si >= ex) { const q = (t - TL.scenes[ex].start) / WALK; if (q >= 1) return null;
        return { x: lerp(p.x, sx, eIO(q)), z: p.z, walking: true, dir: side, wq: Math.min(q * 1.25, .84) }; }
      const t0 = TL.scenes[e].start, q = (t - t0) / WALK;
      if (q < 1) return { x: lerp(sx, p.x, eIO(q)), z: p.z, walking: true, dir: -side, wq: q }; }
    return { x: p.x, z: p.z, walking: false };
  }

  /* ------------------------------------------------------------------ camera framing */
  const FOV = 34, CAMV = new T.Vector3();
  function bboxOf(ids, si, t, cut = 0) { let x0 = 1e9, x1 = -1e9, y1 = 0, y0 = 1e9, z = 0, n = 0;
    for (const id of ids) { const c = CH[id], st = charState(id, si, t); if (!c || !st) continue; x0 = Math.min(x0, st.x - .55); x1 = Math.max(x1, st.x + .55); y1 = Math.max(y1, c.height + .08); y0 = Math.min(y0, cut === 'close' ? c.legL + c.torso * .3 : cut ? c.legL * cut : -.02); z += st.z; n++; }
    return n ? { x0, x1, y0, y1, z: z / n } : null; }
  // camera that fits the box into the screen band [top,bottom] (px), seen from yaw (deg)
  function fitCam(bb, top, bottom, yaw) {
    const tn = Math.tan(FOV * D / 2), frH = (bottom - top) / H, frW = (W - 160) / W, asp = W / H;
    const h = bb.y1 - bb.y0, w = bb.x1 - bb.x0;
    const d = Math.max(h / (2 * tn * frH), w / (2 * tn * asp * frW)) + .3;
    const cx = (bb.x0 + bb.x1) / 2, cy = (bb.y0 + bb.y1) / 2, a = yaw * D;
    const camY = clamp(bb.y0 + h * .78, .7, 2.75);          // about eye level, always under the ceiling
    const f = ((top + bottom) / 2 - H / 2) / (H / 2);         // where the box centre should sit (+ = lower)
    const alpha = Math.atan(f * tn), beta = Math.atan2(cy - camY, d), pitch = beta + alpha;
    const pos = new T.Vector3(cx + Math.sin(a) * d, camY, bb.z + Math.cos(a) * d);
    const tgt = new T.Vector3(cx, camY + Math.tan(pitch) * d, bb.z);
    return { pos, tgt };
  }
  function bandFor(si, j) { const s = SB.scenes[si];
    let top = 600, bottom = 1470;                        // keep faces clear of the subtitles
    if (si === 0 && SB.hook && j === 0) top = (SB.hook_top != null ? +SB.hook_top : 300) + 300;
    if (exOn(si, j)) top = 720;
    if (s.card) top = 960;
    return [top, bottom]; }
  function exOn(si, j) { const s = SB.scenes[si]; let e = null; for (let k = 0; k <= j; k++) { const b = s.beats[k]; if (b.explain !== undefined) e = b.explain || null; } return !!(e && e.kind); }
  function framing(si, j, t) { // subjects for this beat, grown until nobody is half in frame
    const s = SB.scenes[si], B = s.beats[j] || {}, sg = LAYOUT.shotSeg[si];
    const present = sg.order.filter(id => charState(id, si, TL.scenes[si].start + 2) !== null);
    const inShot = s.cast.map(c => c.id).filter(id => present.includes(id));
    let subj;
    const wide = (B.cam && +B.cam.zoom <= 1.05 && !B.cam.on) || (!B.who && inShot.length > 1) || (B.fall || []).length || (si === 0 && j === 0 && SB.hook);
    if (B.cam && typeof B.cam.on === 'string') subj = [B.cam.on];
    else if (wide) subj = inShot.slice();
    else if (B.who && inShot.includes(B.who)) { // speaker + who they talk to (previous/next speaker)
      const other = [s.beats[j - 1], s.beats[j + 1], s.beats[j - 2]].map(b => b && b.who).find(w => w && w !== B.who && inShot.includes(w));
      subj = other && ((si + j) % 3 === 2) ? [B.who, other] : [B.who];
    } else subj = inShot.slice();
    let [top, bottom] = bandFor(si, j); const yaw = ((si * 7 + j * 5) % 3 - 1) * 9;
    let cut = wide ? 0 : subj.length === 1 ? 'close' : .55;
    if (!wide && exOn(si, j)) cut = .55;                     // board up: the speaker from the knees up, under the board
    if (cut === 'close') { top = s.card ? 990 : 430; bottom = s.card ? 1470 : 1440; }
    for (let it = 0; it < 6; it++) {
      const bb = bboxOf(subj, si, t, cut); if (!bb) break;
      const cam = fitCam(bb, top, bottom, yaw);
      const add = present.filter(id => !subj.includes(id) && partlyIn(id, si, t, cam));
      if (!add.length) return { cam, subj, top, bottom, yaw, wide: !!wide };
      subj = subj.concat(add); if (cut === 'close') return framingWith(subj, si, t, yaw, present, s.card ? [990, 1470] : [560, 1460]);
    }
    const bb = bboxOf(present, si, t) || { x0: -1, x1: 1, y0: 0, y1: 2, z: 0 };
    return { cam: fitCam(bb, top, bottom, yaw), subj: present, top, bottom, yaw };
  }
  function framingWith(subj, si, t, yaw, present, band) { const [top, bottom] = band;
    for (let it = 0; it < 6; it++) { const bb = bboxOf(subj, si, t, .55); const cam = fitCam(bb, top, bottom, yaw);
      const add = present.filter(id => !subj.includes(id) && partlyIn(id, si, t, cam)); if (!add.length) return { cam, subj, top, bottom, yaw }; subj = subj.concat(add); }
    const bb = bboxOf(present, si, t, 0); return { cam: fitCam(bb, top, bottom, yaw), subj: present, top, bottom, yaw }; }
  const _cam = new T.PerspectiveCamera(FOV, W / H, .05, 400);
  function partlyIn(id, si, t, cam) {
    const st = charState(id, si, t), c = CH[id]; if (!st || !c) return false;
    _cam.position.copy(cam.pos); _cam.lookAt(cam.tgt); _cam.updateMatrixWorld(); _cam.updateProjectionMatrix();
    let inside = 0, outside = 0;
    for (const dx of [-.42, 0, .42]) for (const y of [c.height * .55, c.height - .1]) { const v = new T.Vector3(st.x + dx, y, st.z).project(_cam); if (v.z >= 1 || Math.abs(v.y) > 1) continue; if (Math.abs(v.x) < .97) inside++; else outside++; }
    return inside > 0 && outside > 0;
  }
  const FR_CACHE = {};
  function framingCached(si, j) { const k = si + ':' + j; if (!FR_CACHE[k]) { const TB = TL.scenes[si].beats[j]; FR_CACHE[k] = framing(si, j, TB.start + .9); } return FR_CACHE[k]; }


  /* ------------------------------------------------------------------ 3D stickers and comic effects */
  const STICK = {}, FXO = {};
  function roundRect(w, h, r) { const sh = new T.Shape(), x = -w / 2, y = -h / 2;
    sh.moveTo(x + r, y); sh.lineTo(x + w - r, y); sh.quadraticCurveTo(x + w, y, x + w, y + r); sh.lineTo(x + w, y + h - r); sh.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    sh.lineTo(x + r, y + h); sh.quadraticCurveTo(x, y + h, x, y + h - r); sh.lineTo(x, y + r); sh.quadraticCurveTo(x, y, x + r, y); return sh; }
  function svgImg(markup, w, h) { return new Promise(res => { const im = new Image(); im.onload = () => res(im); im.onerror = () => res(null);
    im.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${markup}</svg>`); }); }
  async function makeSticker(icon, label) {
    const key = icon + '|' + (label || ''); if (STICK[key]) return STICK[key];
    const cv = document.createElement('canvas'); cv.width = cv.height = 512; const g = cv.getContext('2d');
    const grd = g.createLinearGradient(0, 0, 0, 512); grd.addColorStop(0, '#ffffff'); grd.addColorStop(1, '#fff1d6'); g.fillStyle = grd; g.fillRect(0, 0, 512, 512);
    const im = await svgImg(typeof iconSvg === 'function' ? iconSvg(icon, 50, 50, 100) : '', 100, 100);
    const sz = label ? 330 : 400; if (im) g.drawImage(im, (512 - sz) / 2, label ? 40 : 56, sz, sz);
    if (label) { g.fillStyle = '#1E1620'; g.font = "700 64px Poppins, 'Noto Sans Devanagari', sans-serif"; g.textAlign = 'center'; g.fillText(String(label).slice(0, 14), 256, 462, 470); }
    const tex = new T.CanvasTexture(cv); tex.colorSpace = T.SRGBColorSpace; tex.anisotropy = 4;
    const w = .62, geo = new T.ExtrudeGeometry(roundRect(w, w, .11), { depth: .035, bevelEnabled: true, bevelThickness: .018, bevelSize: .018, bevelSegments: 3, curveSegments: 10 });
    tex.repeat.set(1 / w, 1 / w); tex.offset.set(.5, .5);
    const m = new T.Mesh(geo, [new T.MeshStandardMaterial({ map: tex, roughness: .35 }), new T.MeshStandardMaterial({ color: '#ffd54a', roughness: .35 })]);
    m.castShadow = true; const grpS = grp(); grpS.add(m); m.position.z = -.03; grpS.visible = false; SCENE.add(grpS); STICK[key] = grpS; return grpS;
  }
  const gloss = (c, o = {}) => new T.MeshStandardMaterial(Object.assign({ color: c, roughness: .25, metalness: .05 }, o));
  function heartShape(s) { const h = new T.Shape(); h.moveTo(0, -s * .9); h.bezierCurveTo(-s * 1.2, -s * .1, -s * 1.1, s * .9, -s * .5, s * .9); h.bezierCurveTo(-s * .15, s * .9, 0, s * .6, 0, s * .45);
    h.bezierCurveTo(0, s * .6, s * .15, s * .9, s * .5, s * .9); h.bezierCurveTo(s * 1.1, s * .9, s * 1.2, -s * .1, 0, -s * .9); return h; }
  function starShape(r) { const sh = new T.Shape(); for (let i = 0; i < 10; i++) { const a = Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * .45 : r; const x = Math.cos(a) * rr, y = Math.sin(a) * rr; i ? sh.lineTo(x, y) : sh.moveTo(x, y); } return sh; }
  const ext = (sh, d) => new T.ExtrudeGeometry(sh, { depth: d, bevelEnabled: true, bevelThickness: d * .4, bevelSize: d * .4, bevelSegments: 3, curveSegments: 12 });
  function qMark(m) { const g = grp(); const c = new T.CatmullRomCurve3([[-.07, .1, 0], [-.05, .17, 0], [.03, .19, 0], [.08, .13, 0], [.05, .06, 0], [0, .02, 0], [0, -.04, 0]].map(p => new T.Vector3(...p)));
    g.add(mesh(new T.TubeGeometry(c, 24, .028, 10), m)); const d = mesh(new T.SphereGeometry(.034, 14, 10), m); d.position.y = -.12; g.add(d); return g; }
  function buildFx(kind, text) {
    const g = grp(), parts = [];
    if (kind === 'question') { const m = gloss('#ffc928'); for (let i = 0; i < 3; i++) { const q = qMark(m); q.scale.setScalar(.85 - i * .15); q.position.x = (i - 1) * .2; g.add(q); parts.push(q); } }
    else if (kind === 'exclaim') { const m = gloss('#e8213a'); const e = grp(); const c = capsule(.035, .17, m); c.position.y = .08; e.add(c); const d = mesh(new T.SphereGeometry(.04, 12, 10), m); d.position.y = -.1; e.add(d); g.add(e); parts.push(e); }
    else if (kind === 'hearts') { for (let i = 0; i < 4; i++) { const h = mesh(ext(heartShape(.08), .03), gloss('#ff3f7f', { transparent: true })); h.rotation.z = Math.PI; g.add(h); parts.push(h); } }
    else if (kind === 'stars') { for (let i = 0; i < 5; i++) { const st = mesh(ext(starShape(.09), .025), gloss('#ffd23a', { emissive: '#6b4a00' })); g.add(st); parts.push(st); } }
    else if (kind === 'sweat') { const m = gloss('#7cc8ff', { transparent: true, opacity: .85, roughness: .1 }); for (let i = 0; i < 2; i++) { const d = grp(); d.add(mesh(new T.SphereGeometry(.045, 14, 10), m)); const c = mesh(new T.ConeGeometry(.044, .09, 14), m); c.position.y = .055; d.add(c); g.add(d); parts.push(d); } }
    else if (kind === 'anger') { const m = gloss('#e8213a'); for (let i = 0; i < 4; i++) { const a = grp(); const c = new T.CatmullRomCurve3([[-.07, .0, 0], [-.02, .015, 0], [0, .07, 0]].map(p => new T.Vector3(...p))); a.add(mesh(new T.TubeGeometry(c, 12, .022, 8), m)); a.rotation.z = i * Math.PI / 2; g.add(a); } parts.push(g); }
    else if (kind === 'bulb') { const b = mesh(new T.SphereGeometry(.12, 20, 16), new T.MeshStandardMaterial({ color: '#fff2a0', emissive: '#ffd54a', emissiveIntensity: 1.6, roughness: .2 })); g.add(b);
      const base = mesh(new T.CylinderGeometry(.055, .055, .08, 16), gloss('#9aa0a8', { metalness: .7 })); base.position.y = -.13; g.add(base);
      const glow = mesh(new T.SphereGeometry(.24, 18, 14), new T.MeshBasicMaterial({ color: '#ffe680', transparent: true, opacity: .25 }), false); g.add(glow); parts.push(glow); }
    else if (kind === 'pop') { const cv = document.createElement('canvas'); cv.width = 512; cv.height = 256; const c = cv.getContext('2d'); c.fillStyle = '#ffd54a'; c.fillRect(0, 0, 512, 256);
      c.font = "800 92px Poppins, sans-serif"; c.textAlign = 'center'; c.lineWidth = 14; c.strokeStyle = '#1E1620'; c.strokeText(String(text || 'WAAH!').slice(0, 10), 256, 160, 480); c.fillStyle = '#e8213a'; c.fillText(String(text || 'WAAH!').slice(0, 10), 256, 160, 480);
      const tex = new T.CanvasTexture(cv); tex.colorSpace = T.SRGBColorSpace; tex.repeat.set(1 / 1.2, 1 / .6); tex.offset.set(.5, .5);
      const m = new T.Mesh(new T.ExtrudeGeometry(roundRect(1.2, .6, .14), { depth: .04, bevelEnabled: true, bevelThickness: .02, bevelSize: .02, bevelSegments: 2 }), [new T.MeshStandardMaterial({ map: tex, roughness: .4 }), gloss('#e8213a')]); g.add(m); parts.push(m); }
    g.visible = false; SCENE.add(g); return { g, parts, kind };
  }
  function fxAnchor(f, B, si, t) { const id = f.on || B.who; const c = CH[id], st = id && charState(id, si, t);
    if (c && st) return new T.Vector3(st.x, c.height + .12, st.z); return CAM.position.clone().add(new T.Vector3(0, 0, -3).applyQuaternion(CAM.quaternion)); }
  // a point at the depth of `w`, moved on screen to ndc (clamped so it stays inside the frame)
  function inView(w, nx, ny, lim = [.66, .6, -.35]) { const v = w.clone().project(CAM); v.x = clamp(nx, -lim[0], lim[0]); v.y = clamp(ny, lim[2], lim[1]); return v.unproject(CAM); }
  function animFx(o, f, B, si, t, bt, dur) {
    const a = fxAnchor(f, B, si, t), p = clamp(bt / .25), out = clamp((dur - bt) / .25 + .0001), sc = eOut(p) * (.3 + .7 * out);
    const g = o.g, hv = a.clone().project(CAM), d = CAM.position.distanceTo(a), k = .75 + .035 * d;
    const right = new T.Vector3(1, 0, 0).applyQuaternion(CAM.quaternion), up = new T.Vector3(0, 1, 0).applyQuaternion(CAM.quaternion);
    let ox = 0, oy = .08;
    if (o.kind === 'exclaim') { ox = .32; oy = .3; } else if (o.kind === 'sweat') { ox = .26; oy = -.2; } else if (o.kind === 'anger') { ox = .3; oy = .05; } else if (o.kind === 'bulb') oy = .26;
    const base = inView(a, hv.x, hv.y); g.position.copy(base).add(right.multiplyScalar(ox * k)).add(up.multiplyScalar(oy * k));
    const pv = g.position.clone().project(CAM); g.position.copy(inView(g.position, pv.x, pv.y, [.72, .48, -.4]));
    g.visible = sc > .02; g.quaternion.copy(CAM.quaternion); g.scale.setScalar(Math.max(.001, sc * k));
    if (o.kind === 'question') o.parts.forEach((q, i) => { q.position.y = Math.abs(Math.sin(t * 3 + i)) * .08; q.rotation.y = Math.sin(t * 2 + i) * .5; });
    if (o.kind === 'exclaim') o.parts[0].rotation.z = Math.sin(t * 10) * .12;
    if (o.kind === 'hearts') o.parts.forEach((h, i) => { const q = (t * .7 + i / 4) % 1; h.position.set((i - 1.5) * .18 + Math.sin(t * 2 + i) * .04, q * .5, 0); h.material.opacity = 1 - q; h.rotation.y = t * 2 + i; });
    if (o.kind === 'stars') { g.quaternion.identity(); o.parts.forEach((st, i) => { const an = t * 3 + i * 1.2566; st.position.set(Math.cos(an) * .32, -.05 + Math.sin(an * 2) * .03, Math.sin(an) * .32); st.rotation.set(0, an * 2, 0); }); }
    if (o.kind === 'sweat') o.parts.forEach((dd, i) => { const q = (t * 1.3 + i * .5) % 1; dd.position.set(i * .09, -q * .25, 0); dd.scale.setScalar(1 - q * .5); });
    if (o.kind === 'anger') o.parts[0].scale.setScalar(1 + .12 * Math.sin(t * 16));
    if (o.kind === 'bulb') o.parts[0].scale.setScalar(1 + .15 * Math.sin(t * 6));
    if (o.kind === 'pop') g.rotateZ(-.12 + Math.sin(t * 20) * .02);
  }
  // speed streaks rushing past the camera (the "lines" fx)
  let STREAK = null;
  function streaks(on, t, bt) {
    if (!STREAK) { STREAK = grp(); const m = new T.MeshBasicMaterial({ color: '#ffffff', transparent: true, opacity: .7 }); const r = rng(.5);
      for (let i = 0; i < 46; i++) { const s = new T.Mesh(new T.BoxGeometry(.012, .012, 1.6 + r() * 2.4), m); const a = r() * Math.PI * 2, rad = .9 + r() * 2.2; s.userData = { a, rad, z0: r() * 14 }; STREAK.add(s); } SCENE.add(STREAK); }
    STREAK.visible = on; if (!on) return; STREAK.position.copy(CAM.position); STREAK.quaternion.copy(CAM.quaternion);
    STREAK.children.forEach(s => { const u = s.userData; s.position.set(Math.cos(u.a) * u.rad * 1.0, Math.sin(u.a) * u.rad * 1.6, -((u.z0 - t * 22) % 14 + 14) % 14 - 1.5); });
    STREAK.children[0].material.opacity = .65 * clamp(1 - bt / 2.2);
  }
  // dust motes floating in the light (interiors)
  let DUST = null;
  function dust(on, t) {
    if (!DUST) { const g = new T.BufferGeometry(), r = rng(.9), pts = []; for (let i = 0; i < 260; i++) pts.push(r() * 9 - 4.5, .3 + r() * 3, r() * 8 - 2.5);
      g.setAttribute('position', new T.Float32BufferAttribute(pts, 3)); DUST = new T.Points(g, new T.PointsMaterial({ color: '#fff4d8', size: .025, transparent: true, opacity: .55, depthWrite: false })); DUST.userData.base = pts.slice(); SCENE.add(DUST); }
    DUST.visible = on; if (!on) return; const a = DUST.geometry.attributes.position, b = DUST.userData.base;
    for (let i = 0; i < a.count; i++) { a.setXYZ(i, b[i * 3] + Math.sin(t * .3 + i) * .15, b[i * 3 + 1] + ((t * .05 + i * .013) % 1) * .4 - .2, b[i * 3 + 2] + Math.cos(t * .25 + i * 1.3) * .15); } a.needsUpdate = true;
  }


  /* ------------------------------------------------------------------ depth of field (blurred set behind sharp cast) */
  let RT1, RT2, QSCENE, QCAM, QUAD, BLUR, COPY;
  function dofSetup() {
    const o = { minFilter: T.LinearFilter, magFilter: T.LinearFilter, type: T.HalfFloatType };
    RT1 = new T.WebGLRenderTarget(540, 960, o); RT2 = new T.WebGLRenderTarget(540, 960, o);
    QSCENE = new T.Scene(); QCAM = new T.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    BLUR = new T.ShaderMaterial({ uniforms: { tDiffuse: { value: null }, dir: { value: new T.Vector2() } }, depthTest: false, depthWrite: false,
      vertexShader: 'varying vec2 vUv; void main(){ vUv=uv; gl_Position=vec4(position.xy,0.,1.); }',
      fragmentShader: 'uniform sampler2D tDiffuse; uniform vec2 dir; varying vec2 vUv; void main(){ float w[5]; w[0]=.227027; w[1]=.1945946; w[2]=.1216216; w[3]=.054054; w[4]=.016216; vec4 c=texture2D(tDiffuse,vUv)*w[0]; for(int i=1;i<5;i++){ c+=texture2D(tDiffuse,vUv+dir*float(i))*w[i]; c+=texture2D(tDiffuse,vUv-dir*float(i))*w[i]; } gl_FragColor=c; }' });
    COPY = new T.MeshBasicMaterial({ map: RT1.texture, depthTest: false, depthWrite: false });
    QUAD = new T.Mesh(new T.PlaneGeometry(2, 2), BLUR); QUAD.frustumCulled = false; QSCENE.add(QUAD);
  }
  function renderDof(strength, setG, extras) {
    if (strength < .05) { RENDERER.setRenderTarget(null); RENDERER.render(SCENE, CAM); return; }
    if (!RT1) dofSetup();
    const chars = Object.values(CH).filter(c => c.root.visible);
    chars.forEach(c => c.mats.forEach(m => { m.colorWrite = false; m.depthWrite = false; }));
    extras.forEach(o => { o.userData._v = o.visible; o.visible = false; });
    RENDERER.setRenderTarget(RT1); RENDERER.render(SCENE, CAM);
    chars.forEach(c => c.mats.forEach(m => { m.colorWrite = true; m.depthWrite = true; }));
    QUAD.material = BLUR;
    for (let it = 0; it < 2; it++) for (const [src, dst, dx, dy] of [[RT1, RT2, 1, 0], [RT2, RT1, 0, 1]]) {
      BLUR.uniforms.tDiffuse.value = src.texture; BLUR.uniforms.dir.value.set(dx * strength * (it ? 1.6 : 1) / 540, dy * strength * (it ? 1.6 : 1) / 960);
      RENDERER.setRenderTarget(dst); RENDERER.render(QSCENE, QCAM); }
    RENDERER.setRenderTarget(null); QUAD.material = COPY; RENDERER.autoClear = true; RENDERER.render(QSCENE, QCAM);
    extras.forEach(o => { o.visible = o.userData._v; });
    const bg = SCENE.background; SCENE.background = null; setG.visible = false; const dv = DUST && DUST.visible; if (DUST) DUST.visible = false;
    RENDERER.autoClear = false; RENDERER.clearDepth(); RENDERER.render(SCENE, CAM); RENDERER.autoClear = true;
    SCENE.background = bg; setG.visible = true; if (DUST) DUST.visible = dv;
  }

  /* ------------------------------------------------------------------ init */
  function init() {
    const cv = document.getElementById('c3d');
    RENDERER = new T.WebGLRenderer({ canvas: cv, antialias: true, preserveDrawingBuffer: true });
    RENDERER.setPixelRatio(1); RENDERER.setSize(W, H, false);
    RENDERER.outputColorSpace = T.SRGBColorSpace; RENDERER.toneMapping = T.ACESFilmicToneMapping; RENDERER.toneMappingExposure = 1.08;
    RENDERER.shadowMap.enabled = true; RENDERER.shadowMap.type = T.PCFSoftShadowMap;
    SCENE = new T.Scene(); CAM = new T.PerspectiveCamera(FOV, W / H, .05, 400);
    const hemi = new T.HemisphereLight('#fff4e2', '#6a5848', 1.25); SCENE.add(hemi);
    const key = new T.DirectionalLight('#fff0d8', 2.4); key.position.set(-3, 6, 6); key.castShadow = true; key.shadow.mapSize.set(1024, 1024);
    Object.assign(key.shadow.camera, { left: -6, right: 6, top: 6, bottom: -2, near: .5, far: 30 }); key.shadow.bias = -.0005; key.shadow.normalBias = .02; SCENE.add(key);
    const fill = new T.DirectionalLight('#cfe0ff', .7); fill.position.set(5, 3, 4); SCENE.add(fill);
    const rim = new T.DirectionalLight('#ffe6c0', 1.6); rim.position.set(1, 4, -6); SCENE.add(rim);
    const warm = new T.PointLight('#ffcf8a', 6, 9, 1.6); warm.position.set(0, 3.0, 1.5); SCENE.add(warm);
    LIGHT = { hemi, key, fill, rim };
    LAYOUT = buildLayout();
    for (const sg of LAYOUT.segs) { const k = sg.key; if (!SETS[k]) { SETS[k] = buildSet(sg.set, sg.night); SETS[k].visible = false; SCENE.add(SETS[k]); } }
    const ids = new Set(); SB.scenes.forEach(s => s.cast.forEach(c => ids.add(c.id)));
    for (const id of ids) { CH[id] = buildChar(id); CH[id].root.visible = false; SCENE.add(CH[id].root); }
    document.body.classList.add('d3');
    const jobs = []; SB.scenes.forEach(sc => sc.beats.forEach(b => [].concat(b.show || []).forEach(sh => { const o = typeof sh === 'string' ? { icon: sh } : sh; if (o.icon) jobs.push(makeSticker(o.icon, o.label)); })));
    return Promise.all(jobs);
  }
  function setBoard(text) { // classroom board text
    for (const k in SETS) { const u = SETS[k].userData; if (!u.boardTex) continue; const cv = u.boardTex.image, c = cv.getContext('2d');
      if (u.boardText === text) continue; u.boardText = text; c.fillStyle = '#2e5c47'; c.fillRect(0, 0, cv.width, cv.height); c.fillStyle = '#f4f1e6'; c.font = '700 70px Kalam, Poppins'; c.textAlign = 'center';
      String(text || '').split('\n').forEach((ln, i, a) => c.fillText(ln, cv.width / 2, cv.height / 2 + 24 + (i - (a.length - 1) / 2) * 84)); u.boardTex.needsUpdate = true; }
  }

  /* ------------------------------------------------------------------ per-frame */
  const sceneAt = t => { let i = 0; TL.scenes.forEach((s, k) => { if (t >= s.start) i = k; }); return i; };
  const beatAt = (si, t) => { const bs = TL.scenes[si].beats; let j = 0; bs.forEach((b, k) => { if (t >= b.start) j = k; }); return j; };
  const envAt = t => { if (!TL.env) return .4; const i = Math.floor(t * TL.envFps); return TL.env[Math.min(TL.env.length - 1, Math.max(0, i))] || 0; };
  const VIS = { X: [26, 0, 0, 0], M: [22, 0, 0, 0], A: [33, 1, .15, .5], E: [37, .55, 0, 1], O: [23, .9, 1, .15], U: [17, .55, 1, 0], S: [31, .25, 0, 1] };
  function visAt(t) { if (!TL.visS) return null; const F = TL.visFps || 30, f = t * F, k = Math.floor(f), fr = f - k, n = TL.visS.length;
    const get = i => { i = Math.max(0, Math.min(n - 1, i)); const s = VIS[TL.visS[i]] || VIS.X, o = (TL.visO[i] || 0) / 9, on = o > 0 ? 1 : 0; return [s[0], s[1] * o, s[2] * on, s[3] * on]; };
    const a = get(k), b = get(k + 1), c = get(k - 1), m = [0, 1, 2, 3].map(q => .78 * (a[q] * (1 - fr) + b[q] * fr) + .22 * c[q]); return { w: m[0], h: m[1], r: m[2], teeth: m[3] }; }
  function poseOf(si, j, id) { const s = SB.scenes[si]; let p = (s.cast.find(c => c.id === id) || {}).pose || 'idle'; for (let k = 0; k <= j; k++) { const a = (s.beats[k].act || {})[id]; if (a) p = a; } return p; }
  const yawTo = (a, b) => Math.atan2(b.x - a.x, b.z - a.z) / D; // degrees, 0 = facing camera (+z)
  const angDiff = (a, b) => { let d = (b - a) % 360; if (d > 180) d -= 360; if (d < -180) d += 360; return d; };

  function facing(id, si, j, t) { // desired body yaw (deg) for a beat
    const s = SB.scenes[si], B = s.beats[j]; if (!B) return 0;
    if (B.turn && B.turn[id] !== undefined) return +B.turn[id];
    for (let k = j - 1; k >= 0; k--) { if (B.who === id) break; const b = s.beats[k]; if (b.turn && b.turn[id] !== undefined) return +b.turn[id]; if (b.who === id) break; }
    if (SB.autoturn === false) return 0;
    const me = charState(id, si, t); if (!me) return 0;
    const sp = B.who && B.who !== id ? charState(B.who, si, t) : null;
    if (sp) return clamp(yawTo(me, sp), -70, 70) * .75;         // listeners turn to the speaker (cheated toward camera)
    if (B.who === id) { // speaker half-turns to whoever they talk to
      const other = [s.beats[j - 1], s.beats[j + 1]].map(b => b && b.who).find(w => w && w !== id);
      const o = other && charState(other, si, t); if (o) return clamp(yawTo(me, o), -60, 60) * .45; }
    return 0;
  }

  function pose(c, si, j, t, bt, TB, B) {
    const id = c.id, pb = poseOf(si, j, id), pa = j > 0 ? poseOf(si, j - 1, id) : pb, q = pa === pb ? 1 : eIO(bt / .38);
    const A = poseVec(pa), Bp = poseVec(pb);
    const talking = B.who === id && t < TB.audioEnd, env = talking ? envAt(t) : 0, seed = hash(id) * 10;
    const sp = mixArr(A.sp, Bp.sp, q), hd = mixArr(A.hd, Bp.hd, q), L = mixArr(A.L, Bp.L, q), Rr = mixArr(A.R, Bp.R, q);
    const knee = lerp(A.knee || 0, Bp.knee || 0, q);
    // life: breathing, sway, talk gestures, listening nods
    const br = Math.sin(t * 2.1 + seed) * .5 + .5;
    sp[0] += Math.sin(t * .9 + seed) * 1.2; sp[1] += Math.sin(t * .7 + seed * 2) * 1.6;
    hd[0] += Math.sin(t * 1.3 + seed) * 2; hd[1] += Math.sin(t * .8 + seed) * 4; hd[2] += Math.sin(t * .6 + seed * 3) * 2;
    if (talking) { const g = Math.sin(t * 7.5 + seed) * env, g2 = Math.sin(t * 4.3 + seed * 2) * env;
      hd[0] += -6 * env + g * 5; hd[2] += g2 * 4;
      if (pb === 'talk' || pb === 'idle') { Rr[0] += 20 * env + g * 14; Rr[2] += 25 * env + g2 * 18; L[0] += g2 * 8; L[2] += 10 * env; }
      else { Rr[0] += g * 5; L[0] += g2 * 4; } }
    else if (B.who && B.who !== id) hd[0] += Math.max(0, Math.sin(t * 2.4 + seed)) * 3;
    if (pb === 'laugh') { sp[0] += Math.sin(t * 16) * 2.5; hd[0] += Math.sin(t * 16) * 3; }
    if (pb === 'wave' || Bp.wave) { Rr[3] = Math.sin(t * 9) * 35; }
    if (pb === 'dance') { sp[1] += Math.sin(t * 6) * 8; L[1] += Math.sin(t * 6) * 25; Rr[1] -= Math.sin(t * 6) * 25; }
    if (pb === 'angry' && (B.tremble || []).includes(id)) hd[1] += Math.sin(t * 40) * 3;
    // apply
    c.spine.rotation.set(sp[0] * D, 0, sp[1] * D); c.spine.scale.set(1 + br * .012, 1 + br * .01, 1 + br * .02);
    c.neck.rotation.set(hd[0] * .3 * D, hd[1] * .3 * D, hd[2] * .3 * D); c.head.rotation.set(hd[0] * .7 * D, hd[1] * .7 * D, hd[2] * .7 * D);
    for (const a of c.arms) { const v = a.s > 0 ? L : Rr; a.sh.rotation.x = -v[0] * D; a.sh.rotation.z = a.s * v[1] * D; a.el.rotation.x = -v[2] * D; a.el.rotation.z = -a.s * v[3] * D; }
    const fing = (Bp.finger && q > .5) ? Bp.finger : (A.finger && q <= .5 ? A.finger : null);
    c.arms.forEach(a => { a.finger.visible = fing === (a.s > 0 ? 'L' : 'R'); });
    for (const l of c.legs) { l.th.rotation.set(-knee * .5 * D, 0, l.s * 2 * D); l.kn.rotation.set(knee * D, 0, 0); }
    c.hips.position.y = c.legL * (1 - (1 - Math.cos(knee * D)) * .5);
    // face
    const fa = A.face, fb = Bp.face, eyeK = q < .5 ? fa[0] : fb[0], ek = EYE[eyeK] || EYE.n;
    const browA = fa[2] || [0, 0], browB = fb[2] || [0, 0], brw = mixArr(browA, browB, q);
    const blinkT = (t + seed * 7) % (2.6 + (seed % 1.3)), blink = blinkT < .13 ? Math.sin(blinkT / .13 * Math.PI) : 0;
    let upA = lerp(ek[0], 1.45, blink), loA = ek[1];
    for (const e of c.eyes) { e.up.rotation.x = upA; e.lo.rotation.x = loA; }
    // gaze: toward the speaker, else camera with small saccades
    let gx = Math.sin(t * .7 + seed) * .25, gy = ek[2] ? .45 : Math.sin(t * .5 + seed) * .12;
    if (B.who && B.who !== id) { const me = charState(id, si, t), o = charState(B.who, si, t); if (me && o) gx = clamp((yawTo(me, o) - (c.root.rotation.y / D + hd[1] * .7)) / 50, -1, 1) * .55; }
    for (const e of c.eyes) e.ir.position.set(gx * c.re * .42, gy * c.re * .35, c.re * .63);
    c.brows.forEach(b => { b.b.position.y = 0; b.c.position.y = brw[0] * c.R * .07; b.c.rotation.y = 0; b.c.rotation.z = Math.PI / 2 + b.s * brw[1] * .32; });
    // mouth: visemes while talking, the pose's shape otherwise
    const vm = talking ? visAt(t) : null, shape = q < .5 ? fa[1] : fb[1], R = c.R;
    for (const k in c.lines) c.lines[k].visible = false; c.cav.visible = c.cavD.visible = c.tongue.visible = c.teeth.visible = false;
    let open = 0, wid = 1, round = 0, teethA = 0, dshape = false;
    if (vm) { open = vm.h; wid = vm.w / 28; round = vm.r; teethA = vm.teeth; dshape = shape === 'D' || shape === 'open'; }
    else if (shape === 'O') { open = .85; wid = .7; round = 1; }
    else if (shape === 'D') { open = .75; wid = 1.25; dshape = true; teethA = 1; }
    else if (shape === 'open') { open = .55; wid = 1.0; dshape = true; teethA = .6; }
    if (open < .08) { (c.lines[shape] || c.lines.smile).visible = true; if (!c.lines[shape] && shape === 'O') c.lines.flat.visible = true; }
    else {
      const w = R * .24 * wid * (1 - .3 * round), h = R * (.06 + .24 * open) * (1 + .3 * round);
      const cv = dshape ? c.cavD : c.cav; cv.visible = true; cv.scale.set(w, dshape ? h * .9 : h, 1); cv.position.y = dshape ? -h * .3 : 0;
      c.tongue.visible = open > .25; c.tongue.scale.set(w * .55, h * .35, 1); c.tongue.position.set(0, -h * .55, .002);
      c.teeth.visible = teethA > .3; c.teeth.scale.set(w * 1.3, h * .28, 1); c.teeth.position.set(0, (dshape ? 0 : h * .62) + (dshape ? h * .05 : 0), .003);
    }
  }

  let lastSet = null;
  function render(t) {
    const si = sceneAt(t), s = SB.scenes[si], T0 = TL.scenes[si], j = beatAt(si, t), B = s.beats[j], TB = T0.beats[j], bt = t - TB.start;
    const sg = LAYOUT.shotSeg[si], setG = SETS[sg.key];
    for (const k in SETS) SETS[k].visible = SETS[k] === setG;
    SCENE.background = new T.Color(setG.userData.bg); SCENE.fog = null;
    if (s.set === 'classroom') setBoard(s.board || '');
    setG.userData.anim.forEach(f => f(t));
    if (setG.userData.rock) { setG.rotation.z = Math.sin(t * 1.7) * .0035; setG.position.y = Math.sin(t * 7.3) * .004; }
    const night = sg.night; LIGHT.hemi.intensity = night ? .95 : 1.25; LIGHT.key.intensity = night ? 2.0 : 2.4;
    // characters
    for (const id in CH) {
      const c = CH[id], st = charState(id, si, t); c.root.visible = !!st; if (!st) continue;
      // facing: eased from the previous beat's facing; walking faces the walk direction
      let yaw = facing(id, si, j, t); const yPrev = j > 0 ? facing(id, si, j - 1, t) : yaw;
      yaw = yPrev + angDiff(yPrev, yaw) * eIO(bt / .45);
      if ((B.spin || []).includes(id)) yaw += 360 * eIO(bt / .8);
      let wq = 0;
      if (st.walking) { yaw = lerp(st.dir * 90, yaw, clamp((st.wq - .8) / .2)); wq = st.wq; }
      c.root.position.set(st.x, 0, st.z); c.root.rotation.y = yaw * D;
      pose(c, si, j, t, bt, TB, B);
      // walk cycle
      if (st.walking && wq < 1) { const ph = t * 9, a = (1 - clamp((wq - .85) / .15)) ;
        c.legs.forEach(l => { const sw = Math.sin(ph + (l.s > 0 ? 0 : Math.PI)) * 28 * a; l.th.rotation.x = -sw * D; l.kn.rotation.x = Math.max(0, -Math.sin(ph + (l.s > 0 ? 0 : Math.PI) + .9)) * 40 * a * D; });
        c.arms.forEach(ar => { ar.sh.rotation.x += Math.sin(ph + (ar.s > 0 ? Math.PI : 0)) * 22 * a * D; });
        c.body.position.y = Math.abs(Math.sin(ph)) * .03 * a; } else c.body.position.y = 0;
      // hop (squash & stretch), tremble, fall
      c.body.scale.set(1, 1, 1); c.body.rotation.set(0, 0, 0); c.body.position.x = 0;
      if ((B.hop || []).includes(id)) { const hp = bt / .5; if (hp < 1) { const k2 = Math.sin(hp * Math.PI); c.body.position.y += k2 * .28; c.body.scale.set(1 - .06 * k2, 1 + .09 * k2, 1 - .06 * k2); }
        else if (hp < 1.35) { const k2 = Math.sin((hp - 1) / .35 * Math.PI); c.body.scale.set(1 + .08 * k2, 1 - .1 * k2, 1 + .08 * k2); } }
      if ((B.tremble || []).includes(id)) c.body.position.x = Math.sin(t * 70) * .015;
      const fell = j > 0 && (s.beats[j - 1].fall || []).includes(id);
      if ((B.fall || []).includes(id)) { const k2 = clamp(bt / .5); c.body.rotation.x = -1.45 * (k2 < 1 ? 1 - Math.pow(1 - k2, 3) * Math.abs(Math.cos(k2 * 9)) : 1); }
      else if (fell) c.body.rotation.x = -1.45 * (1 - eIO(bt / .45));
    }
    // camera: glide from the last beat's framing; slow push-in; handheld drift; punch = crash zoom
    const F = framingCached(si, j);
    let pos = F.cam.pos.clone(), tgt = F.cam.tgt.clone();
    const push = eOut(clamp(bt / Math.max(1, TB.end - TB.start))) * .05; pos.lerp(tgt, push);
    const sameStage = k => k >= 0 && LAYOUT.shotSeg[k] === sg;
    let prevF = null, prevEnd = 0;
    if (j > 0) { prevF = framingCached(si, j - 1); prevEnd = T0.beats[j - 1].end - T0.beats[j - 1].start; }
    else if (si > 0 && sameStage(si - 1)) { const pj = TL.scenes[si - 1].beats.length - 1; prevF = framingCached(si - 1, pj); }
    if (prevF && !(s.beats[j] && s.beats[j].cut)) { const q = eIO(bt / .7); if (q < 1) { const pp = prevF.cam.pos.clone().lerp(prevF.cam.tgt, .05); pos = pp.lerp(pos, q); tgt = prevF.cam.tgt.clone().lerp(tgt, q); } }
    if (B.punch && CH[B.punch]) { const c = CH[B.punch], st = charState(B.punch, si, t);
      if (st) { const pq = eOut(clamp((bt - (+B.punch_at || 0)) / .18)), head = new T.Vector3(st.x, c.height - c.R * 1.1, st.z), dir = pos.clone().sub(tgt).normalize();
        const close = head.clone().add(dir.multiplyScalar(4.2)); close.y += .05; pos.lerp(close, pq); tgt.lerp(head.clone().add(new T.Vector3(0, -.12, 0)), pq);
        const sh = bt - (+B.punch_at || 0); if (sh > 0 && sh < .3) { const k2 = (.3 - sh) / .3 * .025; pos.x += Math.sin(t * 95) * k2; pos.y += Math.cos(t * 81) * k2; } } }
    if (B.shake && bt < .45) { const k2 = (.45 - bt) / .45 * .04; pos.x += Math.sin(t * 90) * k2; pos.y += Math.cos(t * 77) * k2; }
    pos.x += Math.sin(t * .9) * .025 + Math.sin(t * 2.3) * .008; pos.y += Math.cos(t * .7) * .018;
    if (setG.userData.rock) pos.y += Math.sin(t * 7.3) * .006;
    CAM.position.copy(pos); CAM.lookAt(tgt); CAM.updateMatrixWorld(); CAM.updateProjectionMatrix();
    // 3D stickers beside the speaker, comic effects, speed streaks, dust
    for (const k in STICK) STICK[k].visible = false; for (const k in FXO) FXO[k].g.visible = false;
    const shows = [].concat(B.show || []).map(sh => typeof sh === 'string' ? { icon: sh } : sh).filter(o => o.icon);
    shows.forEach((o, n) => { const st = STICK[o.icon + '|' + (o.label || '')]; const who = o.on || B.who, c = CH[who], cs = who && charState(who, si, t); if (!st || !c || !cs) return;
      const q = bt - (+o.at || 0); if (q < 0) return; const camR = new T.Vector3(1, 0, 0).applyQuaternion(CAM.quaternion);
      const sx = (screen(who) || { x: 540 }).x, side = o.side ? (o.side === 'left' ? -1 : 1) : (sx < 540 ? 1 : -1);
      const head = new T.Vector3(cs.x, c.height - c.R * .5, cs.z), hv = head.clone().project(CAM), dd = CAM.position.distanceTo(head);
      const p = inView(head, hv.x + side * .5, hv.y + .04 - n * .3, [.6, .5, -.25]); p.add(new T.Vector3(0, 1, 0).applyQuaternion(CAM.quaternion).multiplyScalar(Math.sin(t * 3.2 + n) * .01 * dd));
      st.visible = true; st.position.copy(p); st.lookAt(CAM.position); st.rotateZ(Math.sin(t * 2.1 + n) * .06 - .04 * side); st.rotateY(Math.sin(t * 1.7) * .15);
      const sc = Math.max(.001, (function (x) { x = clamp(x); const c1 = 1.7; return 1 + (c1 + 1) * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); })(q / .35)); st.scale.setScalar(sc * dd * .11); });
    [].concat(B.fx || []).forEach((f, n) => { if (!f || !f.kind || f.kind === 'lines') return; const k = si + ':' + j + ':' + n; if (!FXO[k]) FXO[k] = buildFx(f.kind, f.text); animFx(FXO[k], f, B, si, t, bt, TB.end - TB.start); });
    streaks([].concat(B.fx || []).some(f => f && f.kind === 'lines'), t, bt);
    dust(!!setG.userData.interior, t);
    const blurOf = fr => fr && fr.subj && !fr.wide ? (fr.subj.length === 1 ? 2.4 : 1.3) : 0;
    let blur = blurOf(F); if (prevF && !(s.beats[j] && s.beats[j].cut)) blur = lerp(blurOf(prevF), blur, eIO(bt / .7));
    if (B.punch) blur = Math.max(blur, 2.4 * eOut(clamp(bt / .18)));
    renderDof(SB.dof === false ? 0 : blur, setG, [...Object.values(STICK), ...Object.values(FXO).map(o => o.g)].filter(o => o.visible).concat(STREAK && STREAK.visible ? [STREAK] : []));
  }
  // screen position of a character: x (px) at the head, feet y and head-top y (px)
  function screen(id) { const c = CH[id]; if (!c || !c.root.visible) return null;
    const v = new T.Vector3(), r = c.root.position; const pr = p => { v.copy(p).project(CAM); return [(v.x + 1) / 2 * W, (1 - v.y) / 2 * H]; };
    const hd = pr(new T.Vector3(r.x, c.height + .02, r.z)), ft = pr(new T.Vector3(r.x, 0, r.z)); return { x: hd[0], top: hd[1], foot: ft[1] }; }
  return { init, render, screen };
})();
