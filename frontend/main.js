import { setState } from "./state.js";
import { initRouter, updateSidebarVisibility } from "./router.js";

function initShell() {
  const overlay = document.getElementById("sidebar-overlay");
  overlay?.addEventListener("click", () => {
    setState({ sidebarOpen: false });
    updateSidebarVisibility();
  });

  window.addEventListener("resize", () => {
    if (window.innerWidth > 768) {
      setState({ sidebarOpen: false });
      updateSidebarVisibility();
    }
  });

  initRouter();
  startClock();
}

function startClock() {
  const tick = () => {
    const clock = document.querySelector(".header__clock");
    if (clock) {
      const now = new Date();
      clock.dateTime = now.toISOString();
      clock.textContent = now.toLocaleString("pt-BR", {
        weekday: "short",
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      });
    }
  };
  tick();
  setInterval(tick, 30000);
}

initShell();
