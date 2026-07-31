let selectedPath = "";

$("choose-file").onclick = async () => {
    try {
        const result = await apiCall("Spectrogramma.choose_excel");
        if (!result.path) return;
        selectedPath = result.path;
        $("file-path").textContent = result.path;
        setStatus("Excel-файл вибрано", "success");
    } catch (error) {
        setStatus(error.message, "error");
    }
};

$("analyze").onclick = async () => {
    setBusy(true);
    setStatus("Формування спектрограми…", "working");
    try {
        const result = await apiCall("Spectrogramma.analyze", {
            path: selectedPath,
            column_name: $("column-name").value,
            fs: $("fs").value,
            start_sec: $("start-sec").value,
            duration_sec: $("duration-sec").value,
            y_max: $("y-max").value,
            nperseg: $("nperseg").value,
        });
        const image = $("spectrogram-image");
        image.src = result.image;
        image.hidden = false;
        $("placeholder").hidden = true;
        const info = $("details");
        info.hidden = false;
        info.textContent = `Точок: ${result.points}; сегментів: ${result.windows}; частотних ліній: ${result.frequency_bins}; діапазон: ${result.actual_start.toFixed(3)}–${result.actual_end.toFixed(3)} с.`;
        const note = result.clipped ? " Діапазон скорочено до доступних даних." : "";
        setStatus(`Спектрограму побудовано.${note}`, "success");
    } catch (error) {
        setStatus(error.message, "error");
    } finally {
        setBusy(false);
    }
};
