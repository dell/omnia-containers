/**
 * Collapsible Tables with Height + Ratio Combined
 *
 * - Uses smart logic based on table height and hidden ratio
 * - Collapses only when both conditions are met
 * - Supports manual mode with data attributes
 * - Re-evaluates on window resize
 */
(function () {
  "use strict";

  // ============== CONFIGURATION ==============
  var CONFIG = {
    // Max visible height before considering collapse
    defaultMaxHeight: "70vh",

    // ---- Ratio Thresholds ----
    // Minimum hidden pixels to justify collapsing
    minHiddenPixels: 100,

    // Minimum ratio of hidden content to total height
    // e.g., 0.2 = at least 20% of the table must be hidden
    minHiddenRatio: 0.2,

    // Selector mode
    // "all"    → auto-apply to every table
    // "manual" → only tables inside <div class="collapsible-table">
    mode: "all",

    // Show stats in the button (e.g., "Expand table (40% hidden)")
    showStats: false
  };
  // ===========================================

  /**
   * Convert height string to pixels
   */
  function toPixels(heightStr) {
    if (!heightStr) return null;
    heightStr = heightStr.toString().trim();

    if (heightStr.endsWith("px")) return parseFloat(heightStr);
    if (heightStr.endsWith("vh")) {
      return (parseFloat(heightStr) / 100) * window.innerHeight;
    }
    if (heightStr.endsWith("%")) {
      return (parseFloat(heightStr) / 100) * window.innerHeight;
    }
    return parseFloat(heightStr);
  }

  /**
   * Smart decision: should this table be collapsed?
   */
  function shouldCollapse(tableHeight, maxHeightPx, options) {
    var minPixels = options.minHiddenPixels;
    var minRatio = options.minHiddenRatio;

    // Not taller than max height — no collapse needed
    if (tableHeight <= maxHeightPx) {
      return { collapse: false, reason: "Table fits within max height" };
    }

    var hiddenPixels = tableHeight - maxHeightPx;
    var hiddenRatio = hiddenPixels / tableHeight;

    var meetsMinPixels = hiddenPixels >= minPixels;
    var meetsMinRatio = hiddenRatio >= minRatio;

    if (!meetsMinPixels) {
      return {
        collapse: false,
        reason: "Hidden area (" + Math.round(hiddenPixels) +
                "px) < minimum (" + minPixels + "px)"
      };
    }

    if (!meetsMinRatio) {
      return {
        collapse: false,
        reason: "Hidden ratio (" + Math.round(hiddenRatio * 100) +
                "%) < minimum (" + Math.round(minRatio * 100) + "%)"
      };
    }

    return {
      collapse: true,
      hiddenPixels: hiddenPixels,
      hiddenRatio: hiddenRatio,
      reason: "Collapsing — " + Math.round(hiddenRatio * 100) +
              "% hidden (" + Math.round(hiddenPixels) + "px)"
    };
  }

  /**
   * Process a single table
   */
  function processTable(table, options) {
    var maxHeightPx = toPixels(options.maxHeight);
    if (!maxHeightPx) return;

    // Measure actual table height
    var tableHeight = table.scrollHeight;

    // Smart check — height + ratio
    var decision = shouldCollapse(tableHeight, maxHeightPx, options);

    // Debug logging (optional — remove in production)
    // console.log("Table:", table, decision.reason);

    if (!decision.collapse) return;

    // Wrap table
    var wrapper = table.parentNode;
    if (!wrapper.classList || !wrapper.classList.contains("collapsible-table-wrapper")) {
      wrapper = document.createElement("div");
      wrapper.className = "collapsible-table-wrapper";
      table.parentNode.insertBefore(wrapper, table);
      wrapper.appendChild(table);
    }

    // Apply collapsed state
    wrapper.classList.add("collapsed");
    wrapper.style.maxHeight = maxHeightPx + "px";

    // Button text
    var hiddenPercent = Math.round(decision.hiddenRatio * 100);
    var expandText = CONFIG.showStats
      ? "More (" + hiddenPercent + "% hidden) "
      : "More ";
    var collapseText = "Less ";

    // Create toggle button
    var btn = document.createElement("button");
    btn.className = "table-toggle-btn";
    btn.innerHTML = expandText + '<span class="arrow">▼</span>';

    btn.addEventListener("click", function () {
      var isExpanded = wrapper.classList.toggle("expanded");
      wrapper.classList.toggle("collapsed", !isExpanded);
      btn.classList.toggle("expanded", isExpanded);

      if (isExpanded) {
        btn.innerHTML = collapseText + '<span class="arrow">▼</span>';
      } else {
        btn.innerHTML = expandText + '<span class="arrow">▼</span>';
        wrapper.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    });

    wrapper.parentNode.insertBefore(btn, wrapper.nextSibling);
  }

  /**
   * Parse options from a wrapper element's data attributes
   */
  function getOptions(el) {
    return {
      maxHeight: (el && el.getAttribute("data-max-height")) ||
                 CONFIG.defaultMaxHeight,
      minHiddenPixels: parseFloat(
        (el && el.getAttribute("data-min-hidden-pixels")) ||
        CONFIG.minHiddenPixels
      ),
      minHiddenRatio: parseFloat(
        (el && el.getAttribute("data-min-hidden-ratio")) ||
        CONFIG.minHiddenRatio
      )
    };
  }

  /**
   * Initialize
   */
  function init() {
    if (CONFIG.mode === "manual") {
      var manualTables = document.querySelectorAll(".collapsible-table");
      document.querySelectorAll(".collapsible-table").forEach(function (el) {
        var table = el.querySelector("table");
        if (!table) return;
        processTable(table, getOptions(el));
      });
    } else {
      var allTables = document.querySelectorAll(".md-typeset table");
      document.querySelectorAll(".md-typeset table").forEach(function (table) {
        var wrapper = table.closest(".collapsible-table");
        processTable(table, getOptions(wrapper));
      });
    }
  }

  /**
   * Cleanup for re-initialization
   */
  function cleanup() {
    document.querySelectorAll(".table-toggle-btn").forEach(function (btn) {
      btn.remove();
    });

    document.querySelectorAll(".collapsible-table-wrapper").forEach(
      function (wrapper) {
        wrapper.classList.remove("collapsed", "expanded");
        wrapper.style.maxHeight = "";

        // Unwrap auto-wrapped tables
        if (!wrapper.classList.contains("collapsible-table")) {
          var table = wrapper.querySelector("table");
          if (table) {
            wrapper.parentNode.insertBefore(table, wrapper);
            wrapper.remove();
          }
        }
      }
    );
  }

  // Run on load
  init();

  // Re-evaluate on resize
  var resizeTimer;
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      cleanup();
      init();
    }, 250);
  });
})();
