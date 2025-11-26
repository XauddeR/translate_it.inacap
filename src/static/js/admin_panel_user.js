const addModal = document.getElementById('addUserModal');
function openAddUserModal() {
    addModal.classList.remove('hidden');
    addModal.classList.add('flex');
    const modalFlash = document.getElementById('modalFlashContainer');
    if (modalFlash) modalFlash.innerHTML = '';
}
function closeAddUserModal() {
    addModal.classList.add('hidden');
    addModal.classList.remove('flex');
}

addModal?.addEventListener('click', (e) => { 
    if (e.target === addModal) closeAddUserModal(); 
});

const editModal = document.getElementById('editUserModal');
const editForm  = document.getElementById('editUserForm');

function openEditUserModal(id, usuario, email, is_admin) {
    editForm.action = "{{ url_for('admin.update_user', user_id=0) }}".replace('/0', `/${id}`);

    document.getElementById('edit_usuario').value = usuario || '';
    document.getElementById('edit_email').value   = email || '';
    const passEl  = document.getElementById('edit_password');
    const nivelEl = document.getElementById('edit_nivel');
    if (passEl)  passEl.value  = '';
    if (nivelEl) nivelEl.value = (is_admin ? 'admin' : 'usuario');

    editModal.classList.remove('hidden');
    editModal.classList.add('flex');
}

function closeEditUserModal() {
    editModal.classList.add('hidden');
    editModal.classList.remove('flex');
}

editModal?.addEventListener('click', (e) => { 
    if (e.target === editModal) closeEditUserModal(); 
});

document.addEventListener('click', (e) => {
    const btn = e.target.closest('.btn-edit-user');
    if (!btn) return;
    const id      = Number(btn.dataset.id);
    const usuario = btn.dataset.usuario || '';
    const email   = btn.dataset.email || '';
    const isAdmin = btn.dataset.isAdmin === '1' || btn.dataset.isAdmin === 'true';
    openEditUserModal(id, usuario, email, isAdmin);
});

editForm?.addEventListener('submit', () => {
    const submitBtn = editForm.querySelector('button[type="submit"]');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Guardando…';
    }
});

const confirmModal = document.getElementById('confirmDeleteModal');
const confirmOverlay = document.getElementById('confirmOverlay');
const cancelDelBtn = document.getElementById('cancelDeleteBtn');
const delForm = document.getElementById('deleteUserForm');

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
    const btn = e.target.closest('.btn-delete-user');
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
    if (addModal && !addModal.classList.contains('hidden')) closeAddUserModal();
    if (editModal && !editModal.classList.contains('hidden')) closeEditUserModal();
    if (confirmModal && !confirmModal.classList.contains('hidden')) closeConfirm();
});