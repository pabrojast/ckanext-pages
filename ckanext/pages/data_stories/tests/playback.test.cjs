const test = require('node:test');
const assert = require('node:assert/strict');
const Playback = require('../../public/js/story-playback.js');
function setup() {
  let now = 0, next = 0, playing;
  const timers = new Map(); let serial = 0;
  const clock = {setTimeout(fn, delay) {const id = ++serial; timers.set(id, {fn, at: now + delay}); return id;}, clearTimeout(id) {timers.delete(id);}};
  const playback = new Playback({clock, advance() {next++;}, changed(value) {playing = value;}});
  return {playback, count: () => next, playing: () => playing, tick(ms) {now += ms; for (const [id, timer] of timers) if (timer.at <= now) {timers.delete(id); timer.fn();}}};
}
test('starts manually and waits for both visual acknowledgements', () => {
  const p = setup(); p.playback.step(2, false, ['map', 'dashboard']); p.tick(9000); assert.equal(p.count(), 0);
  p.playback.toggle(); p.playback.visual('map', false); p.tick(9000); assert.equal(p.count(), 0);
  p.playback.visual('dashboard', false); p.tick(1999); assert.equal(p.count(), 0); p.tick(1); assert.equal(p.count(), 1);
});
test('pause and visual failure cancel pending advancement', () => {
  const p = setup(); p.playback.step(1, false); p.playback.toggle(); p.playback.pause(); p.tick(1000); assert.equal(p.count(), 0);
  p.playback.toggle(); p.playback.visual('map', false, true); p.tick(1000); assert.equal(p.count(), 0); assert.equal(p.playing(), false);
});
test('last slide stops instead of wrapping, and navigation resets elapsed time', () => {
  const p = setup(); p.playback.step(1, false); p.playback.toggle(); p.tick(500); p.playback.step(2, true); p.tick(1500); assert.equal(p.playing(), true); p.tick(500); assert.equal(p.playing(), false); assert.equal(p.count(), 0);
});
