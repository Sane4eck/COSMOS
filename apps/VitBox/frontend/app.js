const inputPath = document.getElementById("input-path");
const outputPath = document.getElementById("output-path");
const chooseInputButton = document.getElementById("choose-input");
const chooseOutputButton = document.getElementById("choose-output");
const convertButton = document.getElementById("convert");
const statusBox = document.getElementById("status");

function setStatus(message, kind = "") {
    statusBox.textContent = message;
    statusBox.className = `status ${kind}`.trim();
}

async function waitForBridge() {
    const startedAt = Date.now();

    while (Date.now() - startedAt < 10000) {
        const api =
            window.parent?.pywebview?.api ??
            window.pywebview?.api;

        if (api) {
            return api;
        }

        await new Promise((resolve) => setTimeout(resolve, 50));
    }

    throw new Error("pywebview API не готовий");
}

async function invoke(command, payload = {}) {
    const api = await waitForBridge();
    const response = await api.invoke(command, payload);

    if (!response.ok) {
        throw new Error(response.error || "Невідома помилка");
    }

    return response.result;
}

function setBusy(isBusy) {
    chooseInputButton.disabled = isBusy;
    chooseOutputButton.disabled = isBusy;
    convertButton.disabled = isBusy;
}

chooseInputButton.addEventListener("click", async () => {
    try {
        const result = await invoke("VitBox.choose_input");

        if (!result.path) {
            return;
        }

        inputPath.value = result.path;
        outputPath.value = "";
        setStatus("Вхідний файл вибрано");
    } catch (error) {
        setStatus(error.message, "error");
    }
});

chooseOutputButton.addEventListener("click", async () => {
    try {
        const result = await invoke(
            "VitBox.choose_output",
            {input_path: inputPath.value},
        );

        if (!result.path) {
            return;
        }

        outputPath.value = result.path;
        setStatus("Шлях збереження вибрано");
    } catch (error) {
        setStatus(error.message, "error");
    }
});

convertButton.addEventListener("click", async () => {
    setBusy(true);
    setStatus("Виконується перетворення…", "working");

    try {
        const result = await invoke(
            "VitBox.convert",
            {
                input_path: inputPath.value,
                output_path: outputPath.value,
            },
        );

        setStatus(
            `Готово. Рядків: ${result.rows}, ` +
            `стовпців: ${result.columns}. ` +
            `Файл: ${result.output}`,
            "success",
        );
    } catch (error) {
        setStatus(error.message, "error");
    } finally {
        setBusy(false);
    }
});
