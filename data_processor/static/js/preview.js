document.addEventListener('DOMContentLoaded', function() {
    const previewButtons = document.querySelectorAll('[data-bs-toggle="modal"]');

    previewButtons.forEach(button => {
        const modalId = button.getAttribute('data-bs-target');
        if (!modalId.includes('previewModal')) return;

        const fileId = modalId.replace('#previewModal', '');
        const previewContent = document.querySelector(`#previewContent${fileId}`);

        button.addEventListener('click', async () => {
            try {
                previewContent.innerHTML = '<div class="d-flex justify-content-center"><div class="spinner-border" role="status"><span class="visually-hidden">Chargement...</span></div></div>';

                const response = await fetch(`/preview/${fileId}/`);
                const data = await response.json();

                if (data.error) {
                    previewContent.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }

                let statsHtml = '';
                if (data.stats) {
                    statsHtml = `
                        <div class="card mb-3">
                            <div class="card-header bg-info text-white">
                                <h5 class="mb-0">Statistiques descriptives</h5>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    ${Object.entries(data.stats).map(([col, stats]) => `
                                        <div class="col-md-6 mb-3">
                                            <div class="card">
                                                <div class="card-header bg-light">
                                                    <h6 class="mb-0">${col}</h6>
                                                </div>
                                                <ul class="list-group list-group-flush">
                                                    <li class="list-group-item d-flex justify-content-between">
                                                        <span>Moyenne:</span>
                                                        <strong>${stats.moyenne}</strong>
                                                    </li>
                                                    <li class="list-group-item d-flex justify-content-between">
                                                        <span>Médiane:</span>
                                                        <strong>${stats.médiane}</strong>
                                                    </li>
                                                    <li class="list-group-item d-flex justify-content-between">
                                                        <span>Écart-type:</span>
                                                        <strong>${stats['écart-type']}</strong>
                                                    </li>
                                                    <li class="list-group-item d-flex justify-content-between">
                                                        <span>Min:</span>
                                                        <strong>${stats.min}</strong>
                                                    </li>
                                                    <li class="list-group-item d-flex justify-content-between">
                                                        <span>Max:</span>
                                                        <strong>${stats.max}</strong>
                                                    </li>
                                                    <li class="list-group-item d-flex justify-content-between">
                                                        <span>Valeurs manquantes:</span>
                                                        <strong>${stats.valeurs_manquantes}</strong>
                                                    </li>
                                                </ul>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                    `;
                }

                let tableHtml = `
                    ${statsHtml}
                    <div class="table-responsive">
                        <table class="table table-striped table-hover">
                            <thead class="table-primary">
                                <tr>
                                    ${data.columns.map(col => `<th>${col}</th>`).join('')}
                                </tr>
                            </thead>
                            <tbody>
                                ${data.data.map(row => `
                                    <tr>
                                        ${data.columns.map(col => `<td>${row[col]}</td>`).join('')}
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                `;

                previewContent.innerHTML = tableHtml;
            } catch (error) {
                previewContent.innerHTML = `<div class="alert alert-danger">Erreur lors du chargement des données</div>`;
                console.error('Erreur:', error);
            }
        });
    });
});