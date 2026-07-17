function showLoader(id) {

    const loader = document.getElementById(id);

    if (!loader) {
        return;
    }

    loader.classList.add("show");

}


function hideLoader(id) {

    const loader = document.getElementById(id);

    if (!loader) {
        return;
    }

    loader.classList.remove("show");

}