(() => {
  const navigation = performance.getEntriesByType?.("navigation")[0];
  const isReload = navigation?.type === "reload";

  if ("scrollRestoration" in history) {
    history.scrollRestoration = "manual";
  }

  function resetReloadPosition() {
    if (isReload) requestAnimationFrame(() => window.scrollTo(0, 0));
  }

  resetReloadPosition();
  window.addEventListener("pageshow", resetReloadPosition);

  const themeToggle = document.querySelector("[data-theme-toggle]");
  const navToggle = document.querySelector("[data-nav-toggle]");
  const siteNav = document.querySelector(".site-nav");
  function closeNavigation() {
    navToggle?.setAttribute("aria-expanded", "false");
    navToggle?.setAttribute("aria-label", "Open navigation");
    navToggle?.setAttribute("title", "Open navigation");
    siteNav?.classList.remove("is-open");
  }
  navToggle?.addEventListener("click", () => {
    const isOpen = navToggle.getAttribute("aria-expanded") === "true";
    navToggle.setAttribute("aria-expanded", String(!isOpen));
    navToggle.setAttribute("aria-label", isOpen ? "Open navigation" : "Close navigation");
    navToggle.setAttribute("title", isOpen ? "Open navigation" : "Close navigation");
    siteNav?.classList.toggle("is-open", !isOpen);
  });
  siteNav?.addEventListener("click", (event) => {
    if (event.target.closest("a")) {
      closeNavigation();
    }
  });
  document.addEventListener("click", (event) => {
    if (!siteNav?.classList.contains("is-open")) return;
    if (event.target.closest("[data-nav-toggle], .site-nav")) return;
    closeNavigation();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && siteNav?.classList.contains("is-open")) {
      closeNavigation();
      navToggle?.focus();
    }
  });
  const themeMedia = window.matchMedia?.("(prefers-color-scheme: dark)");
  let storedTheme = null;
  try {
    storedTheme = localStorage.getItem("sarawak-theme");
  } catch (error) {}

  function setTheme(theme, persist = false) {
    const isDark = theme === "dark";
    if (isDark) document.documentElement.setAttribute("data-theme", "dark");
    else document.documentElement.removeAttribute("data-theme");
    if (persist) {
      try {
        localStorage.setItem("sarawak-theme", isDark ? "dark" : "light");
      } catch (error) {}
    }
    if (themeToggle) {
      const nextLabel = isDark ? "Switch to light mode" : "Switch to dark mode";
      themeToggle.setAttribute("aria-label", nextLabel);
      themeToggle.setAttribute("title", nextLabel);
      themeToggle.setAttribute("aria-pressed", String(isDark));
    }
  }

  setTheme(document.documentElement.hasAttribute("data-theme") ? "dark" : "light");
  themeToggle?.addEventListener("click", () => {
    setTheme(document.documentElement.hasAttribute("data-theme") ? "light" : "dark", true);
  });
  if (!storedTheme && themeMedia) {
    themeMedia.addEventListener?.("change", (event) => setTheme(event.matches ? "dark" : "light"));
  }

  const siteBar = document.querySelector(".bar");
  if (siteBar) {
    function updateStickyBar() {
      siteBar.classList.toggle("is-scrolled", window.scrollY > 0);
    }
    window.addEventListener("scroll", updateStickyBar, { passive: true });
    updateStickyBar();
  }

  const backToTop = document.querySelector("[data-back-to-top]");
  if (backToTop) {
    function updateBackToTop() {
      const show = window.scrollY >= 600;
      backToTop.hidden = !show;
      backToTop.tabIndex = show ? 0 : -1;
      backToTop.setAttribute("aria-hidden", show ? "false" : "true");
    }

    backToTop.addEventListener("click", () => {
      const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
    });
    window.addEventListener("scroll", updateBackToTop, { passive: true });
    updateBackToTop();
  }

  const revealCards = document.querySelectorAll(".story-card");
  if (revealCards.length && "IntersectionObserver" in window) {
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-revealed");
        revealObserver.unobserve(entry.target);
      });
    }, { rootMargin: "0px", threshold: 0 });
    revealCards.forEach((card) => revealObserver.observe(card));
  } else {
    revealCards.forEach((card) => card.classList.add("is-revealed"));
  }

  const storyList = document.querySelector("[data-story-list]");
  const stories = storyList
    ? Array.from(storyList.querySelectorAll(".story-card"))
    : Array.from(document.querySelectorAll(".story-card"));

  stories.forEach((story) => {
    const link = story.querySelector("h2 a");
    if (!link) return;

    story.addEventListener("click", (event) => {
      if (event.target.closest("a, button, input, select, textarea")) return;
      link.click();
    });
    story.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      link.click();
    });
  });
})();
