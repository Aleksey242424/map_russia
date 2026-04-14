let map;
let regionsLayer = null;        // векторный слой регионов
let markerLayer = null;         // слой с маркером (точка)
let currentYear = null;
let currentPeople = null;
let ethnicData = {};            // { "Регион": процент }
let availablePeoples = [];      // список народов из текущего года
// ---------- Инициализация карты OpenLayers ----------
function initMap() {
    map = new ol.Map({
        target: 'map',
        layers: [
            new ol.layer.Tile({
                source: new ol.source.OSM()
            })
        ],
        view: new ol.View({
            center: ol.proj.fromLonLat([100, 64]),
            zoom: 3,
            minZoom: 2,
            maxZoom: 10
        })
    });
    // Добавим слой для маркера (красная точка в центре)
    markerLayer = new ol.layer.Vector({
        source: new ol.source.Vector(),
        style: new ol.style.Style({
            image: new ol.style.Circle({
                radius: 8,
                fill: new ol.style.Fill({ color: '#cc3333' }),
                stroke: new ol.style.Stroke({ color: '#ffffff', width: 2 })
            })
        })
    });
    map.addLayer(markerLayer);
}
// Установить маркер и попап (можно использовать стандартный оверлей)
function setMarker(lon, lat, message) {
    const source = markerLayer.getSource();
    source.clear();
    const coord = ol.proj.fromLonLat([lon, lat]);
    const feature = new ol.Feature({ geometry: new ol.geom.Point(coord) });
    source.addFeature(feature);
    // простой попап через обычный alert или можно через оверлей, но для простоты не загромождаем
}
// ---------- Загрузка списка годов ----------
async function loadYears() {
    try {
        const resp = await fetch('/api/years');
        const data = await resp.json();
        const select = document.getElementById('yearSelect');
        select.innerHTML = '<option value="">-- Выберите год --</option>';
        if (data.years && data.years.length) {
            data.years.sort((a,b)=>a-b);
            data.years.forEach(year => {
                const option = document.createElement('option');
                option.value = year;
                option.textContent = `${year} год`;
                select.appendChild(option);
            });
        } else {
            select.innerHTML = '<option value="">Нет данных</option>';
        }
    } catch (err) {
        console.error(err);
        document.getElementById('yearSelect').innerHTML = '<option value="">Ошибка загрузки</option>';
    }
}
// Загрузка данных по году (таблица + обновление списка народов)
async function loadYearData(year) {
    try {
        const resp = await fetch(`/api/data/${year}`);
        if (!resp.ok) throw new Error('Данные не найдены');
        const data = await resp.json();
        // отобразить таблицу
        const tbody = document.getElementById('tableBody');
        tbody.innerHTML = '';
        const peoplesList = [];
        for (let p of data.peoples) {
            const row = tbody.insertRow();
            row.insertCell(0).textContent = p.name;
            row.insertCell(1).textContent = p.population.toFixed(1);
            const percCell = row.insertCell(2);
            percCell.innerHTML = `${p.percentage.toFixed(1)}% <div class="perc-bar"><div class="perc-fill" style="width: ${Math.min(p.percentage * 1.2, 100)}%;"></div></div>`;
            peoplesList.push(p.name);
        }
        document.getElementById('totalInfo').innerHTML = `👥 Общая численность: <strong>${data.total_population.toFixed(1)} млн чел.</strong> (${year} г.)`;
        availablePeoples = peoplesList;
        // обновить select народов
        const peopleSelect = document.getElementById('peopleSelect');
        peopleSelect.disabled = false;
        peopleSelect.innerHTML = '<option value="">-- Выберите народ --</option>';
        availablePeoples.forEach(name => {
            const opt = document.createElement('option');
            opt.value = name;
            opt.textContent = name;
            peopleSelect.appendChild(opt);
        });
        // сбросить текущий выбранный народ
        currentPeople = null;
        // маркер с краткой информацией
        const topPeople = data.peoples[0];
        setMarker(100, 64, `${year} г. | ${topPeople.name} ${topPeople.percentage}%`);
    } catch (err) {
        console.error(err);
        document.getElementById('tableBody').innerHTML = '<tr><td colspan="3">Ошибка загрузки</td></tr>';
        document.getElementById('totalInfo').innerHTML = 'Ошибка сервера';
        document.getElementById('peopleSelect').disabled = true;
    }
}
// ---------- Загрузка геоданных регионов (границы) ----------
async function loadRegionsLayer() {
    // Проверяем, существует ли эндпоинт /api/regions/geojson, если нет – выходим
    try {
        const testResp = await fetch('/api/regions/geojson', { method: 'HEAD' });
        if (!testResp.ok) {
            console.warn('Эндпоинт границ регионов не найден, хороплет недоступен');
            return;
        }
    } catch(e) {
        console.warn('Нет данных границ регионов');
        return;
    }
    const source = new ol.source.Vector({
        url: '/api/regions/geojson',
        format: new ol.format.GeoJSON()
    });
    regionsLayer = new ol.layer.Vector({
        source: source,
        style: function(feature) {
            // стиль по умолчанию (пока нет этнических данных)
            const regionName = feature.get('name') || feature.get('admin_name') || feature.get('region') || '';
            let percentage = ethnicData[regionName] !== undefined ? ethnicData[regionName] : -1;
            let color = '#aaaaaa'; // нет данных
            if (percentage >= 0) {
                if (percentage > 15) color = '#d73027';
                else if (percentage > 5) color = '#fc8d59';
                else if (percentage > 1) color = '#fee090';
                else color = '#e0f3f8';
            }
            return new ol.style.Style({
                fill: new ol.style.Fill({ color: color }),
                stroke: new ol.style.Stroke({ color: '#ffffff', width: 1.2 })
            });
        },
        zIndex: 1
    });
    map.addLayer(regionsLayer);
}
// Загрузка этнических данных для выбранного года и народа (хороплет)
async function loadEthnicData(year, people) {
    if (!year || !people) return;
    try {
        const resp = await fetch(`/api/regions/ethnicity?year=${year}&people=${encodeURIComponent(people)}`);
        if (!resp.ok) {
            console.warn('Этнические данные не найдены');
            ethnicData = {};
            return;
        }
        const data = await resp.json(); // ожидаем объект { "Регион": процент }
        ethnicData = data;
        // обновить стиль слоя регионов, если он существует
        if (regionsLayer) {
            regionsLayer.setStyle(function(feature) {
                const regionName = feature.get('name') || feature.get('admin_name') || feature.get('region') || '';
                let percentage = ethnicData[regionName] !== undefined ? ethnicData[regionName] : -1;
                let color = '#aaaaaa';
                if (percentage >= 0) {
                    if (percentage > 15) color = '#d73027';
                    else if (percentage > 5) color = '#fc8d59';
                    else if (percentage > 1) color = '#fee090';
                    else color = '#e0f3f8';
                }
                return new ol.style.Style({
                    fill: new ol.style.Fill({ color: color }),
                    stroke: new ol.style.Stroke({ color: '#ffffff', width: 1.2 })
                });
            });
            regionsLayer.changed();
        }
    } catch (err) {
        console.error('Ошибка загрузки хороплета', err);
        ethnicData = {};
    }
}
// ---------- Обработчики событий ----------
document.getElementById('yearSelect').addEventListener('change', async (e) => {
    const year = e.target.value;
    if (!year) return;
    currentYear = parseInt(year);
    await loadYearData(currentYear);
    // сбросить хороплет, очистить ethnicData
    ethnicData = {};
    if (regionsLayer) regionsLayer.changed();
    document.getElementById('peopleSelect').value = '';
    currentPeople = null;
});
document.getElementById('applyChoroplethBtn').addEventListener('click', async () => {
    const people = document.getElementById('peopleSelect').value;
    if (!currentYear) {
        alert('Сначала выберите год');
        return;
    }
    if (!people) {
        alert('Выберите народ для отображения на карте');
        return;
    }
    currentPeople = people;
    // Загружаем этнические данные по регионам
    await loadEthnicData(currentYear, currentPeople);
});
// ---------- Инициализация приложения ----------
window.addEventListener('DOMContentLoaded', async () => {
    initMap();
    await loadYears();
    // Пытаемся загрузить слой регионов (если есть)
    await loadRegionsLayer();
    // Установим маркер по умолчанию
    setMarker(100, 64, 'Выберите год');
});