let lineChart = null;


async function loadUsersForLineMetrics() {

    const response = await fetch("/api/dashboard/list_social_networks");

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    const users = await response.json();

    const select = document.getElementById("line-user-id");

    if (!select) {
        return;
    }

    select.innerHTML = "";

    users.forEach(user => {

        const option = document.createElement("option");

        option.value = user.user_id;
        option.textContent = user.username;

        select.appendChild(option);

    });
}


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


    if (userSelect.options.length > 0) {
        userSelect.selectedIndex = 0;
    }


    btn.addEventListener(
        "click",
        loadLineMetricsData
    );

}


async function loadLineMetricsData() {

    const userId =
        document.getElementById("line-user-id").value;


    const type =
        document.getElementById("line-type").value;


    const metric =
        document.getElementById("line-metric").value;


    const dateFrom =
        document.getElementById("line-date-from").value;


    const dateTo =
        document.getElementById("line-date-to").value;



    const url =
        `/api/dashboard/line_metrics/data` +
        `?user_id=${encodeURIComponent(userId)}` +
        `&type=${encodeURIComponent(type)}` +
        `&metric=${encodeURIComponent(metric)}` +
        `&date_from=${encodeURIComponent(dateFrom)}` +
        `&date_to=${encodeURIComponent(dateTo)}`;



    const response = await fetch(url);


    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }


    const data = await response.json();


    renderLineChart(
        data.points,
        metric
    );

}



function renderLineChart(points, metric) {

    const canvas =
        document.getElementById("line-metrics-canvas");


    if (!canvas) {
        return;
    }


    const dpr =
        window.devicePixelRatio || 1;


    const rect =
        canvas.getBoundingClientRect();


    canvas.width =
        rect.width * dpr;


    canvas.height =
        rect.height * dpr;



    const ctx =
        canvas.getContext("2d");


    ctx.scale(
        dpr,
        dpr
    );


    const labels =
        points.map(point => point.day);


    const values =
        points.map(point => point.value);



    if (lineChart) {
        lineChart.destroy();
    }



    const gradient =
        ctx.createLinearGradient(
            0,
            0,
            0,
            canvas.height
        );


    gradient.addColorStop(
        0,
        "rgba(123, 94, 255, 0.35)"
    );


    gradient.addColorStop(
        1,
        "rgba(123, 94, 255, 0.05)"
    );



    lineChart = new Chart(
        canvas,
        {
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

                        borderWidth: 3
                    }
                ]
            },


            options: {

                responsive: true,

                maintainAspectRatio: false,


                plugins: {

                    legend: {
                        display: false
                    },

                    title: {
                        display: false
                    }
                },


                scales: {

                    x: {

                        ticks: {
                            color: "#c8d0e0"
                        },

                        grid: {
                            color: "rgba(255,255,255,0.06)"
                        }

                    },


                    y: {

                        beginAtZero: true,

                        ticks: {
                            color: "#c8d0e0"
                        },

                        grid: {
                            color: "rgba(255,255,255,0.06)"
                        }

                    }

                }

            }
        }
    );

}



window.initLineMetrics = async function () {

    await loadUsersForLineMetrics();

    initLineMetricsControls();

    await loadLineMetricsData();

};