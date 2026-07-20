window.deleteUser = async function (id) {
    const confirmDelete = confirm("Удалить пользователя?");
    if (!confirmDelete) {
        return;
    }
    const response = await fetch(`/api/settings/users/${id}`, {
        method: "DELETE"
    });
    const data = await response.json();
    if (!response.ok) {
        showError(data.message || "Ошибка удаления");
        return;
    }
    showSuccess("Пользователь удалён");
    await loadUsers();
};