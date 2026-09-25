// Four behaviours: actor select auto-submit, confirm() on destructive forms, dirty-textarea warning, bulk assertions.
(function () {
  document.querySelectorAll("select[data-autosubmit]").forEach(function (sel) {
    sel.addEventListener("change", function () { sel.form.submit(); });
  });

  // Bulk clinician assertions: select several, set value once, Record selected submits all.
  (function () {
    var form = document.getElementById("bulk-assert-form");
    if (!form) return;
    var selectAll = document.getElementById("bulk-select-all");
    var checks = form.querySelectorAll(".assert-select");
    var submit = document.getElementById("bulk-submit");
    var msg = document.getElementById("bulk-msg");
    var bulkBtns = document.querySelectorAll("[data-bulk-value]");

    function update() {
      var n = form.querySelectorAll(".assert-rows .assert-select:checked").length;
      if (submit) {
        submit.disabled = n === 0;
        submit.textContent = n ? "Record selected (" + n + ")" : "Record selected";
      }
      if (selectAll) {
        selectAll.checked = n === checks.length && n > 0;
        selectAll.indeterminate = n > 0 && n < checks.length;
      }
      checks.forEach(function (ch) {
        var row = ch.closest(".assert-row");
        if (!row) return;
        row.classList.toggle("is-selected", ch.checked);
        // A row flagged by a failed submit clears once it has a value or is deselected.
        if (!ch.checked || row.querySelector('input[type="radio"]:checked')) row.classList.remove("is-missing");
      });
      if (msg && !form.querySelector(".assert-row.is-missing")) msg.textContent = "";
    }

    if (selectAll) {
      selectAll.addEventListener("change", function () {
        checks.forEach(function (ch) { if (!ch.disabled) ch.checked = selectAll.checked; });
        update();
      });
    }
    checks.forEach(function (ch) {
      ch.addEventListener("change", update);
      // Auto-check row when its radio or note is interacted with
      var row = ch.closest(".assert-row");
      if (row) {
        row.querySelectorAll('input[type="radio"], .assert-note').forEach(function (el) {
          el.addEventListener("change", function () { if (!ch.checked && !ch.disabled) ch.checked = true; update(); });
          el.addEventListener("input", function () { if (!ch.checked && !ch.disabled && el.value) { ch.checked = true; update(); } });
        });
      }
    });
    bulkBtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var val = btn.getAttribute("data-bulk-value");
        form.querySelectorAll(".assert-select:checked").forEach(function (ch) {
          var row = ch.closest(".assert-row");
          if (!row) return;
          var radio = row.querySelector('input[type="radio"][value="' + val + '"]');
          if (radio && !radio.disabled) radio.checked = true;
        });
        update();
      });
    });
    // Validate on submit: every selected row needs a value. Say so in place instead of a browser alert.
    form.addEventListener("submit", function (e) {
      var missing = 0;
      form.querySelectorAll(".assert-rows .assert-select").forEach(function (ch) {
        var row = ch.closest(".assert-row");
        var gap = ch.checked && !row.querySelector('input[name="value_' + ch.value + '"]:checked');
        row.classList.toggle("is-missing", gap);
        if (gap) missing++;
      });
      if (msg) msg.textContent = missing ? "Choose Met, Not met or N/A for " + missing + (missing === 1 ? " selected row." : " selected rows.") : "";
      if (missing) e.preventDefault();
    });
    update();
  })();

  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!window.confirm(form.getAttribute("data-confirm"))) e.preventDefault();
    });
  });

  var ta = document.querySelector("textarea[data-dirty-warn]");
  if (ta) {
    var initial = ta.value, dirty = false;
    ta.addEventListener("input", function () {
      dirty = ta.value !== initial;
      // Sign-off signs the narrative as currently shown; keep the hidden copy in step.
      var mirror = document.getElementById("signoff-narrative");
      if (mirror) mirror.value = ta.value;
    });
    var narrativeForm = document.getElementById("narrative-form");
    if (narrativeForm) narrativeForm.addEventListener("submit", function () { dirty = false; });
    var signoff = document.getElementById("signoff-form");
    if (signoff) signoff.addEventListener("submit", function () { dirty = false; });
    window.addEventListener("beforeunload", function (e) {
      if (dirty) { e.preventDefault(); e.returnValue = ""; }
    });
  }
})();

// Links into a closed <details> (e.g. "#assertions", "#req-radiograph_pa") open the fold they land in.
(function () {
  function reveal() {
    if (!location.hash) return;
    var el = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (!el) return;
    var d = el.closest("details");
    while (d) { d.open = true; d = d.parentElement && d.parentElement.closest("details"); }
    el.scrollIntoView({ block: "start" });
  }
  window.addEventListener("hashchange", reveal);
  reveal();
})();
