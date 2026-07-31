const $ = (id) => document.getElementById(id);

async function apiCall(command, payload = {}) {
    const started = Date.now();
    let api = null;
    while (!api && Date.now() - started < 10000) {
        api = window.parent?.pywebview?.api ?? window.pywebview?.api;
        if (!api) await new Promise((resolve) => setTimeout(resolve, 50));
    }
    if (!api) throw new Error("pywebview API не готовий");
    const response = await api.invoke(command, payload);
    if (!response.ok) throw new Error(response.error || "Невідома помилка");
    return response.result;
}

function setStatus(message, kind = "") {
    const box = $("status");
    box.textContent = message;
    box.className = `status ${kind}`.trim();
}

function setBusy(value) {
    $("choose-file").disabled = value;
    $("analyze").disabled = value;
}
