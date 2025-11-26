const editModal = document.getElementById('editModal');
const editForm  = document.getElementById('editForm');

function openEditModal(id, filename) {
    editModal.classList.remove('hidden');
    editModal.classList.add('flex');
    document.getElementById('editFilename').value = filename;
    editForm.action = `/update_file/${id}`;
}

function closeEditModal() {
    editModal.classList.add('hidden');
    editModal.classList.remove('flex');
}

editModal?.addEventListener('click', (e) => {
    if (e.target === editModal) closeEditModal();
});

const confirmModal = document.getElementById('confirmDeleteModal');
const confirmOverlay = document.getElementById('confirmOverlay');
const cancelDelBtn   = document.getElementById('cancelDeleteBtn');
const delForm        = document.getElementById('deleteFileForm');

function openConfirm(url) {
    delForm.action = url;
    confirmModal.classList.remove('hidden');
    confirmModal.classList.add('flex');
}

function closeConfirm() {
    confirmModal.classList.add('hidden');
    confirmModal.classList.remove('flex');
    delForm.action = '';
}

document.addEventListener('click', (e) => {
    const btn = e.target.closest('.btn-delete-file');
    if (!btn) return;
    e.preventDefault();
    openConfirm(btn.dataset.url);
});

cancelDelBtn?.addEventListener('click', closeConfirm);
confirmOverlay?.addEventListener('click', closeConfirm);

delForm?.addEventListener('submit', () => {
    const btn = delForm.querySelector('button[type="submit"]');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Eliminando…';
    }
});

document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (editModal && !editModal.classList.contains('hidden'))  closeEditModal();
    if (confirmModal && !confirmModal.classList.contains('hidden')) closeConfirm();
});

function startPollingForFile(id) {
    const bar = document.querySelector(`[data-progress-bar="${id}"]`);
    const label = document.querySelector(`[data-progress-label="${id}"]`);
    const card = document.querySelector(`[data-card="${id}"]`);

    if (!bar || !card) return;

    const interval = setInterval(() => {
      fetch(`/api/file_status/${id}`)
        .then(r => r.ok ? r.json() : null)
        .then(data => {
          if (!data || data.error) {
            clearInterval(interval);
            return;
          }

          const pct = data.progreso ?? 0;
          const estado  = data.estado;

          bar.style.width = pct + '%';

          if (label) {
            if (estado === 'completado') {
              label.textContent = 'Completado';
              label.classList.remove('text-rose-300');
            } else if (estado === 'error') {
              label.textContent = 'Error';
              label.classList.add('text-rose-400');
            } else {
              label.textContent = `${Math.round(pct)}%`;
              label.classList.remove('text-rose-400');
            }
          }

          if (estado === 'completado' || estado === 'error') {
            clearInterval(interval);

            setTimeout(() => {
              fetch(window.location.href)
                .then(r => r.text())
                .then(html => {
                  const parser = new DOMParser();
                  const doc    = parser.parseFromString(html, 'text/html');

                  const newCard = doc.querySelector(`[data-card="${id}"]`);
                  const oldCard = document.querySelector(`[data-card="${id}"]`);

                  if (newCard && oldCard) {
                    oldCard.replaceWith(newCard);
                  }
                })
                .catch(() => {});
            }, 500);
          }
        })
        .catch(() => {
          clearInterval(interval);
        });
    }, 1000);
}

document.querySelectorAll('[data-progress-bar]').forEach(bar => {
    const id = bar.getAttribute('data-progress-bar');
    startPollingForFile(id);
});