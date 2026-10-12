(function () {
  function copyButtons() {
    document.querySelectorAll('pre').forEach(function (pre) {
      if (pre.querySelector('.copy')) return;
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'copy';
      btn.textContent = 'Copy';
      btn.addEventListener('click', function () {
        var code = pre.querySelector('code');
        var text = code ? code.textContent : pre.textContent;
        navigator.clipboard.writeText(text).then(function () {
          btn.textContent = 'Copied';
          setTimeout(function () { btn.textContent = 'Copy'; }, 1500);
        });
      });
      pre.appendChild(btn);
    });
  }

  function filterSearch(input) {
    var q = input.value.trim().toLowerCase();
    var root = input.getAttribute('data-search-target') === 'main'
      ? document.querySelector('main')
      : document.querySelector(input.getAttribute('data-search-target') || '.grid');
    if (!root) return;
    root.querySelectorAll('[data-search-item]').forEach(function (el) {
      var hay = (el.getAttribute('data-search') || el.textContent || '').toLowerCase();
      el.classList.toggle('hidden', q && !hay.includes(q));
    });
  }

  document.querySelectorAll('input[type=search][data-search-target]').forEach(function (input) {
    input.addEventListener('input', function () { filterSearch(input); });
  });

  if (window.SITE_SEARCH && document.querySelector('input[data-global-search]')) {
    var g = document.querySelector('input[data-global-search]');
    g.addEventListener('input', function () {
      var q = g.value.trim().toLowerCase();
      window.SITE_SEARCH.forEach(function (item) {
        var el = document.querySelector('[data-search-item][id^="pkg-"],[data-search-item][id^="skill-"]');
      });
    });
  }

  copyButtons();
})();
