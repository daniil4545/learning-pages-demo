const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const script = fs.readFileSync("site/assets/player.js", "utf8");

function browser(saved) {
  const events = new Map();
  let stored = JSON.stringify(saved);
  const audio = {
    id: "lecture-audio",
    src: "https://example.org/audio/lesson.mp3", currentSrc: "", readyState: 0,
    currentTime: 0, duration: 300, playbackRate: 1, ended: false,
    addEventListener: (name, handler) => events.set(name, handler)
  };
  const status = { textContent: "" };
  vm.runInNewContext(script, {
    URL, Number, JSON, Math,
    document: { querySelectorAll: () => [audio], getElementById: () => status },
    window: { addEventListener: (name, handler) => events.set(name, handler) },
    localStorage: {
      getItem: () => stored,
      setItem: (_key, value) => { stored = value; }
    }
  });
  return { audio, fire: name => events.get(name)(), saved: () => JSON.parse(stored) };
}

test("closing before metadata does not erase saved position", () => {
  const page = browser({ time: 180, rate: 1.5 });
  page.fire("pagehide");
  assert.deepEqual(page.saved(), { time: 180, rate: 1.5 });
  page.fire("loadedmetadata");
  assert.equal(page.audio.currentTime, 180);
  assert.equal(page.audio.playbackRate, 1.5);
});

test("native speed change and pause save restored state", () => {
  const page = browser({ time: 50, rate: 1 });
  page.fire("loadedmetadata");
  page.audio.currentTime = 70;
  page.audio.playbackRate = 1.75;
  page.fire("ratechange");
  page.fire("pause");
  assert.deepEqual(page.saved(), { time: 70, rate: 1.75 });
});

test("finishing an episode resets its saved position", () => {
  const page = browser({ time: 50, rate: 1 });
  page.fire("loadedmetadata");
  page.audio.currentTime = 300;
  page.audio.ended = true;
  page.fire("ended");
  assert.equal(page.saved().time, 0);
});

test("each episode restores and saves its own position", () => {
  const stored = new Map([
    ["lecture-position:/audio/one.mp3", JSON.stringify({ time: 20, rate: 1 })],
    ["lecture-position:/audio/two.mp3", JSON.stringify({ time: 90, rate: 1.5 })]
  ]);
  const players = ["one", "two"].map((name, index) => {
    const events = new Map();
    return {
      id: index ? "lecture-audio-2" : "lecture-audio",
      src: `https://example.org/audio/${name}.mp3`, readyState: 0,
      currentTime: 0, duration: 300, playbackRate: 1, ended: false,
      addEventListener: (event, handler) => events.set(event, handler), events
    };
  });
  const statuses = new Map([
    ["audio-status", { textContent: "" }], ["audio-status-2", { textContent: "" }]
  ]);
  vm.runInNewContext(script, {
    URL, Number, JSON, Math,
    document: { querySelectorAll: () => players, getElementById: id => statuses.get(id) },
    window: { addEventListener: () => {} },
    localStorage: { getItem: key => stored.get(key), setItem: (key, value) => stored.set(key, value) }
  });
  players.forEach(player => player.events.get("loadedmetadata")());
  assert.equal(players[0].currentTime, 20);
  assert.equal(players[1].currentTime, 90);
  players[1].currentTime = 110;
  players[1].events.get("pause")();
  assert.equal(JSON.parse(stored.get("lecture-position:/audio/one.mp3")).time, 20);
  assert.equal(JSON.parse(stored.get("lecture-position:/audio/two.mp3")).time, 110);
});
