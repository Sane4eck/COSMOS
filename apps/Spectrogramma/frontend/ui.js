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
<label>vmin<input id="vmin" type="number" step="any" placeholder="Auto"></label>
<label>vmax<input id="vmax" type="number" step="any" placeholder="Auto"></label>
<label class="wide">Формула відображення SXX<input id="formula" type="text" spellcheck="false" list="formula-presets" value="10 * log10(sxx + 1e-9)"></label>
<label class="wide">Кількість точок у сегменті<input id="nperseg" type="number" min="2" max="1000000" value="1000"></label>
</div>
<datalist id="formula-presets">
<option value="10 * log10(sxx + 1e-9)"></option>
<option value="10 * log10(sxx + 1e-10)"></option>
<option value="sxx"></option>
<option value="sqrt(sxx)"></option>
<option value="20 * log10(sqrt(sxx) + 1e-9)"></option>
</datalist>
<p class="hint">Формула застосовується до лінійної матриці sxx після FFT. Доступні: log10, log/ln, sqrt, abs, clip, exp, minimum, maximum, power; можна писати також np.log10, np.sqrt тощо. Зміна формули або vmin/vmax перемальовує графік без повторного FFT.</p>
<p class="hint">vmin/vmax задають межі кольорової шкали. Порожнє поле = Auto.</p>
<label class="check"><input id="open-external" type="checkbox" checked> Також відкрити інтерактивний графік в окремому вікні</label>
<p class="hint">В окремому вікні доступні zoom, pan і збереження. Клацніть по спектрограмі, щоб отримати час, RPM та значення вибраної формули.</p>
<button id="analyze" class="primary" disabled>Запустити аналіз</button>
<div id="status" class="status">Очікування файлу</div>
<div id="details" class="details" hidden></div>
</section>
<section class="preview card"><div id="placeholder">Спектрограма з’явиться тут</div><img id="spectrogram-image" alt="Спектрограма" hidden></section>`;
document.getElementById("app").className = "page";
