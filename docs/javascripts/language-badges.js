/**
 * Dynamic language pill badges for code blocks.
 *
 * - Automatically adds language type badges to all code blocks
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
      
      // If no language from class, default to text
      if (!language && codeBlock.classList.contains("language-text")) {
        language = "text";
      }
      
      // Skip if no language found
      if (!language) continue;
      
      // Only add pill badge if there's a filename
      if (filename) {
        // Create a container for right-side controls
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
    }
  }

  // Run after DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
