(function () {
  "use strict";

  var form = document.querySelector("form[data-autosave]");
  if (!form || !window.localStorage) return;

  var keyAttr = form.getAttribute("data-autosave") || "martyr";
  var storageKey = "shahidnameh:draft:" + keyAttr;
  var submitFlagKey = "shahidnameh:draft:__submitted";
  var statusEl = document.querySelector("[data-autosave-status]");

  var pendingClear = localStorage.getItem(submitFlagKey);
  if (pendingClear) {
    localStorage.removeItem(pendingClear);
    localStorage.removeItem(submitFlagKey);
  }

  function savableFields() {
    return Array.prototype.filter.call(form.elements, function (el) {
      if (!el.name) return false;
      if (el.type === "file" || el.type === "hidden" || el.disabled) return false;
      var tag = el.tagName.toLowerCase();
      return tag === "input" || tag === "select" || tag === "textarea";
    });
  }

  function serialize() {
    var data = {};
    savableFields().forEach(function (el) {
      if (el.type === "checkbox") {
        data[el.name] = el.checked;
      } else {
        data[el.name] = el.value;
      }
    });
    data.__savedAt = new Date().toISOString();
    return data;
  }

  function restore(data) {
    savableFields().forEach(function (el) {
      if (!(el.name in data)) return;
      if (el.type === "checkbox") {
        el.checked = !!data[el.name];
      } else if (el.value !== data[el.name]) {
        el.value = data[el.name];
        el.dispatchEvent(new Event("change", { bubbles: true }));
      }
    });
  }

  function showStatus(text, isError) {
    if (!statusEl) return;
    statusEl.textContent = text;
    statusEl.classList.toggle("is-error", Boolean(isError));
    statusEl.hidden = false;
  }

  var timer = null;
  function scheduleSave() {
    if (timer) clearTimeout(timer);
    timer = setTimeout(function () {
      try {
        localStorage.setItem(storageKey, JSON.stringify(serialize()));
        showStatus("\u2713 \u067e\u06cc\u0634\u2006\u0646\u0648\u06cc\u0633 \u062f\u0631 \u0645\u0631\u0648\u0631\u06af\u0631 \u0630\u062e\u06cc\u0631\u0647 \u0634\u062f", false);
      } catch (err) {
        showStatus("\u0630\u062e\u06cc\u0631\u0647 \u067e\u06cc\u0634\u2006\u0646\u0648\u06cc\u0633 \u0645\u0645\u06a9\u0646 \u0646\u0634\u062f", true);
      }
    }, 700);
  }

  form.addEventListener("input", scheduleSave);
  form.addEventListener("change", scheduleSave);

  function saveNow() {
    if (timer) clearTimeout(timer);
    try {
      localStorage.setItem(storageKey, JSON.stringify(serialize()));
    } catch (err) { /* storage full or unavailable */ }
  }

  window.addEventListener("pagehide", saveNow);
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") saveNow();
  });

  form.addEventListener("submit", function () {
    localStorage.setItem(submitFlagKey, storageKey);
  });

  window.addEventListener("offline", function () {
    showStatus("\u0627\u062a\u0635\u0627\u0644 \u0642\u0637\u0639 \u0634\u062f\u0647 \u2014 \u0627\u0637\u0644\u0627\u0639\u0627\u062a \u062f\u0631 \u0645\u0631\u0648\u0631\u06af\u0631 \u0646\u06af\u0647 \u062f\u0627\u0631\u06cc \u0645\u06cc\u200c\u0634\u0648\u062f", true);
  });
  window.addEventListener("online", function () {
    showStatus("\u0627\u062a\u0635\u0627\u0644 \u0628\u0631\u0642\u0631\u0627\u0631 \u0634\u062f\u061b \u0645\u06cc\u200c\u062a\u0648\u0627\u0646\u06cc\u062f \u0630\u062e\u06cc\u0631\u0647 \u06a9\u0646\u06cc\u062f", false);
  });

  var raw = localStorage.getItem(storageKey);
  if (!raw) return;

  var data;
  try {
    data = JSON.parse(raw);
  } catch (err) {
    localStorage.removeItem(storageKey);
    return;
  }

  var savedAt = data.__savedAt ? new Date(data.__savedAt) : null;
  delete data.__savedAt;

  var hasContent = Object.keys(data).some(function (name) {
    var value = data[name];
    if (typeof value === "boolean") return value;
    return String(value || "").trim().length > 0;
  });

  if (!hasContent) {
    localStorage.removeItem(storageKey);
    return;
  }

  restore(data);
  showStatus(
    "\u067e\u06cc\u0634\u2006\u0646\u0648\u06cc\u0633 \u0630\u062e\u06cc\u0631\u0647\u200c\u0634\u062f\u0647" +
    (savedAt ? " (" + savedAt.toLocaleString("fa-IR") + ") " : " ") +
    "\u0628\u0627\u0632\u06cc\u0627\u0628\u06cc \u0634\u062f",
    false
  );
})();
