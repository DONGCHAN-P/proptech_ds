      const tl = gsap.timeline({ paused: true });
      // 큐 앵커: 자막 문구 일부로 시각을 찾는다 (재분할·재타이밍에도 유지)
      const T = (sub, off = 0) => {
        const c = CUES.find((x) => x[1].includes(sub));
        if (!c) throw new Error("cue anchor not found: " + sub);
        return c[0] + off;
      };
      const S0 = (id, off = 0) => SPANS[id][0] + off;
      const enter = (sel, t, d = 0.5) => tl.fromTo(sel, { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: d, ease: "power2.out" }, t);
      const fade = (sel, t, d = 0.45) => tl.fromTo(sel, { opacity: 0 }, { opacity: 1, duration: d, ease: "power1.out" }, t);
      const grow = (sel, t, d = 1.4, axis = "scaleY") => tl.fromTo(sel, { [axis]: 0 }, { [axis]: 1, duration: d, ease: "power2.inOut" }, t);
      const growX = (sel, t, d = 1.2) => grow(sel, t, d, "scaleX");
      const dim = (sel, t, o = 0.32) => tl.to(sel, { opacity: o, duration: 0.4, ease: "power1.out" }, t);
      const lit = (sel, t) => tl.to(sel, { opacity: 1, duration: 0.4, ease: "power1.out" }, t);
      const stagger = (sels, t, gap, fn = enter) => sels.forEach((s, i) => fn(s, t + i * gap));
      // 장면 경계: 안쪽 래퍼만 짧게 페이드
      for (const id of Object.keys(SPANS)) {
        const [s, d] = SPANS[id];
        tl.fromTo(`#${id}-w`, { opacity: 0 }, { opacity: 1, duration: 0.35, ease: "power1.out" }, s);
        tl.to(`#${id}-w`, { opacity: 0, duration: 0.3, ease: "power1.in" }, s + d - 0.3);
      }
      // 챕터 화면
      tl.fromTo("#card-w", { opacity: 0 }, { opacity: 1, duration: 0.35 }, 0);
      tl.fromTo("#card-t", { opacity: 0, x: -16 }, { opacity: 1, x: 0, duration: 0.6, ease: "power2.out" }, 0.35);
      tl.to("#card-w", { opacity: 0, duration: 0.3 }, CARD - 0.3);
