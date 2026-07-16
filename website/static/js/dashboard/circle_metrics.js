const chartColors = ["#4e79a7","#f28e2b","#e15759","#76b7b2","#59a14f","#edc948","#b07aa1","#ff9da7"];

function getPlatformStats() {
    const element = document.getElementById("platform-stats");
    if (!element) return [];
    try { return JSON.parse(element.dataset.stats); } catch (e) { return []; }
}

function buildDataset(field) {
    const stats = getPlatformStats();
    return {
        labels: stats.map(item => item.platform),
        data: stats.map(item => item[field] || 0)
    };
}

function createPieChart(container, title, field) {
    const item = document.createElement("div");
    item.className = "chart-item";
    item.innerHTML = `<h3>${title}</h3>`;
    const canvas = document.createElement("canvas");
    item.appendChild(canvas);
    container.appendChild(item);

    const dataset = buildDataset(field);
    new Chart(canvas, {
        type: "pie",
        data: {
            labels: dataset.labels,
            datasets: [{ data: dataset.data, backgroundColor: chartColors }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: "bottom", labels: { color: "#e6e6e6", font: { size: 12 }} }
            }
        }
    });
}

window.renderCircleCharts = function () {
    const container = document.getElementById("charts-container");
    container.innerHTML = "";
    createPieChart(container, "Лайки", "likes");
    createPieChart(container, "Просмотры видео", "views_video");
    createPieChart(container, "Описания", "description_count");
    createPieChart(container, "Сохранения", "saves");
    createPieChart(container, "Репосты", "reposts");
    createPieChart(container, "Комментарии", "comments_count");
};