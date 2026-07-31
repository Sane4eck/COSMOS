document.getElementById("app").innerHTML = `
<section class="controls card">
<h2>Аналіз спектрограми вібрацій</h2>
<button id="choose-file" class="primary">Обрати файл Excel</button>
<div id="file-path" class="file-path">Файл не вибрано</div>
<label>Назва колонки<input id="column-name" value="VKD1 g"></label>
<div class="fields">
<label>Частота запису, Hz<input id="fs" type="number" min="1000" max="40000" value="2500"></label>
<label>Початок, с<input id="start-sec" type="number" min="0" max="100000" value="0"></label>
<label>Тривалість, с<input id="duration-sec" type="number" min="1" max="100000" value="300"></label>
<label>Y max<input id="y-max" type="number" min="1" max="1000" value="30"></label>
<label class="wide">Кількість точок у сегменті<input id="nperseg" type="number" min="100" max="100000" value="1000"></label>
</div>
<button id="analyze" class="primary">Запустити аналіз</button>
<div id="status" class="status">Очікування файлу</div>
<div id="details" class="details" hidden></div>
</section>
<section class="preview card">
<div id="placeholder">Спектрограма з’явиться тут</div>
<img id="spectrogram-image" alt="Спектрограма" hidden>
</section>`;
document.getElementById("app").className = "page";
