(function () {
  const ctx = document.getElementById('usersChart');
  if (!ctx) return;

  const labels = JSON.parse(ctx.dataset.labels || '[]');
  const values = JSON.parse(ctx.dataset.values || '[]');

  if (!labels.length || !values.length) {
    console.warn('Sin datos para el gráfico de usuarios.');
  }

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Registros diarios',
        data: values,
        tension: 0.35,
        fill: true,
        borderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 4,
        borderColor: 'rgba(59,130,246,1)',
        backgroundColor: 'rgba(59,130,246,0.18)'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            color: '#cbd5f5',
            maxRotation: 0,
            autoSkip: true
          }
        },
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(148,163,184,0.25)' },
          ticks: { color: '#e5e7eb', precision: 0 }
        }
      },
      plugins: {
        legend: {
          labels: { color: '#e5e7eb' }
        },
        tooltip: {
          callbacks: {
            label: function (ctx) {
              const v = ctx.parsed.y || 0;
              return ` ${v} registro${v === 1 ? '' : 's'}`;
            }
          }
        }
      }
    }
  });
})();
