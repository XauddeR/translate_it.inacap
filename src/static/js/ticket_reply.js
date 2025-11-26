(function () {
    const form = document.getElementById('replyForm');
    const btn = document.getElementById('replyBtn');
    const btnText = document.getElementById('replyBtnText');
    if (!form || !btn || !btnText) return;
    form.addEventListener('submit', () => {
      btn.disabled = true;
      btnText.textContent = 'Enviando…';
    });
})();