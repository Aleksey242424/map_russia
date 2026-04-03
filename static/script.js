let map;               
let popupOverlay;       
let popupElement;       
let markerFeature;      
let vectorLayer;        

function initMap() {
    // Создаём карту
    map = new ol.Map({
        target: 'map',
        layers: [
            new ol.layer.Tile({
                source: new ol.source.OSM()  
            })
        ],
        view: new ol.View({
            center: ol.proj.fromLonLat([100, 64]), 
            zoom: 3
        })
    });

    popupElement = document.createElement('div');
    popupElement.className = 'ol-popup';
    popupOverlay = new ol.Overlay({
        element: popupElement,
        positioning: 'bottom-center',
        stopEvent: false,
        offset: [0, -10]
    });
    map.addOverlay(popupOverlay);

    vectorLayer = new ol.layer.Vector({
        source: new ol.source.Vector(),
        style: new ol.style.Style({
            image: new ol.style.Circle({
                radius: 7,
                fill: new ol.style.Fill({ color: '#cc3333' }),
                stroke: new ol.style.Stroke({ color: '#ffffff', width: 2 })
            })
        })
    });
    map.addLayer(vectorLayer);
}

function setMarkerAndPopup(lon, lat, htmlContent) {

    const source = vectorLayer.getSource();
    source.clear();
    

    const coordinate = ol.proj.fromLonLat([lon, lat]);
    const newMarker = new ol.Feature({
        geometry: new ol.geom.Point(coordinate)
    });
    source.addFeature(newMarker);
    

    popupElement.innerHTML = htmlContent;
    popupOverlay.setPosition(coordinate);
}

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
            document.getElementById('loadingHint').textContent = '✅ Годы загружены';
        } else {
            document.getElementById('loadingHint').textContent = '⚠️ Нет данных о годах';
        }
    } catch (err) {
        console.error(err);
        document.getElementById('loadingHint').textContent = '❌ Ошибка загрузки списка годов';
    }
}

async function updateForYear(year) {
    if (!year) {
        document.getElementById('tableBody').innerHTML = '<tr><td colspan="3">Выберите год</td></tr>';
        document.getElementById('totalInfo').innerHTML = 'Выберите год для отображения';
        vectorLayer.getSource().clear();
        popupOverlay.setPosition(undefined);
        return;
    }
    try {
        const resp = await fetch(`/api/data/${year}`);
        const data = await resp.json();
        if (data.error) {
            document.getElementById('tableBody').innerHTML = `<tr><td colspan="3">${data.error}</td></tr>`;
            document.getElementById('totalInfo').innerHTML = 'Ошибка загрузки';
            return;
        }
        const peoples = data.peoples || [];
        const totalPop = data.total_population;
        

        const tbody = document.getElementById('tableBody');
        tbody.innerHTML = '';
        peoples.forEach(p => {
            const row = tbody.insertRow();
            row.insertCell(0).textContent = p.name;
            row.insertCell(1).textContent = p.population.toFixed(1);
            row.insertCell(2).innerHTML = `${p.percentage.toFixed(1)}% <div class="percentage-bar" style="width: ${p.percentage * 1.5}%; max-width:100%;"></div>`;
        });
        if (peoples.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3">Нет данных по народам</td></tr>';
        }
        document.getElementById('totalInfo').innerHTML = `👥 Общая численность населения России в ${year} году: <strong>${totalPop.toFixed(1)} млн чел.</strong>`;
        
        const topPeople = peoples[0];
        const popupHtml = `
            <b>📅 ${year} год</b><br>
            👥 Население: ${totalPop.toFixed(1)} млн<br>
            🏆 Крупнейший народ: ${topPeople ? topPeople.name : '—'} (${topPeople ? topPeople.percentage.toFixed(1) : 0}%)
            <br><small>📍 Маркер в центре России</small>
        `;
        setMarkerAndPopup(100, 64, popupHtml);
    } catch (err) {
        console.error(err);
        document.getElementById('tableBody').innerHTML = '<tr><td colspan="3">Ошибка получения данных</td></tr>';
        document.getElementById('totalInfo').innerHTML = 'Ошибка сервера';
    }
}

document.getElementById('yearSelect').addEventListener('change', (e) => {
    const year = e.target.value;
    if (year) updateForYear(parseInt(year));
    else updateForYear(null);
});
window.addEventListener('DOMContentLoaded', () => {
    initMap();
    loadYears();
});
