document.addEventListener("DOMContentLoaded", () => {

    registerComponent({
        url: "/api/dashboard/circle_metrics",
        container: "circle-metrics-container",
        loader: "circle-loader",
        init: window.initCircleMetrics
    });


    registerComponent({
        url: "/api/dashboard/line_metrics",
        container: "line-metrics-container",
        loader: "line-loader",
        init: window.initLineMetrics
    });

    registerComponent({
        url: "/api/dashboard/analytics_metrics",
        container: "analytics-metrics-container",
        loader: "analytics-loader",
        init: window.initAnalyticsMetrics
    });

    loadDashboardComponents();

});
