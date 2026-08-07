let selectedPath = "";
let analysisReady = false;
let scaleUpdateTimer = null;

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

function scalePayload() {
    return {
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

async function updateColorScale() {
    if (!analysisReady || !scaleInputsValid()) return;

    try {
        setStatus("Оновлення кольорової шкали…", "working");
        const result = await apiCall("Spectrogramma.update_scale", scalePayload());
        showImage(result.image);
        updateScalePlaceholders(result.vmin, result.vmax);
        setStatus(
            `Кольорову шкалу оновлено: ${Number(result.vmin).toFixed(2)}…${Number(result.vmax).toFixed(2)} дБ/Гц`,
            "success",
        );
    } catch (error) {
        setStatus(error.message, "error");
    }
}

function scheduleColorScaleUpdate() {
    if (!analysisReady) return;
    clearTimeout(scaleUpdateTimer);
    scaleUpdateTimer = setTimeout(updateColorScale, 450);
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
$("vmin").addEventListener("input", scheduleColorScaleUpdate);
$("vmax").addEventListener("input", scheduleColorScaleUpdate);

$("analyze").onclick = async () => {
    if (!scaleInputsValid()) return;

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
            vmin: $("vmin").value.trim(),
            vmax: $("vmax").value.trim(),
            nperseg: $("nperseg").value,
            open_external: $("open-external").checked,
        });
        showImage(result.image);
        updateScalePlaceholders(result.vmin, result.vmax);
        analysisReady = true;

        const info = $("details");
        info.hidden = false;
        info.textContent = `X: ${result.x_label}; Y: ${result.y_label}; fs: ${result.actual_fs.toPrecision(8)} Hz; точок: ${result.points}; сегментів: ${result.windows}; частотних ліній: ${result.frequency_bins}; діапазон: ${result.actual_start.toFixed(6)}–${result.actual_end.toFixed(6)} с; шкала: ${Number(result.vmin).toFixed(2)}…${Number(result.vmax).toFixed(2)} дБ/Гц.`;
        const notes = [];
        if (result.clipped) notes.push("Діапазон скорочено до доступних даних");
        if (result.warning) notes.push(result.warning);
        if (result.external_opened) notes.push("Відкрито інтерактивне вікно");
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
