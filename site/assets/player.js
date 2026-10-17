"use strict";
for (const audio of document.querySelectorAll(".library-player audio")) {
  const status = document.getElementById(audio.id.replace("lecture-audio", "audio-status"));
  const key = "lecture-position:" + new URL(audio.currentSrc || audio.src).pathname;
  let saved = null;
  try { saved = JSON.parse(localStorage.getItem(key)); }
  catch { status.textContent = "Сохранение позиции недоступно в этом браузере."; }
  let restored = false;
  const restore = () => {
    if (saved && Number.isFinite(saved.rate) && saved.rate >= 0.5 && saved.rate <= 4) {
      audio.playbackRate = saved.rate;
    }
    if (saved && Number.isFinite(saved.time) && saved.time > 0 && saved.time < audio.duration - 1) {
      audio.currentTime = saved.time;
      status.textContent = "Продолжение с сохранённой позиции. Нажми воспроизведение.";
    }
    restored = true;
  };
  if (audio.readyState >= 1) restore();
  else audio.addEventListener("loadedmetadata", restore, { once: true });
  const save = () => {
    if (!restored) return;
    try {
      localStorage.setItem(key, JSON.stringify({
        time: audio.ended ? 0 : audio.currentTime, rate: audio.playbackRate
      }));
    } catch { status.textContent = "Сохранение позиции недоступно в этом браузере."; }
  };
  let second = -1;
  audio.addEventListener("timeupdate", () => {
    const current = Math.floor(audio.currentTime);
    if (current !== second) { second = current; save(); }
  });
  for (const event of ["pause", "ended", "ratechange"]) audio.addEventListener(event, save);
  audio.addEventListener("error", () => {
    status.textContent = "Аудио не загрузилось. Обнови страницу и попробуй снова.";
  });
  window.addEventListener("pagehide", save);
}
