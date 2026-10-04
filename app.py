from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# MEB Ders Katsayıları
KATSAYILAR = {
    'turkce': 4.0,
    'matematik': 4.0,
    'fen': 4.0,
    'inkilap': 1.0,
    'din': 1.0,
    'ingilizce': 1.0
}

# Derslerin Maksimum Net Sayıları
MAX_NETLER = {
    'turkce': 20.0,
    'matematik': 20.0,
    'fen': 20.0,
    'inkilap': 10.0,
    'din': 10.0,
    'ingilizce': 10.0
}

# Toplam Ağırlıklı Katsayı Puanı (20*4 + 20*4 + 20*4 + 10*1 + 10*1 + 10*1 = 270)
MAX_AGIRLIKLI_NET = 270.0

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
    girisler = data.get('dersler', {})

    toplam_agirlikli_net = 0.0
    toplam_net = 0.0

    for ders, katsayi in KATSAYILAR.items():
        d = float(girisler.get(f"{ders}_d", 0))
        y = float(girisler.get(f"{ders}_y", 0))
        net = max(0.0, d - (y / 3.0))
        toplam_net += net
        toplam_agirlikli_net += net * katsayi

    # LGS Puanı = Taban Puan (100) + (Ağırlıklı Net / Max Ağırlıklı Net) * 400
    lgs_puani = 100.0 + (toplam_agirlikli_net / MAX_AGIRLIKLI_NET) * 400.0
    lgs_puani = max(100.0, min(500.0, lgs_puani))

    return jsonify({
        'puan': round(lgs_puani, 2),
        'yuzdelik': yuzdelik_dilim_hesapla(lgs_puani),
        'toplam_net': round(toplam_net, 2)
    })
