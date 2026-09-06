(function () {
  /* More Sheet */
  const moreToggle = document.querySelector('[data-more-toggle]');
  const moreSheet = document.querySelector('[data-more-sheet]');
  function openMore() { if (moreSheet) { moreSheet.hidden = false; document.body.style.overflow = 'hidden'; } }
  function closeMore() { if (moreSheet) { moreSheet.hidden = true; document.body.style.overflow = ''; } }
  if (moreToggle) moreToggle.addEventListener('click', openMore);
  document.querySelectorAll('[data-more-close]').forEach((el) => el.addEventListener('click', closeMore));

  /* Toggle Slider Expand/Collapse */
  document.querySelectorAll('[data-toggle-slider]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const sliderId = btn.dataset.toggleSlider;
      const slider = document.querySelector(`[data-slider-id="${sliderId}"]`);
      if (!slider) return;
      const isExpanded = slider.classList.toggle('is-expanded');
      btn.textContent = isExpanded ? 'بستن ←' : 'مشاهده همه ←';
    });
  });

  /* Search Popup */
  const searchToggle = document.querySelector('[data-search-toggle]');
  const searchPopup = document.querySelector('[data-search-popup]');
  function openSearch() { if (searchPopup) { searchPopup.hidden = false; document.body.style.overflow = 'hidden'; } }
  function closeSearch() { if (searchPopup) { searchPopup.hidden = true; document.body.style.overflow = ''; } }
  if (searchToggle) searchToggle.addEventListener('click', openSearch);
  document.querySelectorAll('[data-search-close]').forEach((el) => el.addEventListener('click', closeSearch));

  /* Tabs */
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

  /* Memory Filter */
  const memoryButtons = Array.from(document.querySelectorAll('[data-memory-filter]'));
  const memoryCards = Array.from(document.querySelectorAll('[data-memory-category]'));
  memoryButtons.forEach((button) => button.addEventListener('click', () => {
    const category = button.dataset.memoryFilter;
    memoryButtons.forEach((item) => item.classList.toggle('is-selected', item === button));
    memoryCards.forEach((card) => { card.hidden = category !== 'all' && card.dataset.memoryCategory !== category; });
  }));

  /* Async Filter */
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
    try {
      const response = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      if (!response.ok) throw new Error('request failed');
      resultRegion.innerHTML = await response.text();
      window.history.replaceState({}, '', url);
    } catch (_) { filterForm.submit(); }
    finally { resultRegion.removeAttribute('aria-busy'); resultRegion.classList.remove('is-loading'); }
  }
  if (filterForm) {
    filterForm.addEventListener('submit', (event) => { event.preventDefault(); refreshResults(); });
    filterForm.querySelectorAll('select').forEach((field) => field.addEventListener('change', refreshResults));
    filterForm.querySelectorAll('input[type="text"]').forEach((field) => field.addEventListener('input', () => { window.clearTimeout(timer); timer = window.setTimeout(refreshResults, 380); }));
  }

  /* PWA Install */
  const installCard = document.querySelector('[data-install-card]');
  const sheetInstallBtns = document.querySelectorAll('[data-install-app]');
  const connectionStatus = document.querySelector('[data-pwa-status]');
  let deferredInstallPrompt;

  // Check if PWA is already installed
  const isPWAInstalled = localStorage.getItem('pwaInstalled') === 'true';
  
  // Check if popup was shown today
  function shouldShowInstallPopup() {
    const lastShown = localStorage.getItem('pwaPopupLastShown');
    if (!lastShown) return true;
    
    const lastDate = new Date(lastShown);
    const today = new Date();
    const diffTime = Math.abs(today - lastDate);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    return diffDays >= 1;
  }

  // Function to show install popup
  function showInstallPopup() {
    if (installCard && !isPWAInstalled && shouldShowInstallPopup()) {
      installCard.hidden = false;
      localStorage.setItem('pwaPopupLastShown', new Date().toISOString());
    }
  }

  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    deferredInstallPrompt = event;
    sheetInstallBtns.forEach((btn) => { btn.style.display = ''; });
    showInstallPopup();
  });

  function handleInstallClick() {
    if (deferredInstallPrompt) {
      const prompt = deferredInstallPrompt;
      prompt.prompt().then(() => prompt.userChoice).then((choice) => {
        if (choice && choice.outcome === 'accepted') {
          localStorage.setItem('pwaInstalled', 'true');
          if (installCard) installCard.hidden = true;
          sheetInstallBtns.forEach((btn) => { btn.style.display = 'none'; });
        }
        deferredInstallPrompt = null;
      });
    } else {
      if (installCard) installCard.hidden = true;
    }
  }
  sheetInstallBtns.forEach((btn) => btn.addEventListener('click', handleInstallClick));

  const installCloseBtns = document.querySelectorAll('[data-install-close]');
  installCloseBtns.forEach((btn) => btn.addEventListener('click', () => {
    if (installCard) installCard.hidden = true;
  }));
  
  window.addEventListener('appinstalled', () => {
    localStorage.setItem('pwaInstalled', 'true');
    deferredInstallPrompt = null;
    if (installCard) installCard.hidden = true;
    sheetInstallBtns.forEach((btn) => { btn.style.display = 'none'; });
  });

  // Hide install UI if already installed
  if (isPWAInstalled) {
    if (installCard) installCard.hidden = true;
    sheetInstallBtns.forEach((btn) => { btn.style.display = 'none'; });
  }

  /* Network Status */
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

  /* Background Music */
  const musicControl = document.querySelector('[data-bg-music]');
  const musicToggle = document.querySelector('[data-music-toggle]');
  const bgMusic = document.getElementById('bg-music');
  const playIcon = musicToggle ? musicToggle.querySelector('.play-icon') : null;
  const stopIcon = musicToggle ? musicToggle.querySelector('.stop-icon') : null;
  let musicPlaying = sessionStorage.getItem('musicPlaying') === 'true';

  function updateMusicState() {
    if (!musicToggle || !bgMusic) return;
    musicToggle.classList.toggle('is-playing', musicPlaying);
    if (playIcon) playIcon.style.display = musicPlaying ? 'none' : 'block';
    if (stopIcon) stopIcon.style.display = musicPlaying ? 'block' : 'none';
    sessionStorage.setItem('musicPlaying', musicPlaying);
    if (musicPlaying) {
      bgMusic.play().catch(() => { musicPlaying = false; updateMusicState(); });
    } else {
      bgMusic.pause();
    }
  }

  if (musicToggle && bgMusic) {
    if (musicControl) musicControl.hidden = false;
    musicToggle.addEventListener('click', () => {
      musicPlaying = !musicPlaying;
      updateMusicState();
    });
    if (musicPlaying) updateMusicState();
  }

  /* Ziyaratnama Fullscreen */
  const fullscreenToggle = document.querySelector('[data-fullscreen-toggle]');
  if (fullscreenToggle) {
    fullscreenToggle.addEventListener('click', () => {
      const videoContainer = document.querySelector('.ziyaratnama-video');
      if (!videoContainer) return;
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        videoContainer.requestFullscreen().catch(() => {});
      }
    });
  }

  /* Service Worker */
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => navigator.serviceWorker.register('/service-worker.js', { scope: '/' }).catch(() => undefined));
  }
}());
