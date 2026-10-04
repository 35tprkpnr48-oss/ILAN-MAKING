from flask import Flask, render_template

# Flask uygulamasını başlatıyoruz
app = Flask(__name__)

# Ana sayfa rotasını (URL) tanımlıyoruz.
# Kullanıcı siteye girdiğinde ('/') burası çalışır.
@app.route('/')
def home():
    # 'templates' klasöründeki 'index.html' dosyasını okur ve ekrana basar.
    return render_template('index.html')

# Uygulamayı çalıştırıyoruz
if __name__ == '__main__':
    # Render gibi platformlarda sitenin dış dünyaya açılması için
    # host'u '0.0.0.0' yapmalıyız.
    # Port varsayılan olarak 5000'dir, Render bunu otomatik ayarlar.
    app.run(host='0.0.0.0', port=5000)@app.route('/sitemap.xml')
def sitemap():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://ilan-making.onrender.com/</loc>
    <priority>1.0</priority>
  </url>
</urlset>"""
    return xml, 200, {'Content-Type': 'application/xml'}
