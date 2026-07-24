const chooseFileButton = document.getElementById("choose-file");
const plotButton = document.getElementById("plot");
const saveButton = document.getElementById("save");
const fileName = document.getElementById("file-name");
const timeColumn = document.getElementById("time-column");
const xMin = document.getElementById("x-min");
const xMax = document.getElementById("x-max");
const parameters = document.getElementById("parameters");
const statusBox = document.getElementById("status");
const plotImage = document.getElementById("plot-image");
const previewPlaceholder = document.getElementById("preview-placeholder");

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
    chooseFileButton.disabled = value;
    plotButton.disabled = value;
    saveButton.disabled = value;
}

function renderParameters(items) {
    parameters.innerHTML = "";
    parameters.classList.remove("empty");

    for (const item of items) {
        const row = document.createElement("div");
        row.className = "parameter-row";
        row.dataset.parameter = item.name;

        const name = document.createElement("span");
        name.textContent = item.name;

        const left = document.createElement("input");
        left.type = "checkbox";
        left.className = "left-choice";
        left.checked = item.side === "left";

        const right = document.createElement("input");
        right.type = "checkbox";
        right.className = "right-choice";
        right.checked = item.side === "right";

        left.addEventListener("change", () => {
            if (left.checked) right.checked = false;
        });
        right.addEventListener("change", () => {
            if (right.checked) left.checked = false;
        });

        const leftLabel = document.createElement("label");
        leftLabel.append(left, document.createTextNode(" Ліва сторона"));
        const rightLabel = document.createElement("label");
        rightLabel.append(right, document.createTextNode(" Права сторона"));

        row.append(name, leftLabel, rightLabel);
        parameters.appendChild(row);
    }
}

function collectSelections() {
    return [...parameters.querySelectorAll(".parameter-row")].flatMap((row) => {
        const parameter = row.dataset.parameter;
        if (row.querySelector(".left-choice").checked) {
            return [{parameter, side: "left"}];
        }
        if (row.querySelector(".right-choice").checked) {
            return [{parameter, side: "right"}];
        }
        return [];
    });
}

chooseFileButton.addEventListener("click", async () => {
    try {
        const selected = await invoke("CSVVisualizer.choose_csv");
        if (!selected.path) return;

        setBusy(true);
        setStatus("Завантаження CSV…", "working");
        const result = await invoke("CSVVisualizer.load_csv", {path: selected.path});

        fileName.textContent = result.file_name;
        timeColumn.innerHTML = "";
        for (const column of result.numeric_columns) {
            const option = new Option(column, column, false, column === result.time_column);
            timeColumn.add(option);
        }
        xMin.value = Number(result.x_min).toFixed(3);
        xMax.value = Number(result.x_max).toFixed(3);
        renderParameters(result.parameters);
        setStatus(`Завантажено: ${result.rows} рядків, ${result.columns} стовпців`, "success");
    } catch (error) {
        setStatus(error.message, "error");
    } finally {
        setBusy(false);
    }
});

timeColumn.addEventListener("change", async () => {
    try {
        const result = await invoke("CSVVisualizer.get_x_range", {
            time_column: timeColumn.value,
        });
        xMin.value = Number(result.x_min).toFixed(3);
        xMax.value = Number(result.x_max).toFixed(3);
    } catch (error) {
        setStatus(error.message, "error");
    }
});

plotButton.addEventListener("click", async () => {
    setBusy(true);
    setStatus("Побудова графіка…", "working");
    try {
        const result = await invoke("CSVVisualizer.plot", {
            time_column: timeColumn.value,
            x_min: xMin.value,
            x_max: xMax.value,
            selections: collectSelections(),
        });
        plotImage.src = result.image;
        plotImage.hidden = false;
        previewPlaceholder.hidden = true;
        setStatus("Графік побудовано", "success");
    } catch (error) {
        setStatus(error.message, "error");
    } finally {
        setBusy(false);
    }
});

saveButton.addEventListener("click", async () => {
    setBusy(true);
    setStatus("Збереження Excel…", "working");
    try {
        const result = await invoke("CSVVisualizer.save_excel", {
            time_column: timeColumn.value,
            x_min: xMin.value,
            x_max: xMax.value,
        });
        setStatus(`Файл збережено: ${result.path}`, "success");
    } catch (error) {
        setStatus(error.message, "error");
    } finally {
        setBusy(false);
    }
});
