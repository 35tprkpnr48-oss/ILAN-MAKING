from flask import Flask, render_template_string, request
from math import isfinite

app = Flask(__name__)

# ==========================================
# LGS AYARLARI
# ==========================================

YILLAR = list(range(2018, 2027))

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
        "ad": "İnkılap Tarihi",
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

# Ağırlıklı netin ulaşabileceği en yüksek değer:
# 20*4 + 20*4 + 20*4 + 10 + 10 + 10 = 270

MAKS_AGIRLIKLI_NET = 270

# Tahmini puan-yüzdelik referans noktaları.
# Bunlar MEB'in resmî puan dağılımı değildir.
# Ara tahminlerde doğrusal interpolasyon kullanılır.

YUZDELIK_REFERANS = [
    (100, 100.0),
    (200, 99.0),
    (220, 97.5),
    (240, 94.0),
    (250, 91.0),
    (260, 88.0),
    (270, 84.0),
    (280, 79.0),
    (290, 74.0),
    (300, 68.0),
    (310, 62.0),
    (320, 55.0),
    (330, 48.0),
    (340, 41.0),
    (350, 34.0),
    (360, 27.0),
    (370, 21.0),
    (380, 16.0),
    (390, 12.0),
    (400, 8.8),
    (410, 6.2),
    (420, 4.2),
    (430, 2.8),
    (440, 1.8),
    (450, 1.1),
    (460, 0.65),
    (470, 0.35),
    (480, 0.15),
    (490, 0.05),
    (500, 0.01)
]


# ==========================================
# YÜZDELİK TAHMİNİ
# ==========================================

def yuzdelik_hesapla(puan):

    for i in range(len(YUZDELIK_REFERANS) - 1):

        alt_puan, alt_yuzde = YUZDELIK_REFERANS[i]
        ust_puan, ust_yuzde = YUZDELIK_REFERANS[i + 1]

        if alt_puan <= puan <= ust_puan:

            oran = (
                (puan - alt_puan) /
                (ust_puan - alt_puan)
            )

            sonuc = (
                alt_yuzde +
                oran * (ust_yuzde - alt_yuzde)
            )

            return round(sonuc, 3)

    return 100.0 if puan < 100 else 0.01


# ==========================================
# NET HESAPLAMA
# ==========================================

def net_hesapla(dogru, yanlis):

    return dogru - (yanlis / 3)


# ==========================================
# PUAN HESAPLAMA MODELİ
# ==========================================

def puan_hesapla(netler):

    agirlikli_net = 0

    for kod, ders in DERSLER.items():

        agirlikli_net += (
            netler[kod] * ders["katsayi"]
        )

    # Tahmini model:
    # 0 ağırlıklı net = 100 puan
    # 270 ağırlıklı net = 500 puan

    puan = (
        100 +
        (agirlikli_net / MAKS_AGIRLIKLI_NET) * 400
    )

    puan = max(100, min(500, puan))

    puan = round(puan, 2)

    yuzdelik = yuzdelik_hesapla(puan)

    return {
        "puan": puan,
        "yuzdelik": yuzdelik,
        "agirlikli_net": round(agirlikli_net, 2)
    }


# ==========================================
# HTML
# ==========================================

HTML = r"""
<!DOCTYPE html>
<html lang="tr">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>LGS Puan Hesaplama 2018-2026</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #f3f6fc;
    font-family: Arial, sans-serif;
    color: #17243d;
}

.header {
    background: linear-gradient(135deg,#10264d,#2863c4);
    color: white;
    text-align: center;
    padding: 35px 15px;
}

.header h1 {
    margin: 0;
    font-size: 29px;
}

.header p {
    color: #dce8ff;
    font-size: 14px;
}

.container {
    max-width: 850px;
    margin: 25px auto;
    padding: 12px;
}

.card {
    background: white;
    border-radius: 17px;
    padding: 23px;
    margin-bottom: 20px;
    box-shadow: 0 5px 25px rgba(0,0,0,.06);
}

h2 {
    color: #194785;
    font-size: 21px;
}

select, input {
    width: 100%;
    padding: 13px;
    border: 1px solid #dce3ef;
    border-radius: 9px;
    font-size: 16px;
    background: white;
}

input:focus, select:focus {
    outline: 2px solid #8eb5ff;
}

.ders {
    display: grid;
    grid-template-columns: 1.5fr 1fr 1fr 1fr;
    gap: 9px;
    align-items: center;
    margin-bottom: 17px;
}

.ders-adi {
    font-weight: bold;
    font-size: 14px;
}

.ders-adi small {
    display: block;
    color: #7b879a;
    margin-top: 4px;
}

.baslik {
    font-size: 12px;
    color: #758198;
    margin-bottom: 5px;
}

button {
    width: 100%;
    padding: 16px;
    background: #245bb5;
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 17px;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    background: #17458f;
}

.reset {
    display: block;
    text-align: center;
    padding: 13px;
    color: #526782;
    text-decoration: none;
}

.hata {
    background: #fff0f0;
    color: #a51e1e;
    padding: 15px;
    border-radius: 9px;
    margin-top: 17px;
}

.sonuc {
    background: #f0f6ff;
    border-radius: 13px;
    padding: 20px;
    margin-top: 20px;
}

.sonuc-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}

.sonuc-kutu {
    background: white;
    border-radius: 12px;
    padding: 17px;
    text-align: center;
}

.sonuc-kutu small {
    color: #687891;
}

.puan {
    font-size: 37px;
    color: #2055a7;
    font-weight: bold;
    margin-top: 8px;
}

.yuzde {
    font-size: 29px;
    color: #11815a;
    font-weight: bold;
    margin-top: 8px;
}

.net-satir {
    display: flex;
    justify-content: space-between;
    padding: 12px 0;
    border-bottom: 1px solid #e3eaf5;
}

.net-deger {
    color: #245bb5;
    font-weight: bold;
}

.bar {
    height: 9px;
    background: #e7edf7;
    border-radius: 10px;
    overflow: hidden;
    margin-top: 7px;
}

.bar-ic {
    height: 100%;
    background: #3978dc;
    border-radius: 10px;
}

.uyari {
    background: #fff6e4;
    border-left: 4px solid #e2a333;
    border-radius: 7px;
    padding: 14px;
    font-size: 13px;
    line-height: 1.6;
    color: #72501b;
    margin-top: 15px;
}

.footer {
    text-align: center;
    color: #8390a4;
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
        font-size: 23px;
    }

    .sonuc-grid {
        grid-template-columns: 1fr;
    }

    .card {
        padding: 17px;
    }
}

</style>

</head>

<body>

<div class="header">

<h1>🎓 LGS PUAN HESAPLAMA</h1>

<p>2018 – 2026 | Türkiye Geneli</p>

</div>

<div class="container">

<div class="card">

<h2>Sınav yılını seç</h2>

<form method="POST">

<select name="yil">

{% for yil in yillar %}

<option value="{{ yil }}"
{% if yil == secilen_yil %}selected{% endif %}>

{{ yil }} LGS

</option>

{% endfor %}

</select>

<h2>Ders sonuçlarını gir</h2>

<div class="ders">

<div></div>
<div class="baslik">DOĞRU</div>
<div class="baslik">YANLIŞ</div>
<div class="baslik">BOŞ</div>

</div>

{% for kod, ders in dersler.items() %}

<div class="ders">

<div class="ders-adi">

{{ ders.ad }}

<small>{{ ders.soru }} soru</small>

</div>

<input type="number"
name="{{ kod }}_dogru"
min="0"
max="{{ ders.soru }}"
placeholder="0"
value="{{ girdiler.get(kod, {}).get('dogru', 0) }}"
required>

<input type="number"
name="{{ kod }}_yanlis"
min="0"
max="{{ ders.soru }}"
placeholder="0"
value="{{ girdiler.get(kod, {}).get('yanlis', 0) }}"
required>

<input type="number"
name="{{ kod }}_bos"
min="0"
max="{{ ders.soru }}"
placeholder="0"
value="{{ girdiler.get(kod, {}).get('bos', 0) }}"
required>

</div>

{% endfor %}

<button type="submit">
PUANIMI HESAPLA
</button>

</form>

<a href="/" class="reset">↻ Temizle</a>

{% if hatalar %}

<div class="hata">

<strong>Giriş hatası:</strong>

{% for hata in hatalar %}

<p>{{ hata }}</p>

{% endfor %}

</div>

{% endif %}

{% if sonuc %}

<div class="sonuc">

<h2>🎯 Hesaplama Sonucu</h2>

<div class="sonuc-grid">

<div class="sonuc-kutu">

<small>{{ secilen_yil }} Tahmini LGS Puanı</small>

<div class="puan">
{{ sonuc.puan }}
</div>

</div>

<div class="sonuc-kutu">

<small>Tahmini Yüzdelik Dilim</small>

<div class="yuzde">
%{{ sonuc.yuzdelik }}
</div>

</div>

</div>

<p>
<strong>Toplam net:</strong>
{{ "%.2f"|format(sonuc.toplam_net) }}
</p>

<p>
<strong>Ağırlıklı net:</strong>
{{ sonuc.agirlikli_net }}
</p>

<h3>Ders Netleri</h3>

{% for kod, net in sonuc.netler.items() %}

<div class="net-satir">

<span>{{ dersler[kod].ad }}</span>

<span class="net-deger">
{{ "%.2f"|format(net) }} net
</span>

</div>

<div class="bar">

<div class="bar-ic"
style="width:{{ sonuc.oranlar[kod] }}%">
</div>

</div>

{% endfor %}

<div class="uyari">

<strong>Önemli bilgilendirme:</strong>

Bu sonuç tahminidir, MEB'in resmî puanı değildir.
Net hesabı doğru - yanlış/3 formülüne dayanır.
Puan modeli katsayılı netlerin 100-500 aralığına
basit oransal dönüşümüdür. Yüzdelik ise genel
referans eğrisinden tahmin edilir. Seçilen yılın
gerçek aday ortalamaları ve puan dağılımı
kullanılmadığı için kesinlik garantisi yoktur.

</div>

</div>

{% endif %}

</div>

<div class="card">

<h2>Nasıl hesaplanır?</h2>

<p>Her üç yanlış bir doğruyu götürür.</p>

<p><strong>Net = Doğru - (Yanlış / 3)</strong></p>

<p>
Türkçe, Matematik ve Fen katsayısı 4;
İnkılap, Din ve İngilizce katsayısı 1'dir.
</p>

</div>

</div>

<div class="footer">

LGS Puan Hesaplama © 2026

</div>

</body>
</html>
"""


# ==========================================
# ANA SAYFA
# ==========================================

@app.route("/", methods=["GET", "POST"])
def ana_sayfa():

    sonuc = None
    hatalar = []
    girdiler = {}

    secilen_yil = 2026

    if request.method == "POST":

        try:
            secilen_yil = int(request.form.get("yil", 2026))
        except (ValueError, TypeError):
            secilen_yil = 2026
            hatalar.append("Geçerli bir yıl seçiniz.")

        if secilen_yil not in YILLAR:
            hatalar.append("Seçilen yıl desteklenmiyor.")
            secilen_yil = 2026

        netler = {}
        toplam_net = 0
        oranlar = {}

        for kod, ders in DERSLER.items():

            degerler = {}

            for alan in ["dogru", "yanlis", "bos"]:

                ham = request.form.get(f"{kod}_{alan}", "")

                try:
                    sayi = int(ham)

                    if sayi < 0:
                        raise ValueError

                    degerler[alan] = sayi

                except (ValueError, TypeError):
                    degerler[alan] = None

                girdiler.setdefault(kod, {})[alan] = ham

            dogru = degerler["dogru"]
            yanlis = degerler["yanlis"]
            bos = degerler["bos"]

            if None in (dogru, yanlis, bos):

                hatalar.append(
                    f"{ders['ad']}: Geçerli sayılar giriniz."
                )
                continue

            if max(dogru, yanlis, bos) > ders["soru"]:

                hatalar.append(
                    f"{ders['ad']}: Her sayı en fazla "
                    f"{ders['soru']} olabilir."
                )
                continue

            toplam = dogru + yanlis + bos

            if toplam != ders["soru"]:

                hatalar.append(
                    f"{ders['ad']}: Doğru, yanlış ve boş "
                    f"toplamı {ders['soru']} olmalıdır. "
                    f"Şu an {toplam} girdiniz."
                )
                continue

            net = net_hesapla(dogru, yanlis)

            netler[kod] = net

            toplam_net += net

            oranlar[kod] = round(
                max(0, min(100, dogru / ders["soru"] * 100)),
                2
            )

        if not hatalar and len(netler) == len(DERSLER):

            puan_sonucu = puan_hesapla(netler)

            sonuc = {
                "puan": puan_sonucu["puan"],
                "yuzdelik": puan_sonucu["yuzdelik"],
                "agirlikli_net": puan_sonucu["agirlikli_net"],
                "toplam_net": round(toplam_net, 2),
                "netler": netler,
                "oranlar": oranlar
            }

    return render_template_string(
        HTML,
        yillar=YILLAR,
        dersler=DERSLER,
        secilen_yil=secilen_yil,
        sonuc=sonuc,
        hatalar=hatalar,
        girdiler=girdiler
    )


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
        )
