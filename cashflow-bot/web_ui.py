"""
Web UI - Market Cash Flow Analyzer
Browser'da interaktif UI ile çalışır.

Özellikler:
- Yenile butonu ile canlı veri çekme
- Loading animasyonu
- Otomatik yenileme (opsiyonel)
- Modern, responsive tasarım

Kullanım:
    python web_ui.py

Browser'da otomatik açılır: http://localhost:5000
"""

from flask import Flask, render_template_string, jsonify, request
from cashflow_analyzer import CashFlowAnalyzer
import webbrowser
import threading
import time
from datetime import datetime

app = Flask(__name__)
analyzer = CashFlowAnalyzer()

# HTML Template (Embedded)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>💰 Market Cash Flow - Live UI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1800px;
            margin: 0 auto;
        }

        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }

        .header h1 {
            color: #667eea;
            font-size: 28px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .controls {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }

        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-refresh {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .btn-refresh:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        .btn-refresh:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }

        .btn-auto {
            background: #4CAF50;
            color: white;
        }

        .btn-auto.active {
            background: #f44336;
        }

        .btn-auto:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
        }

        .settings {
            display: flex;
            gap: 15px;
            align-items: center;
        }

        .settings label {
            font-weight: 600;
            color: #333;
        }

        .settings select,
        .settings input {
            padding: 8px 12px;
            border: 2px solid #667eea;
            border-radius: 6px;
            font-size: 14px;
            outline: none;
        }

        .status {
            background: rgba(255, 255, 255, 0.95);
            padding: 15px 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }

        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .status-item strong {
            color: #667eea;
        }

        .loading {
            display: none;
            text-align: center;
            padding: 40px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        .loading.active {
            display: block;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .loading p {
            color: #667eea;
            font-size: 18px;
            font-weight: 600;
        }

        .content {
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            min-height: 400px;
        }

        .error {
            background: #f44336;
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }

        @media (max-width: 768px) {
            .header, .controls, .settings {
                flex-direction: column;
                align-items: stretch;
            }

            .btn {
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💰 Market Cash Flow Analyzer</h1>
            <div class="controls">
                <button class="btn btn-refresh" onclick="refreshData()">
                    🔄 Yenile
                </button>
                <button class="btn btn-auto" onclick="toggleAutoRefresh()">
                    ⏰ Otomatik Yenileme
                </button>
            </div>
        </div>

        <div class="header settings">
            <div>
                <label>Coin Sayısı:</label>
                <select id="topN" onchange="saveSettings()">
                    <option value="10">Top 10</option>
                    <option value="20">Top 20</option>
                    <option value="30" selected>Top 30</option>
                    <option value="50">Top 50</option>
                </select>
            </div>
            <div>
                <label>Otomatik Yenileme:</label>
                <select id="autoInterval" onchange="saveSettings()">
                    <option value="60">1 dakika</option>
                    <option value="300" selected>5 dakika</option>
                    <option value="600">10 dakika</option>
                    <option value="1800">30 dakika</option>
                </select>
            </div>
        </div>

        <div class="status">
            <div class="status-item">
                <strong>Son Güncelleme:</strong>
                <span id="lastUpdate">-</span>
            </div>
            <div class="status-item">
                <strong>Risk:</strong>
                <span id="riskLevel">-</span>
            </div>
            <div class="status-item">
                <strong>Top 10 Dominance:</strong>
                <span id="dominance">-</span>
            </div>
            <div class="status-item">
                <strong>Analiz Edilen Coin:</strong>
                <span id="totalCoins">-</span>
            </div>
        </div>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Binance'den canlı veri çekiliyor...</p>
            <p style="color: #999; margin-top: 10px;">Bu 30-60 saniye sürebilir</p>
        </div>

        <div class="content" id="content">
            <p style="text-align: center; color: #999; padding: 100px 20px;">
                Veri yüklemek için "Yenile" butonuna tıklayın
            </p>
        </div>
    </div>

    <script>
        let autoRefreshTimer = null;
        let autoRefreshActive = false;

        // Ayarları localStorage'dan yükle
        function loadSettings() {
            const topN = localStorage.getItem('topN') || '30';
            const autoInterval = localStorage.getItem('autoInterval') || '300';
            document.getElementById('topN').value = topN;
            document.getElementById('autoInterval').value = autoInterval;
        }

        // Ayarları kaydet
        function saveSettings() {
            localStorage.setItem('topN', document.getElementById('topN').value);
            localStorage.setItem('autoInterval', document.getElementById('autoInterval').value);

            // Otomatik yenileme aktifse, interval'i güncelle
            if (autoRefreshActive) {
                stopAutoRefresh();
                startAutoRefresh();
            }
        }

        // Veri yenile
        async function refreshData() {
            const refreshBtn = document.querySelector('.btn-refresh');
            const loading = document.getElementById('loading');
            const content = document.getElementById('content');

            // Butonu disable et
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '⏳ Yükleniyor...';

            // Loading göster
            loading.classList.add('active');
            content.style.display = 'none';

            try {
                const topN = document.getElementById('topN').value;
                const response = await fetch(`/api/refresh?top_n=${topN}`);
                const data = await response.json();

                if (data.status === 'success') {
                    // İçeriği güncelle
                    content.innerHTML = data.html;

                    // Status bilgilerini güncelle
                    document.getElementById('lastUpdate').textContent = new Date().toLocaleString('tr-TR');
                    document.getElementById('riskLevel').textContent = data.risk.toUpperCase();
                    document.getElementById('dominance').textContent = `%${data.dominance}`;
                    document.getElementById('totalCoins').textContent = data.total_coins;

                    // Risk rengini ayarla
                    const riskElement = document.getElementById('riskLevel');
                    riskElement.style.color = data.risk === 'low' ? '#4CAF50' :
                                               data.risk === 'medium' ? '#FF9800' : '#f44336';
                } else {
                    content.innerHTML = `<div class="error">❌ Hata: ${data.message}</div>`;
                }
            } catch (error) {
                content.innerHTML = `<div class="error">❌ Bağlantı hatası: ${error.message}</div>`;
            } finally {
                // Loading gizle
                loading.classList.remove('active');
                content.style.display = 'block';

                // Butonu aktif et
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '🔄 Yenile';
            }
        }

        // Otomatik yenileme başlat
        function startAutoRefresh() {
            const interval = parseInt(document.getElementById('autoInterval').value) * 1000;
            autoRefreshTimer = setInterval(refreshData, interval);
            autoRefreshActive = true;

            const btn = document.querySelector('.btn-auto');
            btn.classList.add('active');
            btn.innerHTML = '⏸️ Otomatik Yenilemeyi Durdur';
        }

        // Otomatik yenileme durdur
        function stopAutoRefresh() {
            if (autoRefreshTimer) {
                clearInterval(autoRefreshTimer);
                autoRefreshTimer = null;
            }
            autoRefreshActive = false;

            const btn = document.querySelector('.btn-auto');
            btn.classList.remove('active');
            btn.innerHTML = '⏰ Otomatik Yenileme';
        }

        // Otomatik yenileme toggle
        function toggleAutoRefresh() {
            if (autoRefreshActive) {
                stopAutoRefresh();
            } else {
                refreshData(); // İlk veriyi hemen çek
                startAutoRefresh();
            }
        }

        // Sayfa yüklendiğinde ayarları yükle
        loadSettings();

        // İlk veriyi otomatik yükle
        window.addEventListener('load', () => {
            refreshData();
        });
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Ana sayfa"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/refresh')
def api_refresh():
    """Veri yenileme API endpoint'i"""
    try:
        top_n = request.args.get('top_n', 30, type=int)

        # Analiz yap
        report = analyzer.analyze(top_n=top_n, timeframe='15m', format='html')

        if report['status'] != 'success':
            return jsonify({
                'status': 'error',
                'message': report.get('message', 'Bilinmeyen hata')
            })

        return jsonify({
            'status': 'success',
            'html': report['text_report'],
            'risk': report['risk_assessment']['level'],
            'dominance': f"{report['top_10_dominance']:.1f}",
            'total_coins': report['total_coins'],
            'timestamp': report['timestamp']
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })


def open_browser():
    """Browser'ı otomatik aç"""
    time.sleep(1.5)  # Server'ın başlaması için bekle
    webbrowser.open('http://localhost:5000')


if __name__ == '__main__':
    print("=" * 60)
    print("💰 Market Cash Flow - Web UI")
    print("=" * 60)
    print()
    print("🌐 Server başlatılıyor...")
    print("📍 URL: http://localhost:5000")
    print()
    print("💡 İpuçları:")
    print("   - 'Yenile' butonu: Manuel veri güncelleme")
    print("   - 'Otomatik Yenileme': Belirli aralıklarla otomatik güncelleme")
    print("   - Coin sayısını ve interval'i ayarlayabilirsiniz")
    print()
    print("⏹️  Durdurmak için: Ctrl+C")
    print("=" * 60)
    print()

    # Browser'ı otomatik aç
    threading.Thread(target=open_browser, daemon=True).start()

    # Flask server başlat
    app.run(host='0.0.0.0', port=5000, debug=False)
