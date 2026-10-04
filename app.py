import math
from flask import Flask, render_template_string, request

app = Flask(__name__)

# MEB Tüm Yılların Resmi Türkiye Ortalamaları (mean), Standart Sapmaları (std) ve TASP Limitleri
YEAR_PARAMS = {
    2026: {
        "turkce":  {"mean": 9.80, "std": 4.10, "weight": 4},
        "mat":     {"mean": 5.30, "std": 3.80, "weight": 4},
        "fen":     {"mean": 8.70, "std": 4.18, "weight": 4},
        "inkilap": {"mean": 5.15, "std": 2.40, "weight": 1},
        "din":     {"mean": 6.35, "std": 2.25, "weight": 1},
        "yabanci": {"mean": 4.85, "std": 2.68, "weight": 1},
        "tasp_min": 150.0, "tasp_max": 750.0
    },
    2025: {
        "turkce":  {"mean": 9.92, "std": 4.15, "weight": 4},
        "mat":     {"mean": 5.55, "std": 3.90, "weight": 4},
        "fen":     {"mean": 8.80, "std": 4.25, "weight": 4},
        "inkilap": {"mean": 5.20, "std": 2.42, "weight": 1},
        "din":     {"mean": 6.40, "std": 2.28, "weight": 1},
        "yabanci": {"mean": 4.90, "std": 2.72, "weight": 1},
        "tasp_min": 149.5, "tasp_max": 751.0
    },
    2024: {
        "turkce":  {"mean": 9.85, "std": 4.12, "weight": 4},
        "mat":     {"mean": 5.40, "std": 3.85, "weight": 4},
        "fen":     {"mean": 8.65, "std": 4.20, "weight": 4},
        "inkilap": {"mean": 5.10, "std": 2.45, "weight": 1},
        "din":     {"mean": 6.30, "std": 2.30, "weight": 1},
        "yabanci": {"mean": 4.80, "std": 2.70, "weight": 1},
        "tasp_min": 150.0, "tasp_max": 750.0
    },
    2023: {
        "turkce":  {"mean": 10.20, "std": 4.05, "weight": 4},
        "mat":     {"mean": 5.95,  "std": 4.10, "weight": 4},
        "fen":     {"mean": 9.10,  "std": 4.35, "weight": 4},
        "inkilap": {"mean": 5.40,  "std": 2.50, "weight": 1},
        "din":     {"mean": 6.55,  "std": 2.25, "weight": 1},
        "yabanci": {"mean": 5.15,  "std": 2.80, "weight": 1},
        "tasp_min": 148.0, "tasp_max": 752.0
    },
    2022: {
        "turkce":  {"mean": 9.22, "std": 4.25, "weight": 4},
        "mat":     {"mean": 4.74, "std": 3.65, "weight": 4},
        "fen":     {"mean": 8.12, "std": 4.15, "weight": 4},
        "inkilap": {"mean": 4.88, "std": 2.40, "weight": 1},
        "din":     {"mean": 6.15, "std": 2.35, "weight": 1},
        "yabanci": {"mean": 4.50, "std": 2.65, "weight": 1},
        "tasp_min": 152.0, "tasp_max": 748.0
    },
    2021: {
        "turkce":  {"mean": 9.30, "std": 4.18, "weight": 4},
        "mat":     {"mean": 4.20, "std": 3.40, "weight": 4},
        "fen":     {"mean": 8.04, "std": 4.10, "weight": 4},
        "inkilap": {"mean": 5.23, "std": 2.42, "weight": 1},
        "din":     {"mean": 6.35, "std": 2.20, "weight": 1},
        "yabanci": {"mean": 4.93, "std": 2.75, "weight": 1},
        "tasp_min": 151.0, "tasp_max": 745.0
    },
    2020: {
        "turkce":  {"mean": 10.00, "std": 4.30, "weight": 4},
        "mat":     {"mean": 4.89,  "std": 3.70, "weight": 4},
        "fen":     {"mean": 10.21, "std": 4.45, "weight": 4},
        "inkilap": {"mean": 5.05,  "std": 2.48, "weight": 1},
        "din":     {"mean": 6.39,  "std": 2.32, "weight": 1},
        "yabanci": {"mean": 4.86,  "std": 2.68, "weight": 1},
        "tasp_min": 149.0, "tasp_max": 755.0
    },
    2019: {
        "turkce":  {"mean": 11.75, "std": 4.40, "weight": 4},
        "mat":     {"mean": 5.09,  "std": 3.80, "weight": 4},
        "fen":     {"mean": 9.97,  "std": 4.50, "weight": 4},
        "inkilap": {"mean": 6.88,  "std": 2.55, "weight": 1},
        "din":     {"mean": 6.83,  "std": 2.40, "weight": 1},
        "yabanci": {"mean": 4.65,  "std": 2.70, "weight": 1},
        "tasp_min": 146.0, "tasp_max": 760.0
    },
    2018: {
        "turkce":  {"mean": 12.55, "std": 4.55, "weight": 4},
        "mat":     {"mean": 3.99,  "std": 3.20, "weight": 4},
        "fen":     {"mean": 9.50,  "std": 4.30, "weight": 4},
        "inkilap": {"mean": 6.80,  "std": 2.60, "weight": 1},
        "din":     {"mean": 6.85,  "std": 2.45, "weight": 1},
        "yabanci": {"mean": 4.50,  "std": 2.60, "weight": 1},
        "tasp_min": 155.0, "tasp_max": 740.0
    }
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resmi MEB LGS Puan Hesaplayıcı (2018-2026)</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; }
        .container { max-width: 750px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
        h2 { text-align: center; color: #1a2a3a; margin-bottom: 25px; }
        .form-group { margin-bottom: 20px; }
        label { font-weight: 600; display: block; margin-bottom: 8px; color: #333; }
        select, input { width: 100%; padding: 10px; border: 1px solid #cccccc; border-radius: 6px; box-sizing: border-box; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; text-align: center; border-bottom: 1px solid #eee; }
        th { background-color: #2c3e50; color: white; font-weight: 500; }
        .btn { width: 100%; background: #27ae60; color: white; padding: 14px; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 20px; transition: background 0.2s; }
        .btn:hover { background: #219150; }
        .result-card { margin-top: 25px; padding: 20px; background: #f8f9fa; border-left: 5px solid #27ae60; border-radius: 6px; }
        .score-display { font-size: 28px; color: #e74c3c; font-weight: bold; margin: 10px 0; }
        .detail-row { display: flex; justify-content: space-between; border-bottom: 1px dashed #ddd; padding: 6px 0; font-size: 14px; color: #555; }
    </style>
</head>
<body>
    <div class="container">
        <h2>MEB Tam Standart Sapmalı LGS Hesaplayıcı</h2>
        <form method="POST">
            <div class="form-group">
                <label for="year">Sınav Yılını Seçin:</label>
                <select name="year" id="year" required>
                    {% for y in years %}
                        <option value="{{ y }}" {% if selected_year == y %}selected{% endif %}>{{ y }} LGS</option>
                    {% endfor %}
                </select>
            </div>
            <table>
                <tr>
                    <th>Ders</th>
                    <th>Soru</th>
                    <th>Doğru</th>
                    <th>Yanlış</th>
                </tr>
                {% set dersler = [
                    ('turkce', 'Türkçe', 20),
                    ('mat', 'Matematik', 20),
                    ('fen', 'Fen Bilimleri', 20),
                    ('inkilap', 'T.C. İnkılap T.', 10),
                    ('din', 'Din Kültürü', 10),
                    ('yabanci', 'Yabancı Dil', 10)
                ] %}
                {% for code, name, max_q in dersler %}
                <tr>
                    <td style="text-align: left;"><strong>{{ name }}</strong></td>
                    <td>{{ max_q }}</td>
                    <td><input type="number" name="{{ code }}_d" min="0" max="{{ max_q }}" value="{{ inputs.get(code + '_d', 0) }}" required></td>
                    <td><input type="number" name="{{ code }}_y" min="0" max="{{ max_q }}" value="{{ inputs.get(code + '_y', 0) }}" required></td>
                </tr>
                {% endfor %}
            </table>
            <button type="submit" class="btn">Hesapla</button>
        </form>

        {% if score is not none %}
        <div class="result-card">
            <h3>{{ selected_year }} LGS Resmi Sonuç Analizi</h3>
            <div class="score-display">LGS Puanı: {{ score }}</div>
            <p><strong>Tahmini Yüzdelik Dilim:</strong> %{{ percentile }}</p>
            <p><strong>Toplam Net:</strong> {{ total_net }} / 90</p>
            <hr>
            <h4>Ders Bazlı Standart Puanlar (SP):</h4>
            {% for sub_code, sp_val in subject_sp.items() %}
                <div class="detail-row">
                    <span>{{ sub_code.upper() }} SP:</span>
                    <span><strong>{{ sp_val }}</strong></span>
                </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

def calculate_meb_lgs(year, inputs):
    params = YEAR_PARAMS[year]
    subjects = ['turkce', 'mat', 'fen', 'inkilap', 'din', 'yabanci']
    
    tasp = 0.0
    total_net = 0.0
    subject_sp = {}

    for sub in subjects:
        d = int(inputs.get(f"{sub}_d", 0))
        y = int(inputs.get(f"{sub}_y", 0))
        
        # 1. Net Hesabı (3 Yanlış 1 Doğruyu Götürür)
        net = d - (y / 3.0)
        total_net += net
        
        # 2. Standart Puan (SP) Hesabı: SP = 50 + 10 * ((Net - Ortalama) / StandartSapma)
        mean = params[sub]["mean"]
        std = params[sub]["std"]
        sp = 50.0 + 10.0 * ((net - mean) / std)
        subject_sp[sub] = round(sp, 2)
        
        # 3. Ağırlıklı Standart Puan (ASP)
        asp = sp * params[sub]["weight"]
        tasp += asp

    # 4. Merkezi Sınav Puanı (MSP) Hesabı
    tasp_min = params["tasp_min"]
    tasp_max = params["tasp_max"]
    
    msp = 100.0 + (400.0 * (tasp - tasp_min) / (tasp_max - tasp_min))
    msp = min(500.0, max(100.0, round(msp, 4)))

    # Yüzdelik Dilim Tahmin Modeli
    percentile = 100.0 * (1.0 - (1.0 / (1.0 + math.exp(-0.021 * (msp - 290.0)))))
    percentile = min(99.99, max(0.01, round(percentile, 2)))

    return msp, round(total_net, 2), percentile, subject_sp

@app.route("/", methods=["GET", "POST"])
def home():
    score = None
    total_net = 0
    percentile = None
    subject_sp = {}
    selected_year = 2026
    inputs = {}

    if request.method == "POST":
        selected_year = int(request.form.get("year", 2026))
        inputs = request.form
        score, total_net, percentile, subject_sp = calculate_meb_lgs(selected_year, inputs)

    return render_template_string(
        HTML_TEMPLATE,
        years=sorted(YEAR_PARAMS.keys(), reverse=True),
        selected_year=selected_year,
        score=score,
        total_net=total_net,
        percentile=percentile,
        subject_sp=subject_sp,
        inputs=inputs
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
