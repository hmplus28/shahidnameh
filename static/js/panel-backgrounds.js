/* پیش‌نمایش زنده شفافیت تصاویر پس‌زمینه در پنل مدیریت شهیدنامه */
(function () {
  "use strict";

  function toFa(num) {
    var digits = "\u06F0\u06F1\u06F2\u06F3\u06F4\u06F5\u06F6\u06F7\u06F8\u06F9";
    return String(num).replace(/\d/g, function (d) { return digits[+d]; });
  }

  document.querySelectorAll("[data-bg-card]").forEach(function (card) {
    var slider = card.querySelector("input[type=range][data-bg-slider]");
    var layer = card.querySelector("[data-bg-layer]");
    var valueEls = card.querySelectorAll("[data-bg-value]");
    var fileInput = card.querySelector('input[type=file]');
    if (!slider) return;

    // بروزرسانی زنده پیش‌نمایش با حرکت اسلایدر شفافیت
    slider.addEventListener("input", function () {
      var percent = Number(slider.value || 0);
      var ratio = (percent / 100).toFixed(2);
      valueEls.forEach(function (el) { el.textContent = toFa(percent) + "\u066A"; });
      if (layer) layer.style.opacity = ratio;
    });

    // نمایش زنده تصویر انتخاب‌شده (پیش از آپلود) در پیش‌نمایش
    if (fileInput && layer) {
      fileInput.addEventListener("change", function () {
        var file = fileInput.files && fileInput.files[0];
        if (file && window.URL && URL.createObjectURL) {
          layer.style.backgroundImage = 'url("' + URL.createObjectURL(file) + '")';
        }
      });
    }
  });

  // تایید پیش از بازگشت به پیش‌فرض
  document.querySelectorAll("[data-bg-reset]").forEach(function (btn) {
    btn.addEventListener("click", function (event) {
      if (!window.confirm("\u0627\u06CC\u0646 \u067E\u0633\u200C\u0632\u0645\u06CC\u0646\u0647 \u0628\u0647 \u062A\u0635\u0648\u06CC\u0631 \u0648 \u0634\u0641\u0627\u0641\u06CC\u062A \u067E\u06CC\u0634\u200C\u0641\u0631\u0636 \u0628\u0627\u0632\u06AF\u0631\u062F\u062F\u061F")) {
        event.preventDefault();
      }
    });
  });
})();
