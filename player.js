"use strict";
const audio = document.getElementById("lecture-audio");
const speed = document.getElementById("speed");
const status = document.getElementById("audio-status");
const storageKey = "learning-demo:kv-cache:v1";
let saved = null;
try { saved = JSON.parse(localStorage.getItem(storageKey)); }
catch { status.textContent = "Сохранение позиции недоступно в этом браузере."; }
if (saved && [1, 1.25, 1.5, 2].includes(saved.rate)) {
  speed.value = String(saved.rate);
}
audio.playbackRate = Number(speed.value);
audio.addEventListener("loadedmetadata", () => {
  if (saved && Number.isFinite(saved.time) && saved.time > 0 && saved.time < audio.duration - 1) {
    audio.currentTime = saved.time;
    status.textContent = "Продолжение с сохранённой позиции. Нажми воспроизведение.";
  }
});
function savePosition() {
  try {
    localStorage.setItem(storageKey, JSON.stringify({
      time: audio.ended ? 0 : audio.currentTime,
      rate: audio.playbackRate
    }));
  } catch {
    status.textContent = "Сохранение позиции недоступно в этом браузере.";
  }
}
speed.addEventListener("change", () => {
  audio.playbackRate = Number(speed.value);
  savePosition();
});
let lastSaved = -1;
audio.addEventListener("timeupdate", () => {
  const second = Math.floor(audio.currentTime);
  if (second !== lastSaved) { lastSaved = second; savePosition(); }
});
audio.addEventListener("pause", savePosition);
audio.addEventListener("ended", savePosition);
audio.addEventListener("error", () => {
  status.textContent = "Не удалось загрузить аудио. Обнови страницу или открой MP3 напрямую.";
});
window.addEventListener("pagehide", savePosition);
