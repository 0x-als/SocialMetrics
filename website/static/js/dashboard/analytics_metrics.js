window.initAnalyticsMetrics = async function () {
    const response = await fetch("/api/dashboard/analytics_metrics/data");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    renderTopAccounts(data.top_accounts);
    renderAnomalies(data.anomalies);
};

function formatNumber(value) {
    return Number(value || 0).toLocaleString("ru-RU");
}

function renderTopAccounts(accounts) {
    const container = document.getElementById("top-accounts-list");
    container.innerHTML = "";

    if (!accounts || accounts.length === 0) {
        container.innerHTML = `<div class="analytics-empty">Нет данных</div>`;
        return;
    }

    accounts.forEach(a => {
        const row = document.createElement("div");
        row.className = "analytics-row";

        const viewsTotal = (a.views_video || 0) + (a.views_picture || 0);

        row.innerHTML = `
            <div>${a.username}</div>
            <div>${a.type}</div>
            <div>${formatNumber(viewsTotal)}</div>
            <div>${formatNumber(a.likes)}</div>
            <div>${formatNumber(a.comments_count)}</div>
            <div>${formatNumber(a.reposts)}</div>
            <div>${formatNumber(a.saves)}</div>
        `;

        container.appendChild(row);
    });
}


function renderAnomalies(anomalies) {
    const container = document.getElementById("anomalies-list");
    container.innerHTML = "";

    if (!anomalies || anomalies.length === 0) {
        container.innerHTML = `<div class="analytics-empty">Аномалий нет</div>`;
        return;
    }

    anomalies.forEach(a => {
        const row = document.createElement("div");
        row.className = "analytics-row";

        row.innerHTML = `
            <div>${a.username}</div>
            <div>${a.type}</div>
            <div>${formatNumber(a.views)}</div>
            <div>${formatNumber(a.avg_views)}</div>
            <div class="analytics-factor">${a.views_factor}x</div>
        `;

        container.appendChild(row);
    });
}

