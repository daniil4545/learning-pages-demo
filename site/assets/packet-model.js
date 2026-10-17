"use strict";
const model = document.getElementById("packet-model");
if (model) {
  const brightness = document.getElementById("packet-brightness");
  const autoChecksum = document.getElementById("packet-checksum");
  const sum = document.getElementById("packet-sum");
  const hex = value => value.toString(16).toUpperCase().padStart(2, "0");
  let sentChecksum = 0xA5 ^ 0x01 ^ Number(brightness.value);
  let accepted = Number(brightness.value);
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
  };
  brightness.addEventListener("input", render);
  autoChecksum.addEventListener("change", render);
  model.hidden = false;
  render();
}
