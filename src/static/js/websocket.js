const socket = io();

function updateProgressUI(id, progreso, estado) {
    const bar = document.querySelector(`[data-progress-bar='${id}']`);
    const label = document.querySelector(`[data-progress-label='${id}']`);

    if (!bar) return;

    if (progreso !== undefined && progreso !== null) {
        bar.style.width = `${progreso}%`;
    }

    if (label) {
        if (estado === 'error') {
            label.textContent = 'Error';
            label.classList.add('text-rose-400');
        } else if (estado === 'completado') {
            label.textContent = 'Completado';
            label.classList.remove('text-rose-300');
        } else {
            label.textContent = `${progreso ?? 0}%`;
        }
    }

    if (estado === 'completado' || estado === 'error') {
        socket.emit('leave_file_room', { file_id: id });

        setTimeout(() => {
            reloadCard(id);
        }, 1000);
    }
}

function joinRoomsAndSync() {
    document.querySelectorAll('[data-progress-bar]').forEach(bar => {
        const id = bar.getAttribute('data-progress-bar');

        socket.emit('join_file_room', { file_id: id });
        fetch(`/api/file_status/${id}`)
            .then(response => {
                if (!response.ok) return null;
                return response.json();
            })
            .then(data => {
                if (!data || data.error) return;
                const progreso = data.progreso;
                const estado = data.estado;
                updateProgressUI(id, progreso, estado);
            })
            .catch(err => {
                console.error('Error obteniendo estado del archivo:', err);
            });
    });
}

socket.on('connect', () => {
    joinRoomsAndSync();
});

socket.on('status_update', (data) => {
    const id = data.id;
    const progreso = data.progreso;
    const estado = data.estado;

    updateProgressUI(id, progreso, estado);
});

function reloadCard(id) {
    fetch(window.location.href)
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newCard = doc.querySelector(`[data-card='${id}']`);
            const oldCard = document.querySelector(`[data-card='${id}']`);

            if (newCard && oldCard) {
                oldCard.replaceWith(newCard);
            }
        })
        .catch(err => console.error('Error recargando tarjeta:', err));
}