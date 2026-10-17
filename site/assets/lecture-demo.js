"use strict";
const figure = document.querySelector("#algorithm svg.d");
const steps = [
  "1 из 6. Вопрос определяет, что должно стать понятно после лекции.",
  "2 из 6. Агент читает источники; из видео получает субтитры.",
  "3 из 6. План связывает механизм, пример и подходящую схему.",
  "4 из 6. Объяснение собирается в самостоятельную HTML-страницу.",
  "5 из 6. Аудио готовится только после отдельного запроса или согласия.",
  "6 из 6. Проверенная страница добавляется в каталог и публикуется."
];
if (figure) {
  const nodes = Array.from(figure.querySelectorAll(":scope > rect"));
  const previous = document.getElementById("step-prev");
  const next = document.getElementById("step-next");
  const play = document.getElementById("step-play");
  const status = document.getElementById("step-status");
  let step = 0;
  let timer = null;
  const marker = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  marker.setAttribute("r", "5");
  marker.setAttribute("class", "step-marker");
  marker.setAttribute("aria-hidden", "true");
  figure.append(marker);
  figure.classList.add("step-animation");
  const render = () => {
    nodes.forEach((node, index) => { node.dataset.active = String(index === step); });
    const y = Number(nodes[step].getAttribute("y")) + 30;
    const x = Number(nodes[step].getAttribute("x")) - 6;
    marker.style.transform = `translate(${x}px, ${y}px)`;
    previous.disabled = step === 0;
    next.disabled = step === steps.length - 1;
    status.textContent = steps[step];
  };
  const stop = () => {
    clearInterval(timer);
    timer = null;
    play.textContent = "Пройти автоматически";
  };
  previous.addEventListener("click", () => { stop(); step = Math.max(0, step - 1); render(); });
  next.addEventListener("click", () => { stop(); step = Math.min(steps.length - 1, step + 1); render(); });
  play.addEventListener("click", () => {
    if (timer !== null) { stop(); return; }
    if (step === steps.length - 1) step = 0;
    render();
    play.textContent = "Пауза";
    timer = setInterval(() => {
      step += 1;
      render();
      if (step === steps.length - 1) stop();
    }, 1600);
  });
  document.addEventListener("visibilitychange", () => { if (document.hidden) stop(); });
  document.getElementById("step-demo").hidden = false;
  render();
}
