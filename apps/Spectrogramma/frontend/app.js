let selectedPath = "";

function fillSelect(select, items, selectedId) {
    select.innerHTML = "";
    for (const item of items) {
        select.add(new Option(item.label, item.id, false, item.id === selectedId));
    }
    select.disabled = items.length === 0;
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

$("analyze").onclick = async () => {
    setBusy(true);
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
        });
        const image = $("spectrogram-image");
        image.src = result.image;
        image.hidden = false;
        $("placeholder").hidden = true;
        const info = $("details");
        info.hidden = false;
        info.textContent = `X: ${result.x_label}; Y: ${result.y_label}; fs: ${result.actual_fs.toPrecision(8)} Hz; точок: ${result.points}; сегментів: ${result.windows}; частотних ліній: ${result.frequency_bins}; діапазон: ${result.actual_start.toFixed(6)}–${result.actual_end.toFixed(6)} с.`;
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
