const loadButton = document.getElementById("load");
const saveButton = document.getElementById("save");
const filterCheckbox = document.getElementById("use-filter");
const filePath = document.getElementById("file-path");
const statusBox = document.getElementById("status");
const details = document.getElementById("details");
const plotImage = document.getElementById("plot-image");
const placeholder = document.getElementById("placeholder");

async function waitForBridge() {
    const startedAt = Date.now();
    while (Date.now() - startedAt < 10000) {
        const api = window.parent?.pywebview?.api ?? window.pywebview?.api;
        if (api) return api;
        await new Promise((resolve) => setTimeout(resolve, 50));
    }
    throw new Error("pywebview API не готовий");
}

async function invoke(command, payload = {}) {
    const api = await waitForBridge();
    const response = await api.invoke(command, payload);
    if (!response.ok) throw new Error(response.error || "Невідома помилка");
    return response.result;
}

function setStatus(message, kind = "") {
    statusBox.textContent = message;
    statusBox.className = `status ${kind}`.trim();
}

function setBusy(value) {
    loadButton.disabled = value;
    filterCheckbox.disabled = value;
    saveButton.disabled = value || !plotImage.src;
}

loadButton.addEventListener("click", async () => {
    setBusy(true);
    setStatus("Завантаження та обробка даних…", "working");

    try {
        const result = await invoke("HBMVisualizer.load", {
            use_filter: filterCheckbox.checked,
        });
        if (!result.path) {
            setStatus("Вибір файлу скасовано");
            return;
        }

        filePath.textContent = result.path;
        filePath.title = result.path;
        plotImage.src = result.image;
        plotImage.hidden = false;
        placeholder.hidden = true;
        details.hidden = false;
        details.textContent =
            `Рядків: ${result.rows}; стовпців: ${result.columns}; ` +
            `фільтри: ${result.use_filter ? "увімкнено" : "вимкнено"}.`;
        saveButton.disabled = false;
        setStatus("Data loaded", "success");
    } catch (error) {
        setStatus(error.message, "error");
    } finally {
        setBusy(false);
    }
});

saveButton.addEventListener("click", async () => {
    setBusy(true);
    setStatus("Saving", "working");

    try {
        const result = await invoke("HBMVisualizer.save");
        if (!result.path) {
            setStatus("Збереження скасовано");
            return;
        }
        setStatus(`Data saved: ${result.path}`, "success");
    } catch (error) {
        setStatus(error.message, "error");
    } finally {
        setBusy(false);
    }
});
