// Small behaviours on top of server-rendered forms: actor switch, confirm on destructive forms,
// unsaved-narrative warning, "Set unanswered to Met", and links that land inside a closed fold.
(function () {
  document.querySelectorAll("select[data-autosubmit]").forEach(function (sel) {
    sel.addEventListener("change", function () { sel.form.submit(); });
  });

  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!window.confirm(form.getAttribute("data-confirm"))) e.preventDefault();
    });
  });

  // The dentist still reviews and presses Record answers; this only fills the rows they left blank, and
  // never a row where Ophi has a chart note for them to weigh (data-needs-look).
  document.querySelectorAll("[data-all-met]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      btn.closest("form").querySelectorAll(".crit:not([data-needs-look])").forEach(function (row) {
        if (row.querySelector('input[type="radio"]:checked')) return;
        var met = row.querySelector('input[type="radio"][value="met"]');
        if (met) met.checked = true;
      });
    });
  });

  // Answers the dentist tapped but didn't record are lost on leaving; say so first.
  var crit = document.getElementById("crit-form");
  if (crit) {
    var changed = false;
    crit.addEventListener("change", function () { changed = true; });
    crit.addEventListener("submit", function () { changed = false; });
    window.addEventListener("beforeunload", function (e) {
      if (changed) { e.preventDefault(); e.returnValue = ""; }
    });
  }

  document.querySelectorAll("[data-print]").forEach(function (btn) {
    btn.addEventListener("click", function () { window.print(); });
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
    ["narrative-form", "signoff-form"].forEach(function (id) {
      var f = document.getElementById(id);
      if (f) f.addEventListener("submit", function () { dirty = false; });
    });
    window.addEventListener("beforeunload", function (e) {
      if (dirty) { e.preventDefault(); e.returnValue = ""; }
    });
  }
})();

// Links into a closed <details> (e.g. "#req-radiograph_pa") open the fold they land in.
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
