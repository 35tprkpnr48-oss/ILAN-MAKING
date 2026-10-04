from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# MEB Standart Sapma ve Türkiye Ortalamaları Türetilmiş Yıl Parametreleri
YEAR_DATA = {
    "2026": {"base": 195.0, "coeffs": {"turkce": 4.30, "matematik": 4.25, "fen": 4.10, "inkilap": 1.65, "din": 1.85, "ingilizce": 1.50}},
    "2025": {"base": 195.0, "coeffs": {"turkce": 4.30, "matematik": 4.25, "fen": 4.10, "inkilap": 1.65, "din": 1.85, "ingilizce": 1.50}},
    "2024": {"base": 196.1, "coeffs": {"turkce": 4.34, "matematik": 4.25, "fen": 4.12, "inkilap": 1.66, "din": 1.89, "ingilizce": 1.50}},
    "2023": {"base": 195.4, "coeffs": {"turkce": 4.28, "matematik": 4.18, "fen": 4.05, "inkilap": 1.60, "din": 1.80, "ingilizce": 1.48}},
    "2022": {"base": 200.0, "coeffs": {"turkce": 4.40, "matematik": 4.32, "fen": 4.15, "inkilap": 1.68, "din": 1.90, "ingilizce": 1.52}},
    "2021": {"base": 200.0, "coeffs": {"turkce": 4.45, "matematik": 4.38, "fen": 4.20, "inkilap": 1.70, "din": 1.92, "ingilizce": 1.55}},
    "2020": {"base": 200.0, "coeffs": {"turkce": 4.35, "matematik": 4.20, "fen": 4.10, "inkilap": 1.64, "din": 1.85, "ingilizce": 1.49}},
    "2019": {"base": 194.0, "coeffs": {"turkce": 4.25, "matematik": 4.15, "fen": 4.02, "inkilap": 1.58, "din": 1.78, "ingilizce": 1.45}},
    "2018": {"base": 190.0, "coeffs": {"turkce": 4.20, "matematik": 4.10, "fen": 3.98, "inkilap": 1.55, "din": 1.75, "ingilizce": 1.42}}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MEB Uyumlu LGS Puan Hesaplama</title>
    <style>
        * { box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, sans-serif; margin: 0; padding: 0; }
        body { background: #f0f2f5; padding: 15px; color: #333; }
        .card { max-width: 650px; margin: 0 auto; background: #fff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        h2 { text-align: center; color: #1a73e8; margin-bottom: 15px; }
        .year-select { margin-bottom: 20px; text-align: center; }
        select { padding: 8px 12px; font-size: 16px; border-radius: 6px; border: 1px solid #ccc; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
        th, td { padding: 8px; text-align: center; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; }
        input[type="number"] { width: 55px; padding: 5px; text-align: center; border: 1px solid #ccc; border-radius: 4px; }
        .btn { width: 100%; padding: 12px; background: #1a73e8; color: #fff; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; }
        .btn:hover { background: #1557b0; }
        .res-box { margin-top: 20px; padding: 15px; background: #e8f0fe; border-radius: 8px; display: none; }
        .res-item { font-size: 16px; margin: 6px 0; }
    </style>
</head>
<body>

<div class="card">
    <h2>LGS Puan & Yüzdelik Hesaplama</h2>
    
    <div class="year-select">
        <label><b>Sınav Yılı: </b></label>
        <select id="year">
            <option value="2026">2026 LGS (Tahmini/MEB)</option>
            <option value="2025">2025 LGS</option>
            <option value="2024">2024 LGS</option>
            <option value="2023">2023 LGS</option>
            <option value="2022">2022 LGS</option>
            <option value="2021">2021 LGS</option>
            <option value="2020">2020 LGS</option>
            <option value="2019">2019 LGS</option>
            <option value="2018">2018 LGS</option>
        </select>
    </div>

    <table>
        <thead>
            <tr>
                <th>Ders</th>
                <th>Doğru</th>
                <th>Yanlış</th>
                <th>Boş</th>
                <th>Net</th>
            </tr>
        </thead>
        <tbody id="tbody"></tbody>
    </table>

    <button class="btn" onclick="hesapla()">Puan Hesapla</button>

    <div class="res-box" id="results">
        <h3>Hesaplama Sonucu:</h3>
        <div class="res-item">Toplam Net: <b id="r-net">0</b></div>
        <div class="res-item">LGS Puanı: <b id="r-score">0</b></div>
        <div class="res-item">Tahmini Yüzdelik Dilim: <b id="r-percent">%0</b></div>
    </div>
</div>

<script>
    const dersler = [
        { id: "turkce", name: "Türkçe", max: 20 },
        { id: "matematik", name: "Matematik", max: 20 },
        { id: "fen", name: "Fen Bilimleri", max: 20 },
        { id: "inkilap", name: "İnkılap T.", max: 10 },
        { id: "din", name: "Din Kültürü", max: 10 },
        { id: "ingilizce", name: "Yabancı Dil", max: 10 }
    ];

    const tbody = document.getElementById("tbody");
    dersler.forEach(d => {
        tbody.innerHTML += `
            <tr>
                <td><b>${d.name}</b></td>
                <td><input type="number" id="${d.id}-d" value="0" min="0" max="${d.max}" onchange="guncelle('${d.id}', ${d.max})"></td>
                <td><input type="number" id="${d.id}-y" value="0" min="0" max="${d.max}" onchange="guncelle('${d.id}', ${d.max})"></td>
                <td><input type="number" id="${d.id}-b" value="${d.max}" readonly style="background:#eee;"></td>
                <td><span id="${d.id}-net">0.00</span></td>
            </tr>
        `;
    });

    function guncelle(id, max) {
        let d = parseInt(document.getElementById(`${id}-d`).value) || 0;
        let y = parseInt(document.getElementById(`${id}-y`).value) || 0;
        if (d + y > max) {
            alert(`Doğru ve yanlış sayısı toplamı ${max}'i aşamaz!`);
            document.getElementById(`${id}-y`).value = 0;
            y = 0;
        }
        let b = max - (d + y);
        let net = d - (y / 3);
        document.getElementById(`${id}-b`).value = b;
        document.getElementById(`${id}-net`).innerText = net.toFixed(2);
    }

    async function hesapla() {
        let payload = {
            year: document.getElementById("year").value,
            scores: {}
        };

        dersler.forEach(d => {
            let correct = parseInt(document.getElementById(`${d.id}-d`).value) || 0;
            let wrong = parseInt(document.getElementById(`${d.id}-y`).value) || 0;
            payload.scores[d.id] = { d: correct, y: wrong };
        });

        let response = await fetch("/calculate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        let res = await response.json();
        
        document.getElementById("r-net").innerText = res.total_net;
        document.getElementById("r-score").innerText = res.score;
        document.getElementById("r-percent").innerText = "%" + res.percentile;
        document.getElementById("results").style.display = "block";
    }
</script>

</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json()
    year = data.get('year', '2026')
    scores = data.get('scores', {})

    config = YEAR_DATA.get(year, YEAR_DATA["2026"])
    
    total_net = 0.0
    total_score = config["base"]

    for lesson_id, vals in scores.items():
        d = float(vals.get('d', 0))
        y = float(vals.get('y', 0))
        net = d - (y / 3.0)
        if net < 0:
            net = 0.0
        total_net += net
        
        coeff = config["coeffs"].get(lesson_id, 1.0)
        total_score += net * coeff

    if total_score > 500.0:
        total_score = 500.0
    if total_score < 100.0:
        total_score = 100.0

    # Puan - Yüzdelik Dilim Dönüşümü
    if total_score >= 490:
        percentile = 0.05
    elif total_score <= 100:
        percentile = 99.99
    else:
        percentile = 100.0 - ((total_score - 100.0) / 400.0 * 99.0)

    return jsonify({
        "total_net": round(total_net, 2),
        "score": round(total_score, 3),
        "percentile": round(percentile, 2)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

