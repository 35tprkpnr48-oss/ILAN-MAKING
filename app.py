from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# MEB LGS Ders Katsayıları
KATSAYILAR = {'turkce': 4, 'matematik': 4, 'fen': 4, 'inkilap': 1, 'din': 1, 'ingilizce': 1}

# Yaklaşık Ortalama ve Standart Sapmalar
YIL_PARAMETRELERI = {
    '2018': {'ort': {'turkce': 16.48, 'matematik': 6.99, 'fen': 13.05, 'inkilap': 9.26, 'din': 9.72, 'ingilizce': 7.70}, 'ss': {'turkce': 3.55, 'matematik': 4.12, 'fen': 4.38, 'inkilap': 1.68, 'din': 1.05, 'ingilizce': 2.78}},
    '2019': {'ort': {'turkce': 11.75, 'matematik': 5.09, 'fen': 9.97, 'inkilap': 6.88, 'din': 6.83, 'ingilizce': 4.65}, 'ss': {'turkce': 3.68, 'matematik': 3.92, 'fen': 4.21, 'inkilap': 2.11, 'din': 2.05, 'ingilizce': 2.85}},
    '2020': {'ort': {'turkce': 10.00, 'matematik': 4.89, 'fen': 10.21, 'inkilap': 5.05, 'din': 6.39, 'ingilizce': 4.86}, 'ss': {'turkce': 4.11, 'matematik': 3.88, 'fen': 4.50, 'inkilap': 2.45, 'din': 2.22, 'ingilizce': 2.92}},
    '2021': {'ort': {'turkce': 9.41, 'matematik': 4.20, 'fen': 9.93, 'inkilap': 5.23, 'din': 6.35, 'ingilizce': 4.93}, 'ss': {'turkce': 3.90, 'matematik': 3.52, 'fen': 4.31, 'inkilap': 2.38, 'din': 2.15, 'ingilizce': 2.88}},
    '2022': {'ort': {'turkce': 9.12, 'matematik': 4.74, 'fen': 9.50, 'inkilap': 5.54, 'din': 6.45, 'ingilizce': 4.59}, 'ss': {'turkce': 4.02, 'matematik': 3.75, 'fen': 4.41, 'inkilap': 2.40, 'din': 2.18, 'ingilizce': 2.90}},
    '2023': {'ort': {'turkce': 12.01, 'matematik': 5.95, 'fen': 11.23, 'inkilap': 6.55, 'din': 7.10, 'ingilizce': 5.30}, 'ss': {'turkce': 3.85, 'matematik': 4.10, 'fen': 4.15, 'inkilap': 2.20, 'din': 1.98, 'ingilizce': 2.80}},
    '2024': {'ort': {'turkce': 10.15, 'matematik': 4.60, 'fen': 10.10, 'inkilap': 5.32, 'din': 6.25, 'ingilizce': 4.80}, 'ss': {'turkce': 3.95, 'matematik': 3.65, 'fen': 4.35, 'inkilap': 2.35, 'din': 2.10, 'ingilizce': 2.85}},
    '2025': {'ort': {'turkce': 10.30, 'matematik': 4.75, 'fen': 10.25, 'inkilap': 5.40, 'din': 6.30, 'ingilizce': 4.85}, 'ss': {'turkce': 3.92, 'matematik': 3.70, 'fen': 4.30, 'inkilap': 2.30, 'din': 2.12, 'ingilizce': 2.83}},
    '2026': {'ort': {'turkce': 10.20, 'matematik': 4.68, 'fen': 10.18, 'inkilap': 5.38, 'din': 6.28, 'ingilizce': 4.82}, 'ss': {'turkce': 3.94, 'matematik': 3.68, 'fen': 4.32, 'inkilap': 2.33, 'din': 2.11, 'ingilizce': 2.84}}
}

YUZDELIK_TABLOSU = [
    (500, 0.01), (480, 0.25), (460, 0.85), (440, 2.10), (420, 4.30),
    (400, 7.80), (380, 12.50), (350, 21.00), (300, 38.50), (250, 60.00),
    (200, 81.00), (150, 94.00), (100, 100.00)
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LGS Puan Hesaplama</title>
    <style>
        body { font-family: sans-serif; background: #f3f4f6; padding: 15px; margin: 0; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h2 { color: #4f46e5; text-align: center; }
        select, button { width: 100%; padding: 12px; margin-top: 10px; border-radius: 5px; border: 1px solid #ccc; font-size: 16px; }
        button { background: #4f46e5; color: white; font-weight: bold; border: none; cursor: pointer; }
        table { width: 100%; margin-top: 15px; border-collapse: collapse; }
        th, td { padding: 8px; text-align: center; border-bottom: 1px solid #ddd; }
        input[type="number"] { width: 50px; text-align: center; padding: 5px; }
        .result { margin-top: 20px; padding: 15px; background: #eef2ff; border-radius: 5px; display: none; }
    </style>
</head>
<body>
<div class="container">
    <h2>LGS Puan Hesaplama</h2>
    <label>LGS Yılını Seçin:</label>
    <select id="yil">
        <option value="2026" selected>2026 LGS</option>
        <option value="2025">2025 LGS</option>
        <option value="2024">2024 LGS</option>
        <option value="2023">2023 LGS</option>
        <option value="2022">2022 LGS</option>
        <option value="2021">2021 LGS</option>
        <option value="2020">2020 LGS</option>
        <option value="2019">2019 LGS</option>
        <option value="2018">2018 LGS</option>
    </select>

    <table>
        <thead>
            <tr><th>Ders</th><th>Soru</th><th>Doğru</th><th>Yanlış</th></tr>
        </thead>
        <tbody id="ders-listesi"></tbody>
    </table>

    <button onclick="hesapla()">Hesapla</button>

    <div class="result" id="resultCard">
        <h3>Hesaplama Sonucu</h3>
        <p><strong>Toplam Net:</strong> <span id="resNet">0</span></p>
        <p><strong>LGS Puanı:</strong> <span id="resPuan" style="color:blue; font-size: 20px;">0</span></p>
        <p><strong>Tahmini Yüzdelik:</strong> %<span id="resYuzdelik" style="color:red; font-size: 20px;">0</span></p>
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
                <td><strong>${d.name}</strong></td>
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
    if puan >= 500: return 0.01
    if puan <= 100: return 100.0
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

    param = YIL_PARAMETRELERI.get(yil, YIL_PARAMETRELERI['2026'])
    
    # MEB Standart Puan Hesaplama Modeli
    toplam_asp = 0
    toplam_net = 0

    for ders, katsayi in KATSAYILAR.items():
        d = float(girisler.get(f"{ders}_d", 0))
        y = float(girisler.get(f"{ders}_y", 0))
        net = max(0.0, d - (y / 3.0))
        toplam_net += net

        ort, ss = param['ort'][ders], param['ss'][ders]
        sp = 50 + 10 * ((net - ort) / ss)
        toplam_asp += sp * katsayi

    max_asp = 430.0
    min_asp = 130.0
    
    lgs_puani = 100.0 + 400.0 * ((toplam_asp - min_asp) / (max_asp - min_asp))
    lgs_puani = max(100.0, min(500.0, lgs_puani))

    return jsonify({
        'puan': round(lgs_puani, 2),
        'yuzdelik': yuzdelik_dilim_hesapla(lgs_puani),
        'toplam_net': round(toplam_net, 2)
    })
