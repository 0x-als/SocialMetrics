window.loadUsers = async function () {
    const response = await fetch("/api/settings/users");
    if (!response.ok) {
        return;
    }
    const users = await response.json();
    const body = document.getElementById("usersTableBody");
    body.innerHTML = "";
    users.forEach(user => {
        const row = document.createElement("tr");
        row.innerHTML = `
        <td>${user.login}</td>
        <td>${user.role}</td>
        <td>${user.created_at}</td>
        <td>${user.updated_at}</td>
        <td>
        <button class="btn-delete" onclick="deleteUser(${user.id})">удалить</button>
        </td>
        `;
        body.appendChild(row);
    });
};

async function loadRoles() {
    const response = await fetch("/api/settings/users/roles");
    if (!response.ok) {
        return;
    }
    const roles = await response.json();
    const select = document.getElementById("userRole");
    select.innerHTML = "";
    roles.forEach(role => {
        const option = document.createElement("option");
        option.value = role.id;
        option.textContent = role.title;
        select.appendChild(option);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    loadUsers();
    loadRoles();
});