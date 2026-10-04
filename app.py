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
    app.run(host='0.0.0.0', port=5000)
