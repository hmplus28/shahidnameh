(function () {
  function previewTarget(input) {
    const inlineRow = input.closest('tr');
    if (inlineRow) return inlineRow.querySelector('.js-image-preview');
    return document.getElementById('image-live-preview') || input.closest('.form-row')?.parentElement?.querySelector('.js-image-preview');
  }

  function showPreview(input) {
    const preview = previewTarget(input);
    const file = input.files && input.files[0];
    if (!preview || !file || !file.type.startsWith('image/')) return;
    const nextUrl = URL.createObjectURL(file);
    if (preview.dataset.previewUrl) URL.revokeObjectURL(preview.dataset.previewUrl);
    const image = preview.tagName === 'IMG' ? preview : document.createElement('img');
    image.className = 'js-image-preview admin-image-preview';
    image.src = nextUrl;
    image.alt = 'پیش‌نمایش تصویر انتخاب‌شده';
    image.dataset.previewUrl = nextUrl;
    if (preview !== image) preview.replaceWith(image);
  }

  function bindPreview(input) {
    if (input.dataset.previewBound) return;
    input.dataset.previewBound = 'true';
    input.addEventListener('change', () => showPreview(input));
  }

  function bindAll() {
    document.querySelectorAll('input[type="file"][name="image"], input[type="file"][name$="-image"]').forEach(bindPreview);
  }

  document.addEventListener('DOMContentLoaded', bindAll);
  document.addEventListener('formset:added', bindAll);
  if (window.django && window.django.jQuery) window.django.jQuery(document).on('formset:added', bindAll);
}());
