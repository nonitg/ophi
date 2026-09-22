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
    var countEl = document.getElementById("bulk-count");
    var submit = document.getElementById("bulk-submit");
    var bulkBtns = document.querySelectorAll("[data-bulk-value]");

    function update() {
      var n = form.querySelectorAll(".assert-select:checked").length;
      if (countEl) countEl.textContent = n + " selected";
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
        if (row) row.classList.toggle("is-selected", ch.checked);
      });
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
          el.addEventListener("change", function () { if (!ch.checked && !ch.disabled) { ch.checked = true; update(); } });
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
      });
    });
    // Validate on submit: require a value for each selected row
    form.addEventListener("submit", function (e) {
      var selected = form.querySelectorAll(".assert-select:checked");
      if (selected.length === 0) { e.preventDefault(); alert("Select at least one criterion."); return; }
      var missing = [];
      selected.forEach(function (ch) {
        var row = ch.closest(".assert-row");
        var cid = ch.value;
        var has = row && row.querySelector('input[name="value_' + cid + '"]:checked');
        if (!has) missing.push(cid);
      });
      if (missing.length) {
        e.preventDefault();
        alert("Choose Met / Not met / N/A for each selected row.");
      }
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
