/**
 * Palette toggle fallback for file:// browsing.
 *
 * MkDocs Material's bundle.js normally initialises the palette component,
 * but it can fail when the site is opened via file:// (e.g. from a zip).
 * This lightweight fallback detects that situation and wires up the
 * dark / light toggle manually.
 */
(function () {
  "use strict";

  function init() {
    var labels = document.querySelectorAll("label[for^='__palette']");
    if (!labels.length) return;            // no palette configured

    /* If the bundle already unhid a label, it handled initialisation → bail */
    for (var i = 0; i < labels.length; i++) {
      if (!labels[i].hidden) return;
    }

    /* ── The bundle didn't initialise — set up our own handler ── */
    var inputs = document.querySelectorAll("input[name='__palette']");

    function applyScheme() {
      for (var j = 0; j < inputs.length; j++) {
        if (inputs[j].checked) {
          document.body.setAttribute(
            "data-md-color-scheme",
            inputs[j].getAttribute("data-md-color-scheme")
          );
          document.body.setAttribute(
            "data-md-color-primary",
            inputs[j].getAttribute("data-md-color-primary")
          );
          document.body.setAttribute(
            "data-md-color-accent",
            inputs[j].getAttribute("data-md-color-accent")
          );
        }
      }
    }

    for (var k = 0; k < inputs.length; k++) {
      inputs[k].addEventListener("change", applyScheme);
    }

    applyScheme();                         // set initial state
  }

  /* Run after the bundle has had a chance to load */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      setTimeout(init, 100);
    });
  } else {
    setTimeout(init, 100);
  }
})();
