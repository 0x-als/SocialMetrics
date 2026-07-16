let lineChart = null;

function initLineMetricsControls() {
    const btn = document.getElementById("line-load-btn");
    const userSelect = document.getElementById("line-user-id");
    const metricSelect = document.getElementById("line-metric");
    const dateFromInput = document.getElementById("line-date-from");
    const dateToInput = document.getElementById("line-date-to");

    const today = new Date();
    const past = new Date();
    past.setDate(today.getDate() - 30);

    dateToInput.value = today.toISOString().split("T")[0];
    dateFromInput.value = past.toISOString().split("T")[0];
    metricSelect.value = "likes";
    if (userSelect.options.length > 0) userSelect.selectedIndex = 0;

    btn.addEventListener("click", loadLineMetricsData);
    loadLineMetricsData();
}

async function loadLineMetricsData() {
    const userId = document.getElementById("line-user-id").value || "";
    const metric = document.getElementById("line-metric").value;
    const dateFrom = document.getElementById("line-date-from").value;
    const dateTo = document.getElementById("line-date-to").value;

    try {
        const url = `/api/dashboard/line_metrics/data?user_id=${encodeURIComponent(userId)}&metric=${encodeURIComponent(metric)}&date_from=${encodeURIComponent(dateFrom)}&date_to=${encodeURIComponent(dateTo)}`;
        const response = await fetch(url);
        if (!response.ok) return;
        const data = await response.json();

        renderLineChart(data.points, metric);
    } catch (e) {
        console.error(e);
    }
}

function renderLineChart(points, metric) {
    const canvas = document.getElementById("line-metrics-canvas");
    if (!canvas) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;

    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);

    const labels = points.map(p => p.day);
    const values = points.map(p => p.value);

    if (lineChart) lineChart.destroy();

    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    gradient.addColorStop(0, "rgba(123, 94, 255, 0.35)");
    gradient.addColorStop(1, "rgba(123, 94, 255, 0.05)");

    lineChart = new Chart(canvas, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    data: values,
                    borderColor: "#7b5eff",
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: "#4cc9f0",
                    pointBorderColor: "#4cc9f0",
                    borderWidth: 3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: { display: false }
            },
            scales: {
                x: {
                    ticks: {
                        color: "#c8d0e0",
                        font: { size: 13 }
                    },
                    grid: {
                        color: "rgba(255,255,255,0.06)"
                    },
                    border: {
                        color: "rgba(255,255,255,0.25)"
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: "#c8d0e0",
                        font: { size: 13 }
                    },
                    grid: {
                        color: "rgba(255,255,255,0.06)"
                    },
                    border: {
                        color: "rgba(255,255,255,0.25)"
                    }
                }
            }
        }
    });
}
