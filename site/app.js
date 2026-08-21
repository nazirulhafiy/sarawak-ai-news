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

  const backToTop = document.querySelector("[data-back-to-top]");
  if (backToTop) {
    function updateBackToTop() {
      backToTop.hidden = window.scrollY < 600;
    }

    backToTop.addEventListener("click", () => {
      const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
    });
    window.addEventListener("scroll", updateBackToTop, { passive: true });
    updateBackToTop();
  }

  const filter = document.querySelector("[data-category-filter]");
  const storyList = document.querySelector("[data-story-list]");

  if (!filter || !storyList) return;

  const buttons = Array.from(filter.querySelectorAll("[data-section-filter]"));
  const stories = Array.from(storyList.querySelectorAll(".story-card"));
  const status = filter.querySelector("[data-filter-status]");

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

  function applyFilter(section) {
    const activeButton = buttons.find((button) => button.dataset.sectionFilter === section);
    if (!activeButton) return;

    let visibleCount = 0;
    stories.forEach((story) => {
      const isVisible = section === "all" || story.dataset.section === section;
      story.hidden = !isVisible;

      if (isVisible) {
        visibleCount += 1;
        const rank = story.querySelector(".story-rank");
        if (rank) {
          rank.textContent = String(visibleCount);
          rank.setAttribute("aria-label", section === "all" ? `Chronological item ${visibleCount}` : `Filtered item ${visibleCount}`);
        }
      }
    });

    buttons.forEach((button) => {
      const isActive = button === activeButton;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-pressed", String(isActive));
    });

    if (status) {
      status.textContent = section === "all"
        ? `Showing all ${visibleCount} stories`
        : `Showing ${visibleCount} ${activeButton.dataset.filterLabel} stories`;
    }
  }

  filter.hidden = false;
  filter.addEventListener("click", (event) => {
    const button = event.target.closest("[data-section-filter]");
    if (button && filter.contains(button)) {
      const resetToAll = button.classList.contains("is-active") && button.dataset.sectionFilter !== "all";
      applyFilter(resetToAll ? "all" : button.dataset.sectionFilter);
    }
  });
  applyFilter("all");
})();
