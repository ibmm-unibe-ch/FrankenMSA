// Prompt user before leaving while Dash is performing callbacks (computations/loading).
// Watches the `data-dash-is-loading` attribute on <body> which Dash sets when callbacks are in-flight.
(function () {
  'use strict';

  let appLoading = false;

  function updateLoadingState() {
    try {
      const v = document.body.getAttribute('data-dash-is-loading');
      appLoading = v === 'true' || v === 'True';
    } catch (err) {
      appLoading = false;
    }
  }

  // Observe attribute changes on <body>
  const observer = new MutationObserver(function (mutations) {
    for (const m of mutations) {
      if (m.type === 'attributes' && m.attributeName === 'data-dash-is-loading') {
        updateLoadingState();
      }
    }
  });

  if (document && document.body) {
    updateLoadingState();
    observer.observe(document.body, { attributes: true });
  } else {
    // If body not yet present, wait for DOMContentLoaded
    document.addEventListener('DOMContentLoaded', function () {
      updateLoadingState();
      observer.observe(document.body, { attributes: true });
    });
  }

  // Native browser unload prompt
  window.addEventListener('beforeunload', function (e) {
    if (appLoading) {
      const msg = 'A computation is still running — leaving will abort it. Are you sure you want to leave?';
      e.preventDefault();
      // Most browsers ignore the custom message, but setting returnValue is required.
      e.returnValue = msg;
      return msg;
    }
    return undefined;
  });

  // Also intercept same-tab link clicks and navigation attempts
  document.addEventListener('click', function (ev) {
    if (!appLoading) return;
    const a = ev.target.closest && ev.target.closest('a');
    if (!a) return;
    // Only intercept same-origin, same-tab navigations
    try {
      if (a.target && a.target !== '' && a.target !== '_self') return;
      const href = a.getAttribute('href');
      if (!href || href.startsWith('#') || href.startsWith('javascript:')) return;
      // Ask for confirmation
      const ok = window.confirm('A computation is still running — leaving will abort it. Continue?');
      if (!ok) ev.preventDefault();
    } catch (err) {
      // ignore
    }
  }, true);

})();
