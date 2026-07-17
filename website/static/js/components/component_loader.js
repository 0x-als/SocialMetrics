const dashboardComponents = [];


function registerComponent(config) {

    dashboardComponents.push(config);

}


async function loadComponent(config) {

    const container = document.getElementById(config.container);

    showLoader(config.loader);

    try {

        const response = await fetch(config.url);

        if (!response.ok) {
            throw new Error(response.status);
        }


        const html = await response.text();


        await new Promise(resolve => setTimeout(resolve, 600));


        container.innerHTML = html;


        container.classList.add("loaded");


        if (config.init) {
            await config.init();
        }


    } catch(error) {

        console.error(error);

    } finally {

        hideLoader(config.loader);

    }
}


async function loadDashboardComponents() {

    const tasks =
        dashboardComponents.map(
            component => loadComponent(component)
        );


    await Promise.all(tasks);

}