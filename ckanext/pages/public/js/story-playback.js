/* Playback waits for the current visual state, never for a guessed load delay. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.StoryPlayback = factory();
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';
  return function StoryPlayback(options) {
    const clock = options.clock || globalThis;
    const busy = new Set();
    let playing = false, timer, seconds = 10, last = false;
    function clear() { clock.clearTimeout(timer); timer = undefined; }
    function pause() { playing = false; clear(); options.changed(false); }
    function arm() {
      clear();
      if (!playing || busy.size) return;
      timer = clock.setTimeout(() => {
        timer = undefined;
        if (last) pause(); else options.advance();
      }, seconds * 1000);
    }
    return {
      pause,
      toggle() { if (playing) pause(); else { playing = true; options.changed(true); arm(); } },
      step(duration, isLast, waiting) {
        clear(); busy.clear(); (waiting || []).forEach(key => busy.add(key));
        seconds = Number.isFinite(duration) && duration >= 1 && duration <= 600 ? duration : 10;
        last = isLast; arm();
      },
      visual(key, pending, error) {
        if (error) { pause(); return; }
        if (pending) busy.add(key); else busy.delete(key);
        arm();
      },
      dispose() { clear(); playing = false; busy.clear(); }
    };
  };
});
