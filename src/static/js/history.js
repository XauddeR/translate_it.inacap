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