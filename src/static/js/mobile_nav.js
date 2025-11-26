    const btn = document.getElementById('menuBtn');
    const arrow = document.getElementById('menuArrow');
    const drawer = document.getElementById('mobileNav');
    const htmlEl = document.documentElement;
    const bodyEl = document.body;

    const open = () => {
      drawer.classList.remove('hidden');
      arrow.classList.add('rotate-90');
      btn.setAttribute('aria-expanded', 'true');
      htmlEl.classList.add('overflow-hidden');
      bodyEl.classList.add('overflow-hidden', 'touch-none');
      drawer.removeAttribute('aria-hidden');
    };

    const close = () => {
      drawer.classList.add('hidden');
      arrow.classList.remove('rotate-90');
      btn.setAttribute('aria-expanded', 'false');
      htmlEl.classList.remove('overflow-hidden');
      bodyEl.classList.remove('overflow-hidden', 'touch-none');
      drawer.setAttribute('aria-hidden', 'true');
    };

    btn?.addEventListener('click', () => {
      if (drawer.classList.contains('hidden')) open();
      else close();
    });

    drawer?.addEventListener('click', (e) => {
      if (e.target === drawer) close();
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !drawer.classList.contains('hidden')) close();
    });