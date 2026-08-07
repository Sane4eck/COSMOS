let selectedPath = "";
let analysisReady = false;
let visualUpdateTimer = null;
let analysisDetailsBase = "";

const SPECTRUM_UNITS = {
    amplitude_peak: "g",
    amplitude_rms: "g RMS",
    psd: "g²/Hz",
    asd: "g/√Hz",
    psd_db: "dB",
    custom: "",
};

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

function currentSpectrumUnit() {
    return SPECTRUM_UNITS[$("spectrum-type").value] ?? "";
}

function updateUnitLabels(unit = currentSpectrumUnit()) {
    const suffix = unit ? ` [${unit}]` : "";
    $("vmin-label").textContent = `vmin${suffix}`;
    $("vmax-label").textContent = `vmax${suffix}`;
}

function updateControlVisibility() {
    const custom = $("spectrum-type").value === "custom";
    const power = $("color-scale").value === "power";
    $("custom-formula-field").hidden = !custom;
    $("custom-formula-hint").hidden = !custom;
    $("gamma-field").hidden = !power;
    updateUnitLabels();
}

function updateScalePlaceholders(vmin, vmax) {
    $("vmin").placeholder = `Auto (${compactNumber(vmin)})`;
    $("vmax").placeholder = `Auto (${compactNumber(vmax)})`;
}

function visualPayload() {
    return {
        spectrum_type: $("spectrum-type").value,
        formula: $("formula").value.trim(),
        vmin: $("vmin").value.trim(),
        vmax: $("vmax").value.trim(),
        color_scale: $("color-scale").value,
        gamma: $("gamma").value,
        cmap: $("cmap").value,
    };
}

function visualInputsValid() {
    const vminText = $("vmin").value.trim();
    const vmaxText = $("vmax").value.trim();
    const vmin = vminText === "" ? null : Number(vminText);
    const vmax = vmaxText === "" ? null : Number(vmaxText);

    if ((vmin !== null && !Number.isFinite(vmin)) || (vmax !== null && !Number.isFinite(vmax))) {
        setStatus("vmin/vmax повинні бути числами або порожніми для Auto", "error");
        return false;
    }
    if (vmin !== null && vmax !== null && vmin >= vmax) {
        setStatus("vmin повинен бути меншим за vmax", "error");
        return false;
    }

    if ($("color-scale").value === "power") {
        const gamma = Number($("gamma").value);
        if (!Number.isFinite(gamma) || gamma <= 0) {
            setStatus("Gamma для Power scale повинна бути > 0", "error");
            return false;
        }
    }

    if ($("color-scale").value === "log" && vmin !== null && vmin <= 0) {
        setStatus("Для Log scale vmin повинен бути > 0 або Auto", "error");
        return false;
    }

    if ($("spectrum-type").value === "custom" && !$("formula").value.trim()) {
        setStatus("Для Custom режиму введіть формулу", "error");
        return false;
    }

    return true;
}

function setAnalysisDetailsBase(result) {
    analysisDetailsBase = `X: ${result.x_label}; Y: ${result.y_label}; fs: ${result.actual_fs.toPrecision(8)} Hz; точок: ${result.points}; сегментів: ${result.windows}; частотних ліній: ${result.frequency_bins}; діапазон: ${result.actual_start.toFixed(6)}–${result.actual_end.toFixed(6)} с`;
}

function renderVisualDetails(result) {
    const info = $("details");
    info.hidden = false;
    const unit = unitSuffix(result.value_unit);
    const formulaText = result.formula ? `; формула: ${result.formula}` : "";
    const gammaText = result.color_scale === "power" ? `, gamma=${compactNumber(result.gamma)}` : "";
    info.textContent = `${analysisDetailsBase}; Spectrum: ${result.spectrum_label}; Amplitude Peak max: ${compactNumber(result.amplitude_peak_max)} g; SXX: ${compactNumber(result.sxx_min)}…${compactNumber(result.sxx_max)} g²/Hz; результат: ${compactNumber(result.result_min)}…${compactNumber(result.result_max)}${unit}; шкала: ${compactNumber(result.vmin)}…${compactNumber(result.vmax)}${unit}; colors: ${result.color_scale}${gammaText}, cmap=${result.cmap}${formulaText}.`;
}

async function updateVisualization() {
    if (!analysisReady || !visualInputsValid()) return;

    try {
        setStatus("Оновлення спектра та кольорової шкали…", "working");
        const result = await apiCall("Spectrogramma.update_visual", visualPayload());
        showImage(result.image);
        updateScalePlaceholders(result.vmin, result.vmax);
        updateUnitLabels(result.value_unit);
        renderVisualDetails(result);
        const unit = unitSuffix(result.value_unit);
        setStatus(
            `${result.spectrum_label}: шкала ${compactNumber(result.vmin)}…${compactNumber(result.vmax)}${unit}; ${result.color_scale}, ${result.cmap}`,
            "success",
        );
    } catch (error) {
        setStatus(error.message, "error");
    }
}

function scheduleVisualUpdate() {
    if (!analysisReady) return;
    clearTimeout(visualUpdateTimer);
    visualUpdateTimer = setTimeout(updateVisualization, 500);
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

$("spectrum-type").addEventListener("change", () => {
    updateControlVisibility();
    scheduleVisualUpdate();
});
$("color-scale").addEventListener("change", () => {
    updateControlVisibility();
    scheduleVisualUpdate();
});
$("gamma").addEventListener("input", scheduleVisualUpdate);
$("cmap").addEventListener("change", scheduleVisualUpdate);
$("formula").addEventListener("input", scheduleVisualUpdate);
$("vmin").addEventListener("input", scheduleVisualUpdate);
$("vmax").addEventListener("input", scheduleVisualUpdate);

$("analyze").onclick = async () => {
    if (!visualInputsValid()) return;

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
            nperseg: $("nperseg").value,
            open_external: $("open-external").checked,
            ...visualPayload(),
        });
        showImage(result.image);
        updateScalePlaceholders(result.vmin, result.vmax);
        updateUnitLabels(result.value_unit);
        analysisReady = true;
        setAnalysisDetailsBase(result);
        renderVisualDetails(result);

        const unit = unitSuffix(result.value_unit);
        const notes = [];
        if (result.clipped) notes.push("Діапазон скорочено до доступних даних");
        if (result.warning) notes.push(result.warning);
        if (result.external_opened) notes.push("Відкрито інтерактивне вікно");
        notes.push(`Шкала ${compactNumber(result.vmin)}…${compactNumber(result.vmax)}${unit}`);
        notes.push(`${result.color_scale}, ${result.cmap}`);
        setStatus(
            `${result.spectrum_label} побудовано${notes.length ? `. ${notes.join(". ")}.` : "."}`,
            "success",
        );
    } catch (error) {
        setStatus(error.message, "error");
    } finally {
        setBusy(false);
    }
};

updateControlVisibility();
