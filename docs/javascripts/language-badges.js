/**
 * Dynamic language pill badges and CSV table formatting for code blocks.
 *
 * - Automatically adds language type badges to all code blocks
 * - Converts CSV code blocks to formatted tables with toggle functionality
 */
(function () {
  "use strict";

  function init() {
    // Find all code blocks
    var codeBlocks = document.querySelectorAll(".md-typeset .highlight");
    
    for (var i = 0; i < codeBlocks.length; i++) {
      var codeBlock = codeBlocks[i];
      var filename = codeBlock.querySelector(".filename");
      
      // Extract language from class names
      var language = null;
      for (var j = 0; j < codeBlock.classList.length; j++) {
        var className = codeBlock.classList[j];
        if (className.startsWith("language-") && className !== "language-text") {
          language = className.replace("language-", "");
          break;
        }
      }
      
      // Check if it's a CSV block (by language class, filename content, or data structure)
      var isCsv = (language === "csv") || (filename && filename.textContent.toLowerCase().includes(".csv"));
      
      // If not detected by class or filename, check the content
      if (!isCsv) {
        var codeElement = codeBlock.querySelector("code");
        if (codeElement) {
          var content = codeElement.textContent.trim();
          // Check if content looks like CSV: contains commas, multiple lines, and has header-like structure
          var lines = content.split("\n");
          if (lines.length > 1 && content.includes(",")) {
            // Check if first line has commas and subsequent lines have similar structure
            var firstLineCommas = lines[0].split(",").length;
            var looksLikeCsv = true;
            for (var k = 1; k < Math.min(lines.length, 3); k++) {
              if (lines[k].trim() && lines[k].split(",").length !== firstLineCommas && lines[k].split(",").length > 1) {
                looksLikeCsv = false;
                break;
              }
            }
            if (looksLikeCsv && firstLineCommas > 2) {
              isCsv = true;
            }
          }
        }
      }
      
      // If it's CSV, set language to csv
      if (isCsv) {
        language = "csv";
      } else if (!language && codeBlock.classList.contains("language-text")) {
        language = "text";
      }
      
      // Skip if no language found
      if (!language) continue;
      
      // Only add pill badge if there's a filename
      if (filename) {
        // Create a container for right-side controls (toggle + pill)
        var rightControls = document.createElement("div");
        rightControls.className = "right-controls";
        
        // Create pill badge element
        var pill = document.createElement("span");
        pill.className = "language-pill";
        pill.textContent = language.toUpperCase();
        
        // Append pill to right controls
        rightControls.appendChild(pill);
        
        // Append right controls to filename
        filename.appendChild(rightControls);
      }
      
      // Handle CSV blocks - convert to table with toggle
      if (language === "csv") {
        // Create toggle button
        var toggleButton = document.createElement("button");
        toggleButton.className = "csv-toggle table-view"; // Start in table view
        toggleButton.title = "Toggle between table and raw CSV";
        
        // Add toggle button to right controls if filename exists, otherwise add before code block
        if (filename) {
          var rightControls = filename.querySelector(".right-controls");
          if (rightControls) {
            rightControls.insertBefore(toggleButton, rightControls.firstChild);
          }
        } else {
          // Add toggle button before the code block (it will be before the table too)
          codeBlock.parentNode.insertBefore(toggleButton, codeBlock);
        }
        
        convertCsvToTable(codeBlock, toggleButton);
      }
    }
  }

  function convertCsvToTable(codeBlock, toggleButton) {
    var codeElement = codeBlock.querySelector("code");
    if (!codeElement) return;
    
    // Get text content, handling nested spans properly
    var csvText = codeElement.textContent.trim();
    if (!csvText) return;
    
    // Parse CSV
    var lines = csvText.split("\n");
    if (lines.length === 0) return;
    
    var headers = parseCsvLine(lines[0]);
    var rows = [];
    for (var i = 1; i < lines.length; i++) {
      if (lines[i].trim()) {
        var row = parseCsvLine(lines[i]);
        rows.push(row);
      }
    }
    
    // Create table HTML
    var tableHtml = "<table class='csv-table'>";
    tableHtml += "<thead><tr>";
    for (var j = 0; j < headers.length; j++) {
      tableHtml += "<th>" + escapeHtml(headers[j]) + "</th>";
    }
    tableHtml += "</tr></thead><tbody>";
    for (var k = 0; k < rows.length; k++) {
      tableHtml += "<tr>";
      for (var l = 0; l < rows[k].length; l++) {
        tableHtml += "<td>" + escapeHtml(rows[k][l]) + "</td>";
      }
      tableHtml += "</tr>";
    }
    tableHtml += "</tbody></table>";
    
    // Hide the pre element (not the code element) to preserve copy button
    var preElement = codeBlock.querySelector("pre");
    if (preElement) {
      preElement.style.display = "none";
    }
    
    // Set up toggle button click handler
    toggleButton.onclick = function() {
      var table = codeBlock.querySelector(".csv-table");
      var preElement = codeBlock.querySelector("pre");
      
      if (!table) return; // Safety check
      
      if (table.style.display === "none") {
        // Show table, hide pre
        table.style.display = "";
        if (preElement) preElement.style.display = "none";
        toggleButton.classList.add("table-view");
      } else {
        // Hide table, show pre
        table.style.display = "none";
        if (preElement) preElement.style.display = "";
        toggleButton.classList.remove("table-view");
      }
    };
    
    // Create table container
    var tableContainer = document.createElement("div");
    tableContainer.className = "csv-table-container";
    tableContainer.innerHTML = tableHtml;
    tableContainer.style.display = ""; // Ensure table is visible initially
    
    // Insert table after the filename or before the code block
    var filename = codeBlock.querySelector(".filename");
    if (filename) {
      filename.parentNode.insertBefore(tableContainer, filename.nextSibling);
    } else {
      // Insert table before the code block itself
      codeBlock.parentNode.insertBefore(tableContainer, codeBlock);
    }
  }

  function parseCsvLine(line) {
    var result = [];
    var current = "";
    var inQuotes = false;
    
    for (var i = 0; i < line.length; i++) {
      var char = line[i];
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === "," && !inQuotes) {
        result.push(current.trim());
        current = "";
      } else {
        current += char;
      }
    }
    result.push(current.trim());
    return result;
  }

  function escapeHtml(text) {
    var div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  // Run after DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
