(function () {
  const navToggle = document.querySelector('[data-nav-toggle]');
  const mobileNavToggle = document.querySelector('[data-nav-toggle-mobile]');
  const navigation = document.getElementById('primary-navigation');
  function setNavigation(open) {
    if (!navigation) return;
    navigation.classList.toggle('is-open', open);
    document.body.classList.toggle('nav-open', open);
    if (navToggle) navToggle.setAttribute('aria-expanded', String(open));
  }
  function toggleNavigation() {
    setNavigation(navigation && !navigation.classList.contains('is-open'));
  }
  if (navToggle && navigation) navToggle.addEventListener('click', toggleNavigation);
  if (mobileNavToggle && navigation) mobileNavToggle.addEventListener('click', toggleNavigation);
  document.querySelectorAll('[data-nav-close]').forEach((el) => el.addEventListener('click', () => setNavigation(false)));
  if (navigation) navigation.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => setNavigation(false)));

  const tabs = Array.from(document.querySelectorAll('[data-tab-target]'));
  const panels = Array.from(document.querySelectorAll('[data-tab-panel]'));
  function activateTab(tab) {
    const target = tab.dataset.tabTarget;
    tabs.forEach((item) => { item.classList.toggle('is-active', item === tab); item.setAttribute('aria-selected', String(item === tab)); });
    panels.forEach((panel) => { const active = panel.dataset.tabPanel === target; panel.classList.toggle('is-active', active); panel.hidden = !active; });
  }
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => activateTab(tab));
    tab.addEventListener('keydown', (event) => {
      if (!['ArrowRight', 'ArrowLeft'].includes(event.key)) return;
      event.preventDefault();
      const nextIndex = event.key === 'ArrowLeft' ? (index + 1) % tabs.length : (index - 1 + tabs.length) % tabs.length;
      tabs[nextIndex].focus(); activateTab(tabs[nextIndex]);
    });
  });

  const hashTarget = window.location.hash.replace('#panel-', '');
  const hashTab = tabs.find((tab) => tab.dataset.tabTarget === hashTarget);
  if (hashTab) {
    activateTab(hashTab);
    requestAnimationFrame(() => hashTab.scrollIntoView({ block: 'start', behavior: 'smooth' }));
  }

  const memoryButtons = Array.from(document.querySelectorAll('[data-memory-filter]'));
  const memoryCards = Array.from(document.querySelectorAll('[data-memory-category]'));
  memoryButtons.forEach((button) => button.addEventListener('click', () => {
    const category = button.dataset.memoryFilter;
    memoryButtons.forEach((item) => item.classList.toggle('is-selected', item === button));
    memoryCards.forEach((card) => { card.hidden = category !== 'all' && card.dataset.memoryCategory !== category; });
  }));

  const filterForm = document.querySelector('[data-async-filter]');
  const resultRegion = document.getElementById('martyr-results');
  const filterStatus = document.getElementById('filter-status');
  let timer;
  async function refreshResults() {
    if (!filterForm || !resultRegion) return;
    const parameters = new URLSearchParams(new FormData(filterForm));
    const url = `${filterForm.action}?${parameters.toString()}`;
    resultRegion.setAttribute('aria-busy', 'true');
    resultRegion.classList.add('is-loading');
    if (filterStatus) filterStatus.textContent = 'در حال به‌روزرسانی نتایج…';
    try {
      const response = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      if (!response.ok) throw new Error('request failed');
      resultRegion.innerHTML = await response.text();
      window.history.replaceState({}, '', url);
      if (filterStatus) filterStatus.textContent = 'نتایج بدون بارگذاری مجدد به‌روزرسانی شد.';
    } catch (_) { filterForm.submit(); }
    finally { resultRegion.removeAttribute('aria-busy'); resultRegion.classList.remove('is-loading'); }
  }
  if (filterForm) {
    filterForm.addEventListener('submit', (event) => { event.preventDefault(); refreshResults(); });
    filterForm.querySelectorAll('select,input[type="date"]').forEach((field) => field.addEventListener('change', refreshResults));
    filterForm.querySelectorAll('input[type="text"]').forEach((field) => field.addEventListener('input', () => { window.clearTimeout(timer); timer = window.setTimeout(refreshResults, 380); }));
    const reset = document.querySelector('[data-filter-reset]');
    if (reset) reset.addEventListener('click', () => { filterForm.reset(); refreshResults(); });
  }

  const installCard = document.querySelector('[data-install-card]');
  const installButton = document.querySelector('[data-install-app]');
  const connectionStatus = document.querySelector('[data-pwa-status]');
  let deferredInstallPrompt;

  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    deferredInstallPrompt = event;
    if (installCard) installCard.hidden = false;
  });
  if (installButton) installButton.addEventListener('click', async () => {
    if (!deferredInstallPrompt) return;
    await deferredInstallPrompt.prompt();
    const choice = await deferredInstallPrompt.userChoice;
    if (choice.outcome === 'accepted' && installCard) installCard.hidden = true;
    deferredInstallPrompt = null;
  });
  window.addEventListener('appinstalled', () => {
    deferredInstallPrompt = null;
    if (installCard) installCard.hidden = true;
  });

  function updateNetworkStatus() {
    if (!connectionStatus) return;
    const online = navigator.onLine;
    document.documentElement.classList.toggle('is-offline', !online);
    connectionStatus.hidden = online;
    connectionStatus.textContent = online ? '' : 'اتصال اینترنت قطع است؛ نسخه ذخیره‌شده در دسترس است.';
  }
  window.addEventListener('online', updateNetworkStatus);
  window.addEventListener('offline', updateNetworkStatus);
  updateNetworkStatus();

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => navigator.serviceWorker.register('/service-worker.js', { scope: '/' }).catch(() => undefined));
  }
}());
