/**
 * Dynamic language pill badges for code blocks.
 *
 * Automatically adds language type badges to all code blocks
 * by extracting the language class from the code block element.
 */
(function () {
  "use strict";

  function init() {
    // Find all code blocks with filename titles
    var codeBlocks = document.querySelectorAll(".md-typeset .highlight");
    
    for (var i = 0; i < codeBlocks.length; i++) {
      var codeBlock = codeBlocks[i];
      var filename = codeBlock.querySelector(".filename");
      
      // Skip if no filename
      if (!filename) continue;
      
      // Extract language from class names
      var language = null;
      for (var j = 0; j < codeBlock.classList.length; j++) {
        var className = codeBlock.classList[j];
        if (className.startsWith("language-")) {
          language = className.replace("language-", "");
          break;
        }
      }
      
      // Skip if no language found
      if (!language) continue;
      
      // Create pill badge element
      var pill = document.createElement("span");
      pill.className = "language-pill";
      pill.textContent = language.toUpperCase();
      
      // Append to filename
      filename.appendChild(pill);
    }
  }

  // Run after DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
