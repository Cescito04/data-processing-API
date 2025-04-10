// Fonction pour initialiser les graphiques
function initializeCharts() {
    // Récupérer les données statistiques
    const statsTable = document.querySelector('.table-responsive table');
    if (!statsTable) return;

    // Extraire les données du tableau
    const data = extractDataFromTable(statsTable);
    
    // Créer le conteneur pour les graphiques
    const chartsContainer = document.createElement('div');
    chartsContainer.className = 'charts-container mt-4';
    chartsContainer.style.height = '300px';
    statsTable.parentElement.appendChild(chartsContainer);

    // Créer le canvas pour le graphique
    const canvas = document.createElement('canvas');
    canvas.id = 'statsChart';
    chartsContainer.appendChild(canvas);

    // Créer le graphique
    createChart(canvas, data);
}

// Fonction pour extraire les données du tableau
function extractDataFromTable(table) {
    const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    
    const data = {
        labels: [],
        moyenne: [],
        mediane: []
    };

    rows.forEach(row => {
        const cells = Array.from(row.querySelectorAll('td'));
        data.labels.push(cells[0].textContent.trim());
        data.moyenne.push(parseFloat(cells[1].textContent.trim()));
        data.mediane.push(parseFloat(cells[2].textContent.trim()));
    });

    return data;
}

// Fonction pour créer le graphique
function createChart(canvas, data) {
    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Moyenne',
                    data: data.moyenne,
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Médiane',
                    data: data.mediane,
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Statistiques descriptives'
                },
                legend: {
                    position: 'top'
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            }
        }
    });
}

// Initialiser les graphiques quand le DOM est chargé
document.addEventListener('DOMContentLoaded', initializeCharts);