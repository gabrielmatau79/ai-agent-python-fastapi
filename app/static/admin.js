(function () {
  "use strict";

  var STORAGE_KEY = "admin-completed-steps";
  var supportsToolsByProvider = window.__supportsToolsByProvider || {};

  var navLinks = Array.prototype.slice.call(document.querySelectorAll(".step"));
  var panels = Array.prototype.slice.call(document.querySelectorAll(".panel"));
  var providerSelect = document.getElementById("llmProvider");

  function loadCompletedSteps() {
    try {
      return JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "[]");
    } catch (err) {
      return [];
    }
  }

  function markStepCompleted(stepId) {
    var completed = loadCompletedSteps();
    if (completed.indexOf(stepId) === -1) {
      completed.push(stepId);
      try {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(completed));
      } catch (err) {
        /* localStorage unavailable — progress tracking is cosmetic only */
      }
    }
    var link = document.querySelector('.step[data-step="' + stepId + '"]');
    if (link) {
      link.classList.add("done");
    }
  }

  function currentProvider() {
    return providerSelect ? providerSelect.value : null;
  }

  function toolsSupported() {
    var provider = currentProvider();
    return provider ? supportsToolsByProvider[provider] !== false : true;
  }

  function applyProviderFieldVisibility() {
    var provider = currentProvider();
    if (!provider) {
      return;
    }
    document.querySelectorAll("fieldset[data-provider]").forEach(function (fieldset) {
      fieldset.hidden = fieldset.getAttribute("data-provider") !== provider;
    });
    document.querySelectorAll("[data-unsupported-providers]").forEach(function (el) {
      var unsupported = el.getAttribute("data-unsupported-providers").split(",");
      el.hidden = unsupported.indexOf(provider) !== -1;
    });
  }

  function applyToolsGating() {
    var enabled = toolsSupported();
    document.querySelectorAll('[data-requires-tools="true"]').forEach(function (el) {
      el.hidden = !enabled;
    });
    if (!enabled && activePanelId() && requiresTools(activePanelId())) {
      activateStep("llm");
    }
  }

  function requiresTools(stepId) {
    var panel = document.querySelector('.panel[data-panel="' + stepId + '"]');
    return !!panel && panel.getAttribute("data-requires-tools") === "true";
  }

  function activePanelId() {
    var active = panels.filter(function (panel) {
      return !panel.hidden;
    })[0];
    return active ? active.getAttribute("data-panel") : null;
  }

  function firstVisibleStep() {
    var visible = navLinks.filter(function (link) {
      return !link.hidden;
    })[0];
    return visible ? visible.getAttribute("data-step") : "llm";
  }

  function activateStep(stepId) {
    if (requiresTools(stepId) && !toolsSupported()) {
      stepId = firstVisibleStep();
    }
    panels.forEach(function (panel) {
      panel.hidden = panel.getAttribute("data-panel") !== stepId;
    });
    navLinks.forEach(function (link) {
      link.classList.toggle("active", link.getAttribute("data-step") === stepId);
    });
    window.history.replaceState(null, "", "#" + stepId);
  }

  navLinks.forEach(function (link) {
    link.addEventListener("click", function (event) {
      event.preventDefault();
      activateStep(link.getAttribute("data-step"));
    });
  });

  if (providerSelect) {
    providerSelect.addEventListener("change", function () {
      applyProviderFieldVisibility();
      applyToolsGating();
    });
  }

  document.body.addEventListener("htmx:afterRequest", function (event) {
    if (!event.detail.successful) {
      return;
    }
    var form = event.detail.elt;
    var panel = form.closest(".panel");
    if (panel) {
      markStepCompleted(panel.getAttribute("data-panel"));
    }
    if (panel && panel.getAttribute("data-panel") === "llm") {
      applyToolsGating();
    }
  });

  loadCompletedSteps().forEach(markStepCompleted);
  applyProviderFieldVisibility();
  applyToolsGating();
  activateStep(window.location.hash ? window.location.hash.slice(1) : firstVisibleStep());

  window.confirmMemoryChange = function (form) {
    var current = form.elements["_currentType"].value;
    var next = form.elements["agentMemoryType"].value;
    if (current === "memory" && next !== "memory") {
      return window.confirm(
        "Switching away from in-memory sessions will drop all active conversation history. Continue?"
      );
    }
    return true;
  };
})();
