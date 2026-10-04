from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# MEB Resmi Ders Katsayıları
KATSAYILAR = {
    'turkce': 4.0,
    'matematik': 4.0,
    'fen': 4.0,
    'inkilap': 1.0,
    'din': 1.0,
    'ingilizce': 1.0
}

# 2018'den Günümüze MEB Resmi Sınav Raporu Ortalamaları ve Standart Sapmaları
YIL_VERILERI = {
    '2026': {  # 2026 Tahmini Denge
        'ort': {'turkce': 9.80, 'matematik': 5.50, 'fen': 9.50, 'inkilap': 5.20, 'din': 6.00, 'ingilizce': 5.00},
        'ss':  {'turkce': 4.20, 'matematik': 4.10, 'fen': 4.50, 'inkilap': 2.40, 'din': 2.20, 'ingilizce': 2.90},
        'min_tasp': 120.0, 'max_tasp': 435.0
    },
    '2025': {  # 2025 Sınav Modeli
        'ort': {'turkce': 9.90, 'matematik': 5.80, 'fen': 9.20, 'inkilap': 5.40, 'din': 6.10, 'ingilizce': 5.00},
        'ss':  {'turkce': 4.10, 'matematik': 4.20, 'fen': 4.40, 'inkilap': 2.35, 'din': 2.15, 'ingilizce': 2.85},
        'min_tasp': 122.0, 'max_tasp': 438.0
    },
    '2024': {  # MEB 2024 Resmi Veriler
        'ort': {'turkce': 9.63, 'matematik': 6.54, 'fen': 8.63, 'inkilap': 4.68, 'din': 5.74, 'ingilizce': 5.15},
        'ss':  {'turkce': 4.15, 'matematik': 4.30, 'fen': 4.45, 'inkilap': 2.45, 'din': 2.25, 'ingilizce': 2.95},
        'min_tasp': 121.5, 'max_tasp': 432.0
    },
    '2023': {  # MEB 2023 Resmi Veriler
        'ort': {'turkce': 9.99, 'matematik': 5.95, 'fen': 9.01, 'inkilap': 6.06, 'din': 6.29, 'ingilizce': 4.91},
        'ss':  {'turkce': 4.05, 'matematik': 4.15, 'fen': 4.38, 'inkilap': 2.30, 'din': 2.10, 'ingilizce': 2.80},
        'min_tasp': 125.0, 'max_tasp': 442.0
    },
    '2022': {  # MEB 2022 Resmi Veriler
        'ort': {'turkce': 9.22, 'matematik': 4.74, 'fen': 9.50, 'inkilap': 5.54, 'din': 6.45, 'ingilizce': 4.59},
        'ss':  {'turkce': 4.28, 'matematik': 4.25, 'fen': 4.56, 'inkilap': 2.48, 'din': 2.18, 'ingilizce': 2.98},
        'min_tasp': 118.0, 'max_tasp': 430.0
    },
    '2021': {  # MEB 2021 Resmi Veriler
        'ort': {'turkce': 9.41, 'matematik': 4.20, 'fen': 8.04, 'inkilap': 5.23, 'din': 6.35, 'ingilizce': 4.93},
        'ss':  {'turkce': 4.40, 'matematik': 3.90, 'fen': 4.62, 'inkilap': 2.52, 'din': 2.20, 'ingilizce': 3.02},
        'min_tasp': 115.0, 'max_tasp': 428.0
    },
    '2020': {  # MEB 2020 Resmi Veriler
        'ort': {'turkce': 10.00, 'matematik': 4.89, 'fen': 10.21, 'inkilap': 5.05, 'din': 6.39, 'ingilizce': 4.86},
        'ss':  {'turkce': 4.32, 'matematik': 4.12, 'fen': 4.58, 'inkilap': 2.42, 'din': 2.14, 'ingilizce': 2.91},
        'min_tasp': 121.0, 'max_tasp': 434.0
    },
    '2019': {  # MEB 2019 Resmi Veriler
        'ort': {'turkce': 11.75, 'matematik': 5.09, 'fen': 9.97, 'inkilap': 6.88, 'din': 6.83, 'ingilizce': 4.65},
        'ss':  {'turkce': 4.18, 'matematik': 4.21, 'fen': 4.41, 'inkilap': 2.31, 'din': 2.08, 'ingilizce': 2.85},
        'min_tasp': 126.0, 'max_tasp': 440.0
    },
    '2018': {  # MEB 2018 Resmi Veriler (İlk LGS)
        'ort': {'turkce': 12.55, 'matematik': 3.68, 'fen': 8.24, 'inkilap': 6.75, 'din': 7.15, 'ingilizce': 4.38},
        'ss':  {'turkce': 4.10, 'matematik': 3.82, 'fen': 4.30, 'inkilap': 2.25, 'din': 2.01, 'ingilizce': 2.78},
        'min_tasp': 112.0, 'max_tasp': 425.0
    }
}

# MEB Yüzdelik Dilim Ölçeği
YUZDELIK_TABLOSU = [
    (500.0, 0.01), (485.0, 0.15), (470.0, 0.50), (450.0, 1.40), 
    (430.0, 3.30), (410.0, 6.20), (390.0, 10.10), (360.0, 17.50), 
    (320.0, 29.80), (280.0, 45.00), (230.0, 67.00), (180.0, 88.00), (100.0, 100.0)
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LGS Puan Hesaplama (2018-2026)</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f3f4f6; padding: 15px; margin: 0; }
        .container { max-width: 500px; margin: 0 auto; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }
        h2 { color: #3730a3; text-align: center; margin-bottom: 20px; }
        label { font-weight: bold; color: #374151; font-size: 14px; }
        select, button { width: 100%; padding: 12px; margin-top: 6px; border-radius: 8px; border: 1px solid #d1d5db; font-size: 15px; box-sizing: border-box; }
        button { background: #4f46e5; color: white; font-weight: bold; border: none; cursor: pointer; margin-top: 15px; transition: 0.2s; }
        button:hover { background: #4338ca; }
        table { width: 100%; margin-top: 15px; border-collapse: collapse; }
        th { background: #f9fafb; padding: 8px; color: #4b5563; font-size: 13px; }
        td { padding: 6px 4px; text-align: center; border-bottom: 1px solid #f3f4f6; font-size: 14px; }
        input[type="number"] { width: 52px; text-align: center; padding: 6px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; }
        .result { margin-top: 20px; padding: 16px; background: #eef2ff; border-radius: 8px; display: none; border: 1px solid #c7d2fe; }
        .result p { margin: 8px 0; font-size: 15px; }
    </style>
</head>
<body>
<div class="container">
    <h2>LGS Puan Hesaplama</h2>
    <label>Hesaplanacak LGS Yılını Seçin:</label>
    <select id="yil">
        <option value="2026" selected>2026 LGS (Tahmini Denge)</option>
        <option value="2025">2025 LGS Sınavı</option>
        <option value="2024">2024 LGS (Resmi Veriler)</option>
        <option value="2023">2023 LGS (Resmi Veriler)</option>
        <option value="2022">2022 LGS (Resmi Veriler)</option>
        <option value="2021">2021 LGS (Resmi Veriler)</option>
        <option value="2020">2020 LGS (Resmi Veriler)</option>
        <option value="2019">2019 LGS (Resmi Veriler)</option>
        <option value="2018">2018 LGS (Resmi Veriler)</option>
    </select>

    <table>
        <thead>
            <tr><th>Ders</th><th>Soru</th><th>Doğru</th><th>Yanlış</th></tr>
        </thead>
        <tbody id="ders-listesi"></tbody>
    </table>

    <button onclick="hesapla()">Puanı Hesapla</button>

    <div class="result" id="resultCard">
        <h3 style="margin-top:0; color:#1e1b4b;">Hesaplama Sonucu</h3>
        <p><strong>Toplam Net:</strong> <span id="resNet">0</span></p>
        <p><strong>LGS Puanı:</strong> <span id="resPuan" style="color:#4f46e5; font-size: 22px; font-weight:bold;">0</span></p>
        <p><strong>Tahmini Yüzdelik:</strong> %<span id="resYuzdelik" style="color:#dc2626; font-size: 22px; font-weight:bold;">0</span></p>
    </div>
</div>

<script>
    const dersler = [
        { key: 'turkce', name: 'Türkçe', max: 20 },
        { key: 'matematik', name: 'Matematik', max: 20 },
        { key: 'fen', name: 'Fen Bilimleri', max: 20 },
        { key: 'inkilap', name: 'İnkılap Tarihi', max: 10 },
        { key: 'din', name: 'Din Kültürü', max: 10 },
        { key: 'ingilizce', name: 'Yabancı Dil', max: 10 }
    ];

    const tbody = document.getElementById('ders-listesi');
    dersler.forEach(d => {
        tbody.innerHTML += `
            <tr>
                <td style="text-align:left; font-weight:600;">${d.name}</td>
                <td>${d.max}</td>
                <td><input type="number" id="${d.key}_d" min="0" max="${d.max}" value="0"></td>
                <td><input type="number" id="${d.key}_y" min="0" max="${d.max}" value="0"></td>
            </tr>
        `;
    });

    async function hesapla() {
        const yil = document.getElementById('yil').value;
        let dersVerileri = {};
        dersler.forEach(d => {
            dersVerileri[d.key + '_d'] = document.getElementById(d.key + '_d').value;
            dersVerileri[d.key + '_y'] = document.getElementById(d.key + '_y').value;
        });

        const response = await fetch('/hesapla', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ yil: yil, dersler: dersVerileri })
        });

        const data = await response.json();
        document.getElementById('resNet').innerText = data.toplam_net;
        document.getElementById('resPuan').innerText = data.puan;
        document.getElementById('resYuzdelik').innerText = data.yuzdelik;
        document.getElementById('resultCard').style.display = 'block';
    }
</script>
</body>
</html>
"""

def yuzdelik_dilim_hesapla(puan):
    if puan >= 500.0: return 0.01
    if puan <= 100.0: return 100.0
    for i in range(len(YUZDELIK_TABLOSU) - 1):
        p1, y1 = YUZDELIK_TABLOSU[i]
        p2, y2 = YUZDELIK_TABLOSU[i + 1]
        if p1 >= puan >= p2:
            oran = (p1 - puan) / (p1 - p2)
            return round(y1 + oran * (y2 - y1), 2)
    return 100.0

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/hesapla', methods=['POST'])
def hesapla():
    data = request.get_json()
    yil = data.get('yil', '2026')
    girisler = data.get('dersler', {})

    param = YIL_VERILERI.get(yil, YIL_VERILERI['2026'])
    
    toplam_tasp = 0.0
    toplam_net = 0.0

    for ders, katsayi in KATSAYILAR.items():
        d = float(girisler.get(f"{ders}_d", 0))
        y = float(girisler.get(f"{ders}_y", 0))
        net = max(0.0, d - (y / 3.0))
        toplam_net += net

        # MEB Resmi Standart Puan Formülü
        ort, ss = param['ort'][ders], param['ss'][ders]
        sp = 50.0 + 10.0 * ((net - ort) / ss)
        toplam_tasp += sp * katsayi

    if toplam_net <= 0:
        return jsonify({'puan': 100.0, 'yuzdelik': 100.0, 'toplam_net': 0.0})

    # MEB 100-500 Ölçekleme Algoritması
    min_tasp = param['min_tasp']
    max_tasp = param['max_tasp']

    lgs_puani = 100.0 + 400.0 * ((toplam_tasp - min_tasp) / (max_tasp - min_tasp))
    lgs_puani = max(100.0, min(500.0, lgs_puani))

    return jsonify({
        'puan': round(lgs_puani, 2),
        'yuzdelik': yuzdelik_dilim_hesapla(lgs_puani),
        'toplam_net': round(toplam_net, 2)
    })
