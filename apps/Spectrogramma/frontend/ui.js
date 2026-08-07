document.getElementById("app").innerHTML = `
<section class="controls card">
<h2>Аналіз спектрограми вібрацій</h2>
<div class="file-row"><button id="choose-file" class="primary">Обрати Excel або TDMS</button><div id="file-path" class="file-path">Файл не вибрано</div></div>
<div class="fields axes">
<label>Вісь X<select id="x-axis" disabled></select></label>
<label>Вісь Y<select id="y-axis" disabled></select></label>
</div>
<div class="fields">
<label>Частота запису, Hz<input id="fs" type="number" min="0.000001" step="any" value="2500"></label>
<label>Початок, с<input id="start-sec" type="number" step="any" value="0"></label>
<label>Тривалість, с<input id="duration-sec" type="number" min="0.000001" step="any" value="300"></label>
<label>Y max, тис. RPM<input id="y-max" type="number" min="0.001" step="any" value="30"></label>

<label>Тип спектра<select id="spectrum-type">
<option value="amplitude_peak" selected>Amplitude Peak [g]</option>
<option value="amplitude_rms">Amplitude RMS [g RMS]</option>
<option value="psd">PSD [g²/Hz]</option>
<option value="asd">ASD [g/√Hz]</option>
<option value="psd_db">PSD dB</option>
<option value="custom">Custom Formula</option>
</select></label>
<label>Color scale<select id="color-scale">
<option value="linear">Linear</option>
<option value="power" selected>Power</option>
<option value="log">Log</option>
</select></label>
<label id="gamma-field">Gamma<input id="gamma" type="number" min="0.000001" step="any" value="0.5"></label>
<label>Colormap<select id="cmap">
<option value="turbo" selected>turbo</option>
<option value="viridis">viridis</option>
<option value="plasma">plasma</option>
<option value="inferno">inferno</option>
<option value="magma">magma</option>
<option value="nipy_spectral">nipy_spectral</option>
<option value="jet">jet</option>
</select></label>
<label><span id="vmin-label">vmin [g]</span><input id="vmin" type="number" step="any" value="0" placeholder="Auto"></label>
<label><span id="vmax-label">vmax [g]</span><input id="vmax" type="number" step="any" value="30" placeholder="Auto"></label>
<label class="wide" id="custom-formula-field" hidden>Формула відображення SXX<input id="formula" type="text" spellcheck="false" list="formula-presets" value="10 * log10(sxx + 1e-9)"></label>
<label class="wide">Кількість точок у сегменті<input id="nperseg" type="number" min="2" max="1000000" value="1000"></label>
</div>
<datalist id="formula-presets">
<option value="10 * log10(sxx + 1e-9)"></option>
<option value="sxx_db = 10 * np.log10(sxx + 1e-10)"></option>
<option value="sxx"></option>
<option value="sqrt(sxx)"></option>
<option value="20 * log10(sqrt(sxx) + 1e-9)"></option>
</datalist>
<p class="hint">Amplitude Peak — одностороння амплітуда FFT-bin з компенсацією Hann window. Якщо вхідний сигнал у g, шкала також у g peak. Amplitude RMS = Peak / √2.</p>
<p class="hint">vmin/vmax, Color scale, Gamma та Colormap змінюють тільки відображення кольорів і не змінюють фізичні значення спектра. Power/Log залишають colorbar у реальних одиницях вибраного режиму.</p>
<p class="hint" id="custom-formula-hint" hidden>Custom Formula застосовується до існуючого SXX без повторного FFT. Доступні: log10, log/ln, sqrt, abs, clip, exp, minimum, maximum, power та відповідні np.* функції.</p>
<label class="check"><input id="open-external" type="checkbox" checked> Також відкрити інтерактивний графік в окремому вікні</label>
<p class="hint">В окремому вікні доступні zoom, pan і збереження. Клацніть по спектрограмі, щоб отримати час, RPM та фізичне значення FFT-bin.</p>
<button id="analyze" class="primary" disabled>Запустити аналіз</button>
<div id="status" class="status">Очікування файлу</div>
<div id="details" class="details" hidden></div>
</section>
<section class="preview card"><div id="placeholder">Спектрограма з’явиться тут</div><img id="spectrogram-image" alt="Спектрограма" hidden></section>`;
document.getElementById("app").className = "page";
