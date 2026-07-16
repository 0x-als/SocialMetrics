async function loadCircleMetrics() {
    try {
        const response = await fetch("/api/dashboard/circle_metrics");

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const html = await response.text();
        document.getElementById("circle-metrics-container").innerHTML = html;

        if (typeof window.renderCircleCharts === "function") {
            window.renderCircleCharts();
        }

    } catch (err) {
        console.error("Ошибка загрузки статистики:", err);
    }
}

async function loadLineMetricsFragment() {
    try {
        const response = await fetch("/api/dashboard/line_metrics");

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const html = await response.text();
        document.getElementById("line-metrics-container").innerHTML = html;

        // 1. Загружаем пользователей
        await loadUsersForLineMetrics();

        // 2. Инициализируем кнопки
        if (typeof initLineMetricsControls === "function") {
            initLineMetricsControls();
        }

        // 3. Автоматически выбираем первого пользователя и строим график
        autoLoadFirstUserMetrics();

    } catch (err) {
        console.error("Ошибка загрузки линейной статистики:", err);
    }
}

async function loadUsersForLineMetrics() {
    try {
        const response = await fetch("/api/dashboard/list_social_networks");

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const users = await response.json();

        const select = document.getElementById("line-user-id");
        select.innerHTML = "";

        users.forEach(u => {
            const option = document.createElement("option");
            option.value = u.user_id;
            option.textContent = u.username;
            select.appendChild(option);
        });

    } catch (err) {
        console.error("Ошибка загрузки пользователей:", err);
    }
}

async function autoLoadFirstUserMetrics() {
    const select = document.getElementById("line-user-id");
    if (!select || select.options.length === 0) {
        console.warn("Нет пользователей для автозагрузки");
        return;
    }

    // Выбираем первого пользователя
    select.selectedIndex = 0;

    // Автоматически ставим период — например, последние 30 дней
    const dateTo = document.getElementById("line-date-to");
    const dateFrom = document.getElementById("line-date-from");

    const today = new Date();
    const past = new Date();
    past.setDate(today.getDate() - 30);

    dateTo.value = today.toISOString().split("T")[0];
    dateFrom.value = past.toISOString().split("T")[0];

    // Автоматически выбираем метрику
    const metricSelect = document.getElementById("line-metric");
    metricSelect.value = "likes";

    // Строим график
    await loadLineMetricsData();
}

async function loadLineMetricsData() {
    const userId = document.getElementById("line-user-id").value;
    const metric = document.getElementById("line-metric").value;
    const dateFrom = document.getElementById("line-date-from").value;
    const dateTo = document.getElementById("line-date-to").value;

    const url =
        `/api/dashboard/line_metrics/data` +
        `?user_id=${encodeURIComponent(userId)}` +
        `&metric=${encodeURIComponent(metric)}` +
        `&date_from=${encodeURIComponent(dateFrom)}` +
        `&date_to=${encodeURIComponent(dateTo)}`;

    const response = await fetch(url);
    const data = await response.json();

    renderLineChart(data.points, metric);
}


document.addEventListener("DOMContentLoaded", () => {
    loadCircleMetrics();
    loadUsersForLineMetrics()
    loadLineMetricsFragment();
});
