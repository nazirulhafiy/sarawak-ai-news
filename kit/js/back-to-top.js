  const backToTop = document.querySelector("[data-back-to-top]");
  if (backToTop) {
    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    let hideTimer = 0;

    function updateBackToTop() {
      const show = window.scrollY >= 600;
      const reduce = Boolean(reduceMotion?.matches);
      if (show) {
        window.clearTimeout(hideTimer);
        backToTop.hidden = false;
        if (reduce) backToTop.classList.add("is-visible");
        else requestAnimationFrame(() => {
          if (window.scrollY >= 600) backToTop.classList.add("is-visible");
        });
        return;
      }
      backToTop.classList.remove("is-visible");
      if (reduce || backToTop.hidden) {
        backToTop.hidden = true;
        return;
      }
      window.clearTimeout(hideTimer);
      hideTimer = window.setTimeout(() => {
        if (window.scrollY < 600) backToTop.hidden = true;
      }, 200);
    }

    backToTop.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: reduceMotion?.matches ? "auto" : "smooth" });
    });
    window.addEventListener("scroll", updateBackToTop, { passive: true });
    updateBackToTop();
  }
