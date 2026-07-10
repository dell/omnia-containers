/**
 * Collapsible Tables
 *
 * - Automatically collapses markdown tables based on smart criteria
 * - Uses ratio-based logic to determine if collapsing is worth it
 * - Preserves original table styling
 */
(function () {
  "use strict";

  // ============== CONFIGURATION ==============
  var CONFIG = {
    defaultMaxRows: 10,      // Default visible rows
    minHiddenRows: 3,         // At least this many rows must be hidden
    minHiddenRatio: 0.2       // At least 20% of rows must be hidden
  };
  // ===========================================

  /**
   * Decide whether collapsing is worth it
   */
  function shouldCollapse(totalRows, maxVisible) {
    var hiddenRows = totalRows - maxVisible;

    if (hiddenRows <= 0) return false;

    var meetsMinHidden = hiddenRows >= CONFIG.minHiddenRows;
    var meetsRatio = (hiddenRows / totalRows) >= CONFIG.minHiddenRatio;

    // Both conditions must be true
    return meetsMinHidden && meetsRatio;
  }

  function init() {
    var tables = document.querySelectorAll(".md-typeset table");
    
    for (var i = 0; i < tables.length; i++) {
      var table = tables[i];
      
      // Skip CSV tables (they have csv-table class)
      if (table.classList.contains("csv-table")) continue;
      
      // Count rows (excluding header)
      var tbody = table.querySelector("tbody");
      if (!tbody) continue;
      
      var rows = tbody.querySelectorAll("tr");
      var totalRows = rows.length;
      
      // Smart check — is collapsing worth it?
      if (!shouldCollapse(totalRows, CONFIG.defaultMaxRows)) continue;
      
      var maxRows = CONFIG.defaultMaxRows;
      var hiddenCount = totalRows - maxRows;
      
      // Store hidden rows for later use
      var hiddenRows = [];
      
      // Hide rows beyond the limit
      for (var j = 0; j < rows.length; j++) {
        if (j >= maxRows) {
          rows[j].classList.add("hidden-row");
          hiddenRows.push(rows[j]);
        }
      }
      
      // Create toggle button
      var btn = document.createElement("button");
      btn.className = "table-toggle-btn";
      btn.innerHTML = 'Show ' + hiddenCount + ' more rows <span class="arrow">▼</span>';
      
      btn.addEventListener("click", (function(btn, hiddenRows, hiddenCount) {
        return function() {
          var isExpanded = btn.classList.toggle("expanded");
          
          if (isExpanded) {
            btn.innerHTML = 'Show less <span class="arrow">▼</span>';
            // Show hidden rows
            for (var k = 0; k < hiddenRows.length; k++) {
              hiddenRows[k].classList.add("visible");
            }
          } else {
            btn.innerHTML = 'Show ' + hiddenCount + ' more rows <span class="arrow">▼</span>';
            // Hide rows again
            for (var k = 0; k < hiddenRows.length; k++) {
              hiddenRows[k].classList.remove("visible");
            }
          }
        };
      })(btn, hiddenRows, hiddenCount));
      
      // Insert button after the table
      table.parentNode.insertBefore(btn, table.nextSibling);
    }
  }

  // Run after DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
