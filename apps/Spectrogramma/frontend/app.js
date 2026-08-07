let selectedPath = "";
let analysisReady = false;
let visualUpdateTimer = null;
let analysisDetailsBase = "";

function fillSelect(select, items, selectedId) {
    select.innerHTML = "";
    for (const item of items) {
        select.add(new Option(item.label, item.id, false, item.id === selectedId));
    }
    select.disabled = items.length === 0;
}

function showImage(imageData) {
    const image = $("spectrogram-image");
    image.src = imageData;
    image.hidden = false;
    $("placeholder").hidden = true;
}

function updateScalePlaceholders(vmin, vmax) {
    $("vmin").placeholder = `Auto (${Number(vmin).toFixed(2)})`;
    $("vmax").placeholder = `Auto (${Number(vmax).toFixed(2)})`;
}

function visualPayload() {
    return {
        formula: $("formula").value.trim(),
        vmin: $("vmin").value.trim(),
        vmax: $("vmax").value.trim(),
    };
}

function scaleInputsValid() {
    const vminText = $("vmin").value.trim();
    const vmaxText = $("vmax").value.trim();
    const vmin = vminText === "" ? null : Number(vminText);
    const vmax = vmaxText === "" ? null : Number(vmaxText);

    if ((vmin !== null && !Number.isFinite(vmin)) || (vmax !== null && !Number.isFinite(vmax))) {
        return false;
    }
    if (vmin !== null && vmax !== null && vmin >= vmax) {
        setStatus("vmin повинен бути меншим за vmax", "error");
        return false;
    }
    return true;
}

function compactNumber(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) return String(value);
    const magnitude = Math.abs(number);
    if (magnitude !== 0 && (magnitude < 1e-3 || magnitude >= 1e4)) {
        return number.toExponential(3);
    }
    return Number(number.toPrecision(6)).toString();
}

function unitSuffix(unit) {
    return unit ? ` ${unit}` : "";
}

function setAnalysisDetailsBase(result) {
    analysisDetailsBase = `X: ${result.x_label}; Y: ${result.y_label}; fs: ${result.actual_fs.toPrecision(8)} Hz; точок: ${result.points}; сегментів: ${result.windows}; частотних ліній: ${result.frequency_bins}; діапазон: ${result.actual_start.toFixed(6)}–${result.actual_end.toFixed(6)} с`;
}

function renderVisualDetails(result) {
    const info = $("details");
    info.hidden = false;
    const unit = unitSuffix(result.value_unit);
    info.textContent = `${analysisDetailsBase}; SXX: ${compactNumber(result.raw_min)}…${compactNumber(result.raw_max)}; результат: ${compactNumber(result.result_min)}…${compactNumber(result.result_max)}${unit}; шкала: ${compactNumber(result.vmin)}…${compactNumber(result.vmax)}${unit}; формула: ${result.formula}.`;
}

async function updateVisualization() {
    if (!analysisReady || !scaleInputsValid()) return;

    const formula = $("formula").value.trim();
    if (!formula) {
        setStatus("Введіть формулу відображення", "error");
        return;
    }

    try {
        setStatus("Оновлення формули та кольорової шкали…", "working");
        const result = await apiCall("Spectrogramma.update_visual", visualPayload());
        showImage(result.image);
        updateScalePlaceholders(result.vmin, result.vmax);
        renderVisualDetails(result);
        const unit = unitSuffix(result.value_unit);
        setStatus(
            `Відображення оновлено: ${compactNumber(result.vmin)}…${compactNumber(result.vmax)}${unit}`,
            "success",
        );
    } catch (error) {
        setStatus(error.message, "error");
    }
}

function scheduleVisualUpdate() {
    if (!analysisReady) return;
    clearTimeout(visualUpdateTimer);
    visualUpdateTimer = setTimeout(updateVisualization, 650);
}

async function refreshAxisInfo() {
    if (!selectedPath || !$("x-axis").value || !$("y-axis").value) return;
    try {
        const result = await apiCall("Spectrogramma.axis_info", {
            path: selectedPath,
            x_axis: $("x-axis").value,
            y_axis: $("y-axis").value,
            fs: $("fs").value,
        });
        if (result.suggested_fs) {
            $("fs").value = Number(result.suggested_fs).toPrecision(10);
        }
        $("start-sec").value = Number(result.x_min).toPrecision(10);
        const available = Math.max(0, Number(result.x_max) - Number(result.x_min));
        if (available > 0) {
            $("duration-sec").value = Math.min(300, available).toPrecision(10);
        }
        if (result.warning) setStatus(result.warning, "working");
    } catch (error) {
        setStatus(error.message, "error");
    }
}

$("choose-file").onclick = async () => {
    setBusy(true);
    try {
        const selected = await apiCall("Spectrogramma.choose_source");
        if (!selected.path) return;
        selectedPath = selected.path;
        analysisReady = false;
        analysisDetailsBase = "";
        $("vmin").placeholder = "Auto";
        $("vmax").placeholder = "Auto";
        $("file-path").textContent = selected.path;
        setStatus("Читання структури файлу…", "working");
        const source = await apiCall("Spectrogramma.inspect_source", {
            path: selectedPath,
        });
        fillSelect($("x-axis"), source.x_axes, source.default_x);
        fillSelect($("y-axis"), source.y_axes, source.default_y);
        $("analyze").disabled = false;
        await refreshAxisInfo();
        setStatus(`${source.source_type.toUpperCase()}: осі завантажено`, "success");
    } catch (error) {
        setStatus(error.message, "error");
    } finally {
        setBusy(false);
    }
};

$("x-axis").onchange = refreshAxisInfo;
$("y-axis").onchange = refreshAxisInfo;
$("formula").addEventListener("input", scheduleVisualUpdate);
$("vmin").addEventListener("input", scheduleVisualUpdate);
$("vmax").addEventListener("input", scheduleVisualUpdate);

$("analyze").onclick = async () => {
    if (!scaleInputsValid()) return;
    if (!$("formula").value.trim()) {
        setStatus("Введіть формулу відображення", "error");
        return;
    }

    setBusy(true);
    analysisReady = false;
    setStatus("Формування спектрограми…", "working");
    try {
        const result = await apiCall("Spectrogramma.analyze", {
            path: selectedPath,
            x_axis: $("x-axis").value,
            y_axis: $("y-axis").value,
            fs: $("fs").value,
            start_sec: $("start-sec").value,
            duration_sec: $("duration-sec").value,
            y_max: $("y-max").value,
            formula: $("formula").value.trim(),
            vmin: $("vmin").value.trim(),
            vmax: $("vmax").value.trim(),
            nperseg: $("nperseg").value,
            open_external: $("open-external").checked,
        });
        showImage(result.image);
        updateScalePlaceholders(result.vmin, result.vmax);
        analysisReady = true;
        setAnalysisDetailsBase(result);
        renderVisualDetails(result);

        const unit = unitSuffix(result.value_unit);
        const notes = [];
        if (result.clipped) notes.push("Діапазон скорочено до доступних даних");
        if (result.warning) notes.push(result.warning);
        if (result.external_opened) notes.push("Відкрито інтерактивне вікно");
        notes.push(`Шкала ${compactNumber(result.vmin)}…${compactNumber(result.vmax)}${unit}`);
        setStatus(
            `Спектрограму побудовано${notes.length ? `. ${notes.join(". ")}.` : "."}`,
            "success",
        );
    } catch (error) {
        setStatus(error.message, "error");
    } finally {
        setBusy(false);
    }
};
