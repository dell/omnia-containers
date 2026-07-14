/**
 * Flowchart interactivity for Get Started page
 */
(function () {
  "use strict";

  function setState(el, solid) {
    el.classList.toggle('state-solid', solid);
    el.classList.toggle('state-dotted', !solid);
  }

  function selectPath(choice) {
    document.getElementById('btn-manual').classList.toggle('active', choice === 'manual');
    document.getElementById('btn-buildstream').classList.toggle('active', choice === 'buildstream');
    document.getElementById('branch-manual').classList.toggle('open', choice === 'manual');
    document.getElementById('branch-buildstream').classList.toggle('open', choice === 'buildstream');
    setState(document.getElementById('stem-manual'), choice === 'manual');
    setState(document.getElementById('stem-buildstream'), choice === 'buildstream');
    setState(document.getElementById('half-manual'), choice === 'manual');
    setState(document.getElementById('half-buildstream'), choice === 'buildstream');
    setState(document.getElementById('final-connector'), true);
    document.getElementById('placeholder').style.display = 'none';
  }

  // Run after DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      window.selectPath = selectPath;
    });
  } else {
    window.selectPath = selectPath;
  }
})();
