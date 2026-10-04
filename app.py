from flask import Flask, render_template_string, request
import math

app = Flask(__name__)

# ==========================================
# LGS RESMİ HESAPLAMA SİSTEMİ
# ==========================================

DERSLER = {
    "turkce": {
        "ad": "Türkçe",
        "soru": 20,
        "katsayi": 4
    },
    "matematik": {
        "ad": "Matematik",
        "soru": 20,
        "katsayi": 4
    },
    "fen": {
        "ad": "Fen Bilimleri",
        "soru": 20,
        "katsayi": 4
    },
    "inkilap": {
        "ad": "T.C. İnkılap Tarihi",
        "soru": 10,
        "katsayi": 1
    },
    "din": {
        "ad": "Din Kültürü",
        "soru": 10,
        "katsayi": 1
    },
    "ingilizce": {
        "ad": "İngilizce",
        "soru": 10,
        "katsayi": 1
    }
}

YILLAR = list(range(2018, 2027))

# Buraya yalnızca MEB'den doğrulanmış yıllık veriler girilecek.
# Ortalama, standart sapma, TASP minimum/maksimum ve
# puan dağılımı olmadan resmî puan/yüzdelik hesaplanamaz.

RESMI_VERILER = {
    yil: {
        "ortalama": {},
        "standart_sapma": {},
        "tasp_min": None,
        "tasp_max": None,
        "puan_dagilimi": [],
        "kaynak": None,
        "durum": "veri_bekleniyor"
    }
    for yil in YILLAR
}


# ==========================================
# VERİ DOĞRULAMA
# ==========================================

def sayi_al(deger):
    try:
        sayi = int(deger)
        return sayi
    except (ValueError, TypeError):
        return None


def verileri_kontrol_et(yil, sonuclar):
    hatalar = []

    for kod, ders in DERSLER.items():
        dogru = sonuclar[kod]["dogru"]
        yanlis = sonuclar[kod]["yanlis"]
        bos = sonuclar[kod]["bos"]

        if None in (dogru, yanlis, bos):
            hatalar.append(f"{ders['ad']} için geçersiz sayı girdiniz.")
            continue

        if min(dogru, yanlis, bos) < 0:
            hatalar.append(f"{ders['ad']} için negatif sayı girilemez.")

        if dogru + yanlis + bos != ders["soru"]:
            hatalar.append(
                f"{ders['ad']} toplamı {ders['soru']} soru olmalıdır."
            )

    if yil not in YILLAR:
        hatalar.append("Geçersiz sınav yılı.")

    return hatalar


# ==========================================
# NET HESAPLAMA
# ==========================================

def net_hesapla(dogru, yanlis):
    return dogru - (yanlis / 3)


# ==========================================
# RESMİ LGS PUAN HESAPLAMA
# ==========================================

def resmi_puan_hesapla(yil, netler):

    veri = RESMI_VERILER[yil]

    gerekli_dersler = list(DERSLER.keys())

    if not all(
        kod in veri["ortalama"]
        and kod in veri["standart_sapma"]
        for kod in gerekli_dersler
    ):
        return None

    if veri["tasp_min"] is None or veri["tasp_max"] is None:
        return None

    if veri["tasp_max"] <= veri["tasp_min"]:
        return None

    tasp = 0

    for kod, ders in DERSLER.items():

        ortalama = veri["ortalama"][kod]
        sapma = veri["standart_sapma"][kod]

        if sapma <= 0:
            return None

        standart_puan = (
            50 + 10 * (netler[kod] - ortalama) / sapma
        )

        agirlikli_puan = standart_puan * ders["katsayi"]

        tasp += agirlikli_puan

    min_tasp = veri["tasp_min"]
    max_tasp = veri["tasp_max"]

    puan = (
        100 + 400 * (tasp - min_tasp) / (max_tasp - min_tasp)
    )

    puan = max(100, min(500, puan))

    return {
        "puan": round(puan, 2),
        "tasp": round(tasp, 4)
    }


# ==========================================
# YÜZDELİK DİLİM HESAPLAMA
# ==========================================

def yuzdelik_hesapla(yil, puan):

    dagilim = RESMI_VERILER[yil]["puan_dagilimi"]

    if not dagilim:
        return None

    toplam = sum(item["ogrenci"] for item in dagilim)

    if toplam <= 0:
        return None

    ust = sum(
        item["ogrenci"]
        for item in dagilim
        if item["puan"] > puan
    )

    esit = sum(
        item["ogrenci"]
        for item in dagilim
        if item["puan"] == puan
    )

    yuzdelik = ((ust + esit / 2) / toplam) * 100

    return round(yuzdelik, 4)


# ==========================================
# HTML TASARIMI
# ==========================================

HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>LGS Puan Hesaplama | Resmî Veri Sistemi</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f1f5fb;
    color: #17233a;
}

.header {
    background: linear-gradient(135deg,#10264d,#2455a4);
    color: white;
    text-align: center;
    padding: 35px 15px;
}

.header h1 {
    margin: 0;
    font-size: 30px;
}

.header p {
    margin-bottom: 0;
    color: #dbeafe;
}

.container {
    max-width: 850px;
    margin: 25px auto;
    padding: 15px;
}

.card {
    background: white;
    padding: 22px;
    border-radius: 16px;
    box-shadow: 0 5px 25px rgba(0,0,0,.06);
    margin-bottom: 20px;
}

h2 {
    color: #173c78;
    font-size: 21px;
}

select, input {
    width: 100%;
    padding: 12px;
    border: 1px solid #d4dce9;
    border-radius: 8px;
    font-size: 16px;
    background: white;
}

.ders {
    display: grid;
    grid-template-columns: 1.5fr 1fr 1fr 1fr;
    gap: 10px;
    align-items: center;
    margin-bottom: 14px;
}

.ders-baslik {
    font-size: 12px;
    color: #667085;
    margin-bottom: 5px;
}

.ders-adi {
    font-weight: bold;
    font-size: 14px;
}

button {
    width: 100%;
    padding: 16px;
    border: none;
    background: #2455a4;
    color: white;
    border-radius: 9px;
    font-size: 17px;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    background: #173c78;
}

.sonuc {
    background: #edf4ff;
    padding: 20px;
    border-radius: 12px;
    margin-top: 20px;
}

.puan {
    font-size: 42px;
    font-weight: bold;
    color: #174c9b;
    text-align: center;
    margin: 15px;
}

.net {
    font-size: 15px;
    color: #2455a4;
    font-weight: bold;
}

.hata {
    background: #feecec;
    padding: 14px;
    border-radius: 8px;
    color: #a32020;
    margin-bottom: 15px;
}

.uyari {
    background: #fff6df;
    border-left: 4px solid #e4a321;
    padding: 14px;
    border-radius: 7px;
    line-height: 1.6;
    font-size: 14px;
}

.footer {
    text-align: center;
    color: #718096;
    padding: 25px;
    font-size: 13px;
}

@media(max-width:600px) {
    .ders {
        grid-template-columns: 1fr 1fr 1fr;
    }

    .ders-adi {
        grid-column: 1 / -1;
    }

    .header h1 {
        font-size: 24px;
    }
}

</style>
</head>

<body>

<div class="header">
    <h1>🎓 LGS PUAN HESAPLAMA</h1>
    <p>2018–2026 Sınav Yılları | Türkiye Geneli</p>
</div>

<div class="container">

<div class="card">

<h2>Sınav yılını seç</h2>

<form method="POST">

<select name="yil" required>

{% for yil in yillar %}
<option value="{{ yil }}" {% if secilen_yil == yil %}selected{% endif %}>
{{ yil }} LGS
</option>
{% endfor %}

</select>

<h2>Ders sonuçlarını gir</h2>

<div class="ders">
<div></div>
<div class="ders-baslik">Doğru</div>
<div class="ders-baslik">Yanlış</div>
<div class="ders-baslik">Boş</div>
</div>

{% for kod, ders in dersler.items() %}

<div class="ders">

<div class="ders-adi">
{{ ders.ad }}
<br>
<small>{{ ders.soru }} soru</small>
</div>

<input type="number" min="0" max="{{ ders.soru }}"
name="{{ kod }}_dogru"
placeholder="0"
value="{{ girdiler.get(kod, {}).get('dogru', '') }}"
required>

<input type="number" min="0" max="{{ ders.soru }}"
name="{{ kod }}_yanlis"
placeholder="0"
value="{{ girdiler.get(kod, {}).get('yanlis', '') }}"
required>

<input type="number" min="0" max="{{ ders.soru }}"
name="{{ kod }}_bos"
placeholder="0"
value="{{ girdiler.get(kod, {}).get('bos', '') }}"
required>

</div>

{% endfor %}

<button type="submit">PUANIMI HESAPLA</button>

</form>

{% if hatalar %}
<div class="hata">
{% for hata in hatalar %}
<div>• {{ hata }}</div>
{% endfor %}
</div>
{% endif %}

{% if sonuc %}

<div class="sonuc">

<h2>Hesaplama Sonucu</h2>

{% if sonuc.puan is not none %}

<div class="puan">{{ sonuc.puan }}</div>

<p style="text-align:center">LGS Puanı</p>

{% if sonuc.yuzdelik is not none %}
<h3 style="text-align:center">
Türkiye Geneli Yüzdelik Dilimi:
%{{ sonuc.yuzdelik }}
</h3>
{% else %}
<div class="uyari">
Bu yıl için doğrulanmış ayrıntılı öğrenci puan dağılımı
bulunmadığından yüzdelik dilim hesaplanamadı.
</div>
{% endif %}

{% else %}

<div class="uyari">
Bu sınav yılına ait resmî ortalama, standart sapma ve
TASP dönüşüm verilerinin tamamı henüz sisteme eklenmemiştir.
Kesin LGS puanı üretilemedi.
</div>

{% endif %}

<h3>Ders Netleri</h3>

{% for kod, net in sonuc.netler.items() %}
<p>
{{ dersler[kod].ad }}:
<strong class="net">{{ "%.2f"|format(net) }} net</strong>
</p>
{% endfor %}

</div>

{% endif %}

</div>

<div class="card">

<h2>Hesaplama hakkında</h2>

<div class="uyari">
Yanlış cevapların üçte biri doğru cevaplardan düşülerek
net hesaplanır. Puan hesaplaması ilgili yılın resmî
istatistikleriyle yapılır. Verisi bulunmayan yıllar için
rastgele puan veya yüzdelik üretilmez.
</div>

</div>

</div>

<div class="footer">
LGS Puan Hesaplama Platformu © 2026
</div>

</body>
</html>
"""


# ==========================================
# ANA SAYFA VE HESAPLAMA
# ==========================================

@app.route("/", methods=["GET", "POST"])
def ana_sayfa():

    sonuc = None
    hatalar = []
    girdiler = {}
    secilen_yil = 2026

    if request.method == "POST":

        yil = sayi_al(request.form.get("yil"))

        if yil is None or yil not in YILLAR:
            yil = 2026
            hatalar.append("Geçerli bir sınav yılı seçiniz.")

        secilen_yil = yil

        netler = {}

        for kod, ders in DERSLER.items():

            dogru = sayi_al(request.form.get(kod + "_dogru"))
            yanlis = sayi_al(request.form.get(kod + "_yanlis"))
            bos = sayi_al(request.form.get(kod + "_bos"))

            girdiler[kod] = {
                "dogru": request.form.get(kod + "_dogru", ""),
                "yanlis": request.form.get(kod + "_yanlis", ""),
                "bos": request.form.get(kod + "_bos", "")
            }

            if None in (dogru, yanlis, bos):
                continue

            netler[kod] = net_hesapla(dogru, yanlis)

        hatalar.extend(verileri_kontrol_et(yil, {
            kod: {
                "dogru": sayi_al(request.form.get(kod + "_dogru")),
                "yanlis": sayi_al(request.form.get(kod + "_yanlis")),
                "bos": sayi_al(request.form.get(kod + "_bos"))
            }
            for kod in DERSLER
        }))

        if not hatalar:

            puan_sonucu = resmi_puan_hesapla(yil, netler)

            puan = None
            yuzdelik = None

            if puan_sonucu:
                puan = puan_sonucu["puan"]
                yuzdelik = yuzdelik_hesapla(yil, puan)

            sonuc = {
                "puan": puan,
                "yuzdelik": yuzdelik,
                "netler": netler
            }

    return render_template_string(
        HTML,
        yillar=YILLAR,
        dersler=DERSLER,
        sonuc=sonuc,
        hatalar=hatalar,
        girdiler=girdiler,
        secilen_yil=secilen_yil
    )


# ==========================================
# SAĞLIK KONTROLÜ
# ==========================================

@app.route("/health")
def health():
    return {"status": "ok"}


# ==========================================
# SUNUCU
# ==========================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
  )
