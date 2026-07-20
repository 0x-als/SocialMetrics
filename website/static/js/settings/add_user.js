async function addUser() {
    const login = document.getElementById("userLogin").value;
    const password = document.getElementById("userPassword").value;
    const role = document.getElementById("userRole").value;
    const response = await fetch("/api/settings/users/create", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            login: login,
            password: password,
            role_id: role
        })
    });
    const data = await response.json();
    if (!response.ok) {
        showError(data.message || "Ошибка создания пользователя");
        return;
    }
    showSuccess("Пользователь добавлен");
    closeModal("userModal");
    document.getElementById("userLogin").value = "";
    document.getElementById("userPassword").value = "";
    await loadUsers();
}