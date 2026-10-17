"use strict";
const model = document.getElementById("packet-model");
if (model) {
  const brightness = document.getElementById("packet-brightness");
  const autoChecksum = document.getElementById("packet-checksum");
  const sum = document.getElementById("packet-sum");
  const cells = Array.from(model.querySelectorAll(".packet-bytes > div"));
  const previous = document.getElementById("packet-prev");
  const next = document.getElementById("packet-next");
  const play = document.getElementById("packet-play");
  const hex = value => value.toString(16).toUpperCase().padStart(2, "0");
  let sentChecksum = 0xA5 ^ 0x01 ^ Number(brightness.value);
  let accepted = Number(brightness.value);
  let step = 0;
  let timer = null;
  const stop = () => {
    clearInterval(timer);
    timer = null;
    play.textContent = "Пройти приём";
  };
  const render = () => {
    const requested = Number(brightness.value);
    const expected = 0xA5 ^ 0x01 ^ requested;
    if (autoChecksum.checked) sentChecksum = expected;
    const valid = sentChecksum === expected;
    if (valid) accepted = requested;
    document.getElementById("brightness-value").textContent = String(requested);
    document.getElementById("packet-payload").textContent = hex(requested);
    sum.textContent = hex(sentChecksum);
    sum.dataset.valid = String(valid);
    document.getElementById("packet-status").textContent = valid
      ? "XOR совпадает. Команда принята."
      : `XOR не совпадает: ожидалось ${hex(expected)}. Команда отклонена.`;
    document.getElementById("packet-output").textContent = `Яркость лампы: ${accepted} из 100.`;
    document.getElementById("packet-lamp").style.opacity = String(0.08 + accepted * 0.0092);
    const descriptions = [
      "1 из 4. Разбор текущего пакета: A5 отмечает начало, 01 выбирает команду яркости.",
      `2 из 4. Поле ${hex(requested)} задаёт желаемую яркость ${requested} из 100.`,
      `3 из 4. Вычисленный XOR ${hex(expected)} сравнивается с переданным ${hex(sentChecksum)}.`,
      valid ? `4 из 4. Проверка прошла: приёмник установил яркость ${accepted}.`
        : `4 из 4. Проверка не прошла: приёмник сохранил яркость ${accepted}.`
    ];
    cells.forEach((cell, i) => {
      cell.dataset.active = String((step === 0 && i < 2) || (step === 1 && i === 2) || (step === 2 && i === 3));
    });
    document.getElementById("packet-step-status").textContent = descriptions[step];
    previous.disabled = step === 0;
    next.disabled = step === 3;
  };
  const change = () => { stop(); step = 0; render(); };
  brightness.addEventListener("input", change);
  autoChecksum.addEventListener("change", change);
  previous.addEventListener("click", () => { stop(); step = Math.max(0, step - 1); render(); });
  next.addEventListener("click", () => { stop(); step = Math.min(3, step + 1); render(); });
  play.addEventListener("click", () => {
    if (timer !== null) { stop(); return; }
    if (step === 3) step = 0;
    render();
    play.textContent = "Пауза";
    timer = setInterval(() => {
      step += 1;
      render();
      if (step === 3) stop();
    }, 1800);
  });
  document.addEventListener("visibilitychange", () => { if (document.hidden) stop(); });
  model.hidden = false;
  render();
}
