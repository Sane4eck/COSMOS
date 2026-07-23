const navigation = document.getElementById("app-navigation");
const container = document.getElementById("app-container");
const pageTitle = document.getElementById("page-title");

const frames = new Map();

function activateApp(app) {
    for (const button of navigation.querySelectorAll("button")) {
        button.classList.toggle(
            "active",
            button.dataset.appId === app.id,
        );
    }

    for (const [appId, frame] of frames.entries()) {
        frame.classList.toggle("active", appId === app.id);
    }

    pageTitle.textContent = app.title;
}

function createApp(app, isFirst) {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.appId = app.id;
    button.textContent = app.title;
    button.addEventListener("click", () => activateApp(app));
    navigation.appendChild(button);

    const frame = document.createElement("iframe");
    frame.src = app.url;
    frame.title = app.title;
    frame.className = "app-frame";
    container.appendChild(frame);
    frames.set(app.id, frame);

    if (isFirst) {
        activateApp(app);
    }
}

async function loadApps() {
    try {
        const response = await fetch("/api/apps");

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const apps = await response.json();

        if (!apps.length) {
            container.innerHTML = "<p>Немає підключених модулів.</p>";
            return;
        }

        apps.forEach((app, index) => createApp(app, index === 0));
    } catch (error) {
        container.innerHTML =
            `<p class="error">Помилка завантаження модулів: ${error}</p>`;
    }
}

loadApps();
