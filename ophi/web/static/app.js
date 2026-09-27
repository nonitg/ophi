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

  // The confirmation after a write is a toast: it says what happened, then gets out of the way.
  var note = document.querySelector(".done-note");
  if (note) setTimeout(function () { note.classList.add("is-gone"); }, 4000);

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
  // Dev aid: the case page's Laya + LightGBM output, printed to the browser console.
  var ml = document.getElementById("ml-debug");
  if (ml) {
    var m = JSON.parse(ml.textContent);
    console.group("Ophi ML — " + m.case_id + " (scored " + (m.scored_on || "never") + ")");
    console.log(m.shown ? "Page shows plan: " + m.shown
      : m.plans.length ? "Chart changed since scoring: no plan matches, page shows the engine's gaps"
      : "No plan for this case; run scripts/laya-demo-predict.py");
    console.log("Laya input:\n" + m.laya_input);
    m.plans.forEach(function (p) {
      console.group("Plan " + p.state + (p.matches_chart ? " (shown)" : ""));
      console.log("Models:", p.model);
      console.log("LightGBM P(denied): now " + p.now.score + " (" + p.now.level + ") -> after fixes "
        + p.after_fixes.score + " (" + p.after_fixes.level + (p.after_fixes.because ? ", " + p.after_fixes.because : "") + ")");
      console.log("Remaining: " + p.remaining);
      console.log("Laya P(yes) per note question:");
      console.table(p.note_answers);
      console.log("LightGBM drivers (push on log-odds of denial):");
      console.table(p.drivers.map(function (d) { return { feature: d.feature, push: d.push, label: d.label }; }));
      console.log("Fixes in plan order (risk_drop = P(denied) removed alone):");
      console.table(p.fixes.map(function (f) { return { kind: f.kind, who: f.who, risk_drop: f.risk_drop, concern: f.concern, title: f.title }; }));
      console.groupEnd();
    });
    console.log("Raw:", m);
    console.groupEnd();
  }
})();
