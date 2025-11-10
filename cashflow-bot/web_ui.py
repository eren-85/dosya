"""
Web UI - Market Cash Flow & Accumulation Detector
Browser'da interaktif UI ile çalışır.

Özellikler:
- Cash Flow analizi + Accumulation detection tek ekranda
- Parametreler UI'den ayarlanabilir
- Yenile butonu ile canlı veri çekme
- Loading animasyonu
- Otomatik yenileme (opsiyonel)
- Tab yapısı (Cash Flow / Whale Signals)
- Modern, responsive tasarım

Kullanım:
    python web_ui.py

Browser'da otomatik açılır: http://localhost:5000
"""

from flask import Flask, render_template_string, jsonify, request, Response, stream_with_context
from cashflow_analyzer import CashFlowAnalyzer
from accumulation_detector import AccumulationDetector
import webbrowser
import threading
import time
import json
from datetime import datetime

app = Flask(__name__)
cash_flow_analyzer = CashFlowAnalyzer()
accumulation_detector = AccumulationDetector()

# HTML Template (Embedded)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>💰 Market Analyzer - Cash Flow & Whale Hunter</title>
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
            max-width: 95%;
            margin: 0 auto;
        }

        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }

        .header h1 {
            color: #667eea;
            font-size: 28px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .tabs {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            border-bottom: 2px solid #e0e0e0;
        }

        .tab {
            padding: 12px 24px;
            background: transparent;
            border: none;
            border-bottom: 3px solid transparent;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            color: #666;
            transition: all 0.3s ease;
        }

        .tab:hover {
            color: #667eea;
        }

        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }

        .controls {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }

        .control-section {
            margin-bottom: 20px;
        }

        .control-section:last-child {
            margin-bottom: 0;
        }

        .control-section h3 {
            color: #667eea;
            font-size: 16px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .control-row {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }

        .control-item {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }

        .control-item label {
            font-size: 13px;
            font-weight: 600;
            color: #555;
        }

        .control-item input,
        .control-item select {
            padding: 8px 12px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 14px;
            outline: none;
            min-width: 120px;
        }

        .control-item input:focus,
        .control-item select:focus {
            border-color: #667eea;
        }

        .control-item input[type="number"] {
            width: 100px;
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
            align-self: flex-end;
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

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .loading p {
            color: #667eea;
            font-size: 18px;
            font-weight: 600;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .content {
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            min-height: 400px;
        }

        .empty-state {
            text-align: center;
            color: #999;
            padding: 100px 20px;
        }

        .error {
            background: #f44336;
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }

        .accumulation-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }

        .accumulation-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #667eea;
        }

        .accumulation-card.high-score {
            border-left-color: #4CAF50;
            background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        }

        .accumulation-card h3 {
            color: #667eea;
            font-size: 24px;
            margin-bottom: 10px;
        }

        .accumulation-card .score {
            font-size: 32px;
            font-weight: bold;
            color: #f44336;
            margin-bottom: 15px;
        }

        .accumulation-card.high-score .score {
            color: #4CAF50;
        }

        .accumulation-card .metrics {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            font-size: 13px;
        }

        .accumulation-card .metric {
            display: flex;
            justify-content: space-between;
        }

        .accumulation-card .metric strong {
            color: #555;
        }

        .accumulation-card .criteria {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid rgba(0,0,0,0.1);
            font-size: 12px;
            color: #666;
        }

        @media (max-width: 768px) {
            .control-row {
                flex-direction: column;
                align-items: stretch;
            }

            .btn {
                justify-content: center;
            }

            .accumulation-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💰 Market Analyzer - Cash Flow & Whale Hunter</h1>
            <div class="tabs">
                <button class="tab active" onclick="switchTab(this, 'cashflow')">📊 Cash Flow</button>
                <button class="tab" onclick="switchTab(this, 'accumulation')">🐋 Whale Signals</button>
            </div>
        </div>

        <div class="controls">
            <div class="control-section">
                <h3>⚙️ Genel Ayarlar</h3>
                <div class="control-row">
                    <div class="control-item">
                        <label>Gösterilecek Coin:</label>
                        <select id="topN">
                            <option value="10">Top 10</option>
                            <option value="20">Top 20</option>
                            <option value="30" selected>Top 30</option>
                            <option value="50">Top 50</option>
                        </select>
                    </div>
                    <div class="control-item">
                        <label>Oto Yenileme:</label>
                        <select id="autoInterval">
                            <option value="60">1 dakika</option>
                            <option value="300" selected>5 dakika</option>
                            <option value="600">10 dakika</option>
                            <option value="1800">30 dakika</option>
                        </select>
                    </div>
                    <button class="btn btn-refresh" onclick="refreshData()">🔄 Yenile</button>
                    <button class="btn btn-auto" onclick="toggleAutoRefresh()">⏰ Otomatik Yenileme</button>
                </div>
            </div>

            <div class="control-section" id="accumulationControls" style="display: none;">
                <h3>🔍 Akümülasyon Parametreleri (Whale Tespiti)</h3>
                <div class="control-row">
                    <div class="control-item">
                        <label>🎯 Taranacak Coin Sayısı:</label>
                        <select id="maxCoins">
                            <option value="0">TÜM Coinler (500+)</option>
                            <option value="200">Top 200</option>
                            <option value="300">Top 300</option>
                            <option value="500">Top 500</option>
                        </select>
                    </div>
                    <div class="control-item">
                        <label>Hacim Artışı (%):</label>
                        <input type="number" id="volumeThreshold" value="50" min="0" max="200" step="10">
                    </div>
                    <div class="control-item">
                        <label>Max Fiyat Değişimi (%):</label>
                        <input type="number" id="priceThreshold" value="5" min="0" max="20" step="1">
                    </div>
                    <div class="control-item">
                        <label>Min Alım Baskısı (%):</label>
                        <input type="number" id="buyPressureMin" value="52" min="50" max="70" step="1">
                    </div>
                    <div class="control-item">
                        <label>Max Alım Baskısı (%):</label>
                        <input type="number" id="buyPressureMax" value="60" min="50" max="70" step="1">
                    </div>
                    <div class="control-item">
                        <label>Trade Count Artış (%):</label>
                        <input type="number" id="tradeThreshold" value="30" min="0" max="100" step="5">
                    </div>
                </div>
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
            <div class="status-item">
                <strong>Whale Sinyalleri:</strong>
                <span id="whaleSignals">-</span>
            </div>
        </div>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p id="loadingText">Binance'den canlı veri çekiliyor...</p>
            <p style="color: #999; margin-top: 10px;">Bu 30-90 saniye sürebilir</p>
        </div>

        <!-- Cash Flow Tab -->
        <div class="tab-content active" id="cashflowContent">
            <div class="content" id="cashflowData">
                <p class="empty-state">
                    Veri yüklemek için "Yenile" butonuna tıklayın
                </p>
            </div>
        </div>

        <!-- Accumulation Tab -->
        <div class="tab-content" id="accumulationContent">
            <div class="content" id="accumulationData">
                <p class="empty-state">
                    Whale sinyallerini görmek için "Yenile" butonuna tıklayın
                </p>
            </div>
        </div>
    </div>

    <script>
        let autoRefreshTimer = null;
        let autoRefreshActive = false;
        let currentTab = 'cashflow';

        // Tab switching
        function switchTab(element, tab) {
            currentTab = tab;

            // Update tab buttons
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            element.classList.add('active');

            // Update tab content
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(tab + 'Content').classList.add('active');

            // Show/hide accumulation controls
            document.getElementById('accumulationControls').style.display =
                tab === 'accumulation' ? 'block' : 'none';
        }

        // Ayarları localStorage'dan yükle
        function loadSettings() {
            document.getElementById('topN').value = localStorage.getItem('topN') || '30';
            document.getElementById('autoInterval').value = localStorage.getItem('autoInterval') || '300';
            document.getElementById('maxCoins').value = localStorage.getItem('maxCoins') || '0';
            document.getElementById('volumeThreshold').value = localStorage.getItem('volumeThreshold') || '50';
            document.getElementById('priceThreshold').value = localStorage.getItem('priceThreshold') || '5';
            document.getElementById('buyPressureMin').value = localStorage.getItem('buyPressureMin') || '52';
            document.getElementById('buyPressureMax').value = localStorage.getItem('buyPressureMax') || '60';
            document.getElementById('tradeThreshold').value = localStorage.getItem('tradeThreshold') || '30';
        }

        // Ayarları kaydet
        function saveSettings() {
            localStorage.setItem('topN', document.getElementById('topN').value);
            localStorage.setItem('autoInterval', document.getElementById('autoInterval').value);
            localStorage.setItem('maxCoins', document.getElementById('maxCoins').value);
            localStorage.setItem('volumeThreshold', document.getElementById('volumeThreshold').value);
            localStorage.setItem('priceThreshold', document.getElementById('priceThreshold').value);
            localStorage.setItem('buyPressureMin', document.getElementById('buyPressureMin').value);
            localStorage.setItem('buyPressureMax', document.getElementById('buyPressureMax').value);
            localStorage.setItem('tradeThreshold', document.getElementById('tradeThreshold').value);
        }

        // Veri yenile
        // REAL-TIME STREAMING SCAN (Whale Signals için)
        let currentEventSource = null;
        let accumulationSignals = [];

        function startStreamingScan() {
            const refreshBtn = document.querySelector('.btn-refresh');
            const loading = document.getElementById('loading');
            const accumulationContent = document.getElementById('accumulationData');

            // Eğer önceki stream varsa kapat
            if (currentEventSource) {
                currentEventSource.close();
            }

            // Ayarları kaydet
            saveSettings();

            // Butonu disable et
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '⏳ Taranıyor...';

            // Sinyalleri temizle
            accumulationSignals = [];

            // Coin sayısı kontrolü
            const maxCoins = parseInt(document.getElementById('maxCoins').value);
            const scanMessage = maxCoins === 0 ? 'TÜM Binance Coinleri' : `Top ${maxCoins} Coin`;

            // İlk mesaj
            accumulationContent.innerHTML = `
                <div style="text-align: center; padding: 40px;">
                    <h2 style="color: #667eea;">🔍 ${scanMessage} Taranıyor...</h2>
                    <p style="font-size: 16px; margin-top: 10px;">Her sinyal bulunduğunda anında görünecek!</p>
                    <div id="scanProgress" style="margin-top: 20px; font-size: 14px; color: #888;"></div>
                    <div id="signalsContainer" class="accumulation-grid" style="margin-top: 30px;"></div>
                </div>
            `;

            // EventSource oluştur
            const params = new URLSearchParams({
                max_coins: maxCoins,
                volume_threshold: document.getElementById('volumeThreshold').value,
                price_threshold: document.getElementById('priceThreshold').value,
                buy_pressure_min: document.getElementById('buyPressureMin').value,
                buy_pressure_max: document.getElementById('buyPressureMax').value,
                trade_threshold: document.getElementById('tradeThreshold').value
            });

            currentEventSource = new EventSource(`/api/scan_stream?${params}`);

            currentEventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                const progressDiv = document.getElementById('scanProgress');
                const signalsContainer = document.getElementById('signalsContainer');

                if (data.type === 'start') {
                    progressDiv.innerHTML = `📊 ${data.total_coins} coin taranacak...`;
                }
                else if (data.type === 'progress') {
                    progressDiv.innerHTML = `⏳ ${data.scanned}/${data.total} coin tarandı (${data.percent}%) - ${data.signals_found} sinyal bulundu`;
                }
                else if (data.type === 'signal') {
                    // YENİ SİNYAL BULUNDU - ANINDA EKLE!
                    const signal = data.data;
                    accumulationSignals.push(signal);

                    // Skorları sırala (en yüksek üstte)
                    accumulationSignals.sort((a, b) => b.accumulation_score - a.accumulation_score);

                    // Tüm sinyalleri yeniden render et
                    renderAccumulationSignals(signalsContainer);
                }
                else if (data.type === 'complete') {
                    progressDiv.innerHTML = `✅ Tarama tamamlandı! ${data.total_scanned} coin tarandı, ${data.signals_found} sinyal bulundu.`;
                    refreshBtn.disabled = false;
                    refreshBtn.innerHTML = '🔄 Yeniden Tara';
                    currentEventSource.close();
                    currentEventSource = null;

                    // Whale Signals sayısını güncelle
                    document.getElementById('whaleSignals').textContent = data.signals_found;
                }
                else if (data.type === 'error') {
                    accumulationContent.innerHTML = `<div class="error">❌ Hata: ${data.message}</div>`;
                    refreshBtn.disabled = false;
                    refreshBtn.innerHTML = '🔄 Yeniden Tara';
                    currentEventSource.close();
                    currentEventSource = null;
                }
            };

            currentEventSource.onerror = function(error) {
                console.error('EventSource error:', error);
                const progressDiv = document.getElementById('scanProgress');
                if (progressDiv) {
                    progressDiv.innerHTML = '❌ Bağlantı hatası! Lütfen tekrar deneyin.';
                }
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '🔄 Yeniden Tara';
                if (currentEventSource) {
                    currentEventSource.close();
                    currentEventSource = null;
                }
            };
        }

        function renderAccumulationSignals(container) {
            let html = '';
            accumulationSignals.forEach((signal, index) => {
                const highScore = signal.accumulation_score >= 70;
                const pricePos = signal.price_position || 50;
                const priceChange30d = signal.price_change_30d || 0;
                const positionLabel = pricePos < 30 ? '🟢DİP' : pricePos < 60 ? '🟡ORTA' : '🔴TEPE';

                html += `
                    <div class="accumulation-card ${highScore ? 'high-score' : ''}" style="animation: slideIn 0.3s ease; cursor: pointer;" onclick="showCoinAnalysis('${signal.symbol}', ${JSON.stringify(signal).replace(/"/g, '&quot;')})">
                        <div style="position: absolute; top: 10px; right: 10px; font-size: 12px; color: #888;">#${index + 1}</div>
                        <h3>${signal.symbol} 👆</h3>
                        <div class="score">${signal.accumulation_score.toFixed(1)}/100 ⭐</div>
                        <div class="metrics">
                            <div class="metric">
                                <strong>Hacim:</strong>
                                <span>$${signal.volume_24h.toLocaleString('en-US', {maximumFractionDigits: 0})}</span>
                            </div>
                            <div class="metric">
                                <strong>Vol Artış:</strong>
                                <span>${signal.volume_increase > 0 ? '+' : ''}${signal.volume_increase.toFixed(1)}% ${signal.volume_increase > 100 ? '🔥' : '📈'}</span>
                            </div>
                            <div class="metric">
                                <strong>Fiyat 30d:</strong>
                                <span>${priceChange30d > 0 ? '+' : ''}${priceChange30d.toFixed(1)}%</span>
                            </div>
                            <div class="metric">
                                <strong>Pozisyon:</strong>
                                <span>${pricePos.toFixed(0)}% ${positionLabel}</span>
                            </div>
                            <div class="metric">
                                <strong>Fiyat 24h:</strong>
                                <span>${signal.price_change > 0 ? '+' : ''}${signal.price_change.toFixed(2)}% ${Math.abs(signal.price_change) < 3 ? '✅' : '📊'}</span>
                            </div>
                            <div class="metric">
                                <strong>Alım:</strong>
                                <span>${signal.buy_pressure.toFixed(1)}% ${signal.buy_pressure >= 52 && signal.buy_pressure <= 58 ? '🟢' : '🟡'}</span>
                            </div>
                            <div class="metric">
                                <strong>Trade:</strong>
                                <span>${signal.trade_count_increase > 0 ? '+' : ''}${signal.trade_count_increase.toFixed(1)}% ${signal.trade_count_increase > 50 ? '🔥' : '📈'}</span>
                            </div>
                            <div class="metric">
                                <strong>OBV:</strong>
                                <span>${signal.obv_trend}</span>
                            </div>
                        </div>
                        <div class="criteria">
                            ✅ Kriterler: ${signal.criteria_met.join(', ')}
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;

            // Metrik açıklamalarını en alta ekle
            const explanationHTML = `
                <div style="margin-top: 40px; padding: 30px; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <h2 style="color: #667eea; margin-bottom: 20px;">📚 Metrik Açıklamaları</h2>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                        <div style="padding: 15px; background: #f8fafc; border-radius: 8px;">
                            <h4 style="color: #3b82f6; margin-bottom: 10px;">📊 Hacim (Volume)</h4>
                            <p style="font-size: 14px; line-height: 1.6; color: #64748b;">
                                Son 24 saatte bu coin için yapılan toplam işlem hacmi (USD bazında).
                                Yüksek hacim = Yüksek likidite ve ilgi.
                            </p>
                        </div>
                        <div style="padding: 15px; background: #f8fafc; border-radius: 8px;">
                            <h4 style="color: #3b82f6; margin-bottom: 10px;">📈 Vol Artış (Volume Increase)</h4>
                            <p style="font-size: 14px; line-height: 1.6; color: #64748b;">
                                Son 24h hacminin 7 günlük ortalamaya göre % artışı.
                                >100% = Anormal hacim patlaması (whale aktivitesi olabilir!)
                            </p>
                        </div>
                        <div style="padding: 15px; background: #f8fafc; border-radius: 8px;">
                            <h4 style="color: #3b82f6; margin-bottom: 10px;">💰 Fiyat 30d (Price 30 Days)</h4>
                            <p style="font-size: 14px; line-height: 1.6; color: #64748b;">
                                Son 30 gündeki fiyat değişim yüzdesi.
                                Negatif değer = Fiyat düşüyor (dipte olabilir).
                                >30% = Zaten pompalandı (dikkat!)
                            </p>
                        </div>
                        <div style="padding: 15px; background: #f8fafc; border-radius: 8px;">
                            <h4 style="color: #3b82f6; margin-bottom: 10px;">🎯 Pozisyon (Price Position)</h4>
                            <p style="font-size: 14px; line-height: 1.6; color: #64748b;">
                                Mevcut fiyatın 30 günlük min-max aralığındaki konumu (0-100%).
                                <br>🟢 0-30% = Dipte (ideal alım bölgesi)
                                <br>🟡 30-70% = Orta
                                <br>🔴 70-100% = Tepede (risk!)
                            </p>
                        </div>
                        <div style="padding: 15px; background: #f8fafc; border-radius: 8px;">
                            <h4 style="color: #3b82f6; margin-bottom: 10px;">💵 Fiyat 24h (Price 24h)</h4>
                            <p style="font-size: 14px; line-height: 1.6; color: #64748b;">
                                Son 24 saatteki fiyat değişimi.
                                Akümülasyon için ideal: ±5% arası (yatay hareket).
                                Whale'ler dikkat çekmeden topluyor!
                            </p>
                        </div>
                        <div style="padding: 15px; background: #f8fafc; border-radius: 8px;">
                            <h4 style="color: #3b82f6; margin-bottom: 10px;">🟢 Alım (Buy Pressure)</h4>
                            <p style="font-size: 14px; line-height: 1.6; color: #64748b;">
                                Toplam hacmin ne kadarı ALIM emri (%).
                                52-58% = İdeal gizli akümülasyon!
                                >60% = Çok belirgin (FOMO olabilir)
                                <50% = Satış baskısı var
                            </p>
                        </div>
                        <div style="padding: 15px; background: #f8fafc; border-radius: 8px;">
                            <h4 style="color: #3b82f6; margin-bottom: 10px;">🔥 Trade (Trade Count Increase)</h4>
                            <p style="font-size: 14px; line-height: 1.6; color: #64748b;">
                                İşlem sayısındaki artış (son 24h vs 7 gün ort.).
                                >30% = Aktivite artıyor (whale girişi?)
                                Negatif = İlgi azalıyor (dikkat!)
                            </p>
                        </div>
                        <div style="padding: 15px; background: #f8fafc; border-radius: 8px;">
                            <h4 style="color: #3b82f6; margin-bottom: 10px;">📊 OBV (On-Balance Volume)</h4>
                            <p style="font-size: 14px; line-height: 1.6; color: #64748b;">
                                Hacim akış yönü göstergesi.
                                <br>UP 🔼 = Hacim ALIM yönünde (güçlü!)
                                <br>DOWN 🔻 = Hacim SATIM yönünde (zayıf)
                                OBV UP olan coinler tercih edilir.
                            </p>
                        </div>
                        <div style="padding: 15px; background: #f8fafc; border-radius: 8px;">
                            <h4 style="color: #3b82f6; margin-bottom: 10px;">⭐ Skor (Accumulation Score)</h4>
                            <p style="font-size: 14px; line-height: 1.6; color: #64748b;">
                                Tüm kriterlerin toplamı (0-100+).
                                <br>90-100+ = Çok güçlü sinyal!
                                <br>70-90 = İyi sinyal
                                <br>60-70 = Orta seviye
                                <br><60 = Zayıf (filtrelenir)
                            </p>
                        </div>
                    </div>
                </div>
            `;

            container.insertAdjacentHTML('beforeend', explanationHTML);
        }

        // Coin analizi modal göster
        function showCoinAnalysis(symbol, signal) {
            // Analiz yap
            const analysis = analyzeCoin(signal);

            // Modal oluştur
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.8);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                animation: fadeIn 0.2s ease;
            `;

            modal.innerHTML = `
                <div style="
                    background: white;
                    border-radius: 16px;
                    padding: 40px;
                    max-width: 600px;
                    max-height: 80vh;
                    overflow-y: auto;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
                        <h2 style="color: #667eea; margin: 0;">🔍 ${symbol} Analizi</h2>
                        <button onclick="this.closest('[style*=fixed]').remove()" style="
                            background: #ef4444;
                            color: white;
                            border: none;
                            border-radius: 8px;
                            padding: 8px 16px;
                            cursor: pointer;
                            font-size: 14px;
                        ">✕ Kapat</button>
                    </div>

                    <div style="margin-bottom: 25px; padding: 20px; background: ${analysis.strengthColor}15; border-left: 4px solid ${analysis.strengthColor}; border-radius: 8px;">
                        <div style="font-size: 18px; font-weight: bold; color: ${analysis.strengthColor}; margin-bottom: 10px;">
                            ${analysis.strength} - Skor: ${signal.accumulation_score.toFixed(1)}/100
                        </div>
                        <div style="font-size: 14px; color: #64748b;">
                            ${analysis.summary}
                        </div>
                    </div>

                    <div style="margin-bottom: 25px;">
                        <h3 style="color: #3b82f6; margin-bottom: 15px;">💡 Detaylı Değerlendirme</h3>
                        <div style="font-size: 14px; line-height: 1.8; color: #334155;">
                            ${analysis.details}
                        </div>
                    </div>

                    <div style="margin-bottom: 25px;">
                        <h3 style="color: #3b82f6; margin-bottom: 15px;">✅ Güçlü Yönler</h3>
                        <ul style="margin: 0; padding-left: 20px; color: #10b981;">
                            ${analysis.strengths.map(s => `<li style="margin-bottom: 8px;">${s}</li>`).join('')}
                        </ul>
                    </div>

                    ${analysis.weaknesses.length > 0 ? `
                    <div style="margin-bottom: 25px;">
                        <h3 style="color: #3b82f6; margin-bottom: 15px;">⚠️ Riskler</h3>
                        <ul style="margin: 0; padding-left: 20px; color: #ef4444;">
                            ${analysis.weaknesses.map(w => `<li style="margin-bottom: 8px;">${w}</li>`).join('')}
                        </ul>
                    </div>
                    ` : ''}

                    <div style="padding: 20px; background: #f8fafc; border-radius: 8px; margin-top: 25px;">
                        <h3 style="color: #3b82f6; margin-bottom: 15px;">🎯 Tavsiye</h3>
                        <div style="font-size: 14px; line-height: 1.8; color: #334155; font-weight: 500;">
                            ${analysis.recommendation}
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);
        }

        // Coin analizini yap
        function analyzeCoin(signal) {
            const score = signal.accumulation_score;
            const pricePos = signal.price_position || 50;
            const priceChange30d = signal.price_change_30d || 0;
            const volIncrease = signal.volume_increase;
            const buyPressure = signal.buy_pressure;
            const obvTrend = signal.obv_trend;

            const strengths = [];
            const weaknesses = [];
            let strength = '';
            let strengthColor = '';
            let summary = '';
            let details = '';
            let recommendation = '';

            // Skor bazlı değerlendirme
            if (score >= 95) {
                strength = '🔥 ÇOK GÜÇLÜ SİNYAL';
                strengthColor = '#10b981';
                summary = 'Bu coin tüm akümülasyon kriterlerini başarıyla geçiyor. Whale aktivitesi çok net!';
            } else if (score >= 80) {
                strength = '✅ GÜÇLÜ SİNYAL';
                strengthColor = '#3b82f6';
                summary = 'Güçlü bir akümülasyon sinyali. Whale toplama ihtimali yüksek.';
            } else if (score >= 70) {
                strength = '🟡 ORTA SİNYAL';
                strengthColor = '#f59e0b';
                summary = 'Orta seviye akümülasyon sinyali. Dikkatli yaklaşın.';
            } else {
                strength = '⚪ ZAYIF SİNYAL';
                strengthColor = '#94a3b8';
                summary = 'Zayıf sinyal. Daha güçlü fırsatlar bekleyin.';
            }

            // Pozisyon analizi
            if (pricePos < 20) {
                strengths.push(`Fiyat çok dipte (%${pricePos.toFixed(0)}) - İdeal giriş bölgesi!`);
            } else if (pricePos < 40) {
                strengths.push(`Fiyat dip bölgesinde (%${pricePos.toFixed(0)}) - İyi giriş fırsatı`);
            } else if (pricePos > 70) {
                weaknesses.push(`Fiyat tepede (%${pricePos.toFixed(0)}) - Risk yüksek!`);
            }

            // 30 günlük fiyat değişimi
            if (priceChange30d < -20) {
                strengths.push(`30 günde %${Math.abs(priceChange30d).toFixed(1)} düşmüş - Düşük riskli giriş`);
            } else if (priceChange30d > 30) {
                weaknesses.push(`30 günde %${priceChange30d.toFixed(1)} artmış - Zaten pompalanmış olabilir`);
            }

            // Hacim artışı
            if (volIncrease > 200) {
                strengths.push(`Hacim %${volIncrease.toFixed(0)} artmış - Whale hareketi olabilir!`);
            } else if (volIncrease > 100) {
                strengths.push(`Hacim %${volIncrease.toFixed(0)} artmış - Güçlü ilgi var`);
            } else if (volIncrease < 30) {
                weaknesses.push(`Hacim artışı zayıf (%${volIncrease.toFixed(0)})`);
            }

            // Alım baskısı
            if (buyPressure >= 52 && buyPressure <= 58) {
                strengths.push(`İdeal gizli alım baskısı (%${buyPressure.toFixed(1)}) - Whale toplama ihtimali yüksek`);
            } else if (buyPressure > 58) {
                weaknesses.push(`Alım baskısı çok yüksek (%${buyPressure.toFixed(1)}) - FOMO olabilir`);
            } else if (buyPressure < 50) {
                weaknesses.push(`Alım baskısı zayıf (%${buyPressure.toFixed(1)}) - Satış baskısı var`);
            }

            // OBV
            if (obvTrend === 'UP') {
                strengths.push('OBV yukarı yönlü - Hacim akışı pozitif');
            } else {
                weaknesses.push('OBV aşağı yönlü - Hacim akışı negatif');
            }

            // Detaylı açıklama oluştur
            details = `
                <strong>Fiyat Konumu:</strong> Coin şu anda 30 günlük fiyat aralığının %${pricePos.toFixed(0)}'inde işlem görüyor.
                ${pricePos < 30 ? 'Bu dip bölgesidir ve giriş için ideal.' : pricePos > 70 ? 'Bu tepe bölgesidir, dikkatli olun!' : 'Bu orta bölgedir.'}
                <br><br>
                <strong>Hacim Analizi:</strong> Son 24 saatte hacim 7 günlük ortalamaya göre %${volIncrease.toFixed(1)} arttı.
                ${volIncrease > 100 ? 'Bu anormal bir hacim patlamasıdır ve büyük oyuncuların pozisyon aldığını gösterebilir.' : 'Normal hacim akışı.'}
                <br><br>
                <strong>Akümülasyon Göstergeleri:</strong> Alım baskısı %${buyPressure.toFixed(1)} seviyesinde.
                ${buyPressure >= 52 && buyPressure <= 58 ? 'Bu, whale\'lerin dikkat çekmeden gizlice topladığını gösterebilir.' : ''}
            `;

            // Tavsiye oluştur
            if (score >= 85 && pricePos < 40 && obvTrend === 'UP') {
                recommendation = `
                    <strong style="color: #10b981;">✅ GÜÇLÜ ALIM FIRSATı!</strong><br><br>
                    Bu coin güçlü akümülasyon göstergeleri sergiliyor. Ancak:<br>
                    • Kendi araştırmanızı yapın (DYOR)<br>
                    • Stop-loss belirleyin (örn. %${pricePos > 20 ? '10' : '15'} altında)<br>
                    • Portföyünüzün küçük bir kısmıyla girin<br>
                    • Hacim patlaması/breakout bekleyin<br><br>
                    <em>Risk Yönetimi: Her zaman dikkatli olun ve yatırım tavsiyesi değildir!</em>
                `;
            } else if (score >= 70 && weaknesses.length <= 2) {
                recommendation = `
                    <strong style="color: #3b82f6;">🟡 DİKKATLİ GİRİŞ ÖNERİSİ</strong><br><br>
                    Orta seviye bir fırsat. Girmek istiyorsanız:<br>
                    • Daha fazla onay bekleyin (grafik formasyonu vb.)<br>
                    • Küçük pozisyonla başlayın<br>
                    • Sıkı stop-loss kullanın<br><br>
                    ${weaknesses.length > 0 ? `<strong>Dikkat!</strong> ${weaknesses[0]}` : ''}
                `;
            } else {
                recommendation = `
                    <strong style="color: #f59e0b;">⚠️ BEKLE VE İZLE</strong><br><br>
                    Bu coin şu an için yeterince güçlü değil. Tavsiye:<br>
                    • Daha güçlü sinyaller bekleyin<br>
                    • Watch list'e ekleyip takip edin<br>
                    • Daha iyi fırsatlar arayın<br><br>
                    ${weaknesses.length > 0 ? `<strong>Sorunlar:</strong><br>• ${weaknesses.join('<br>• ')}` : ''}
                `;
            }

            return {
                strength,
                strengthColor,
                summary,
                details,
                strengths,
                weaknesses,
                recommendation
            };
        }

        async function refreshData() {
            const refreshBtn = document.querySelector('.btn-refresh');
            const loading = document.getElementById('loading');
            const cashflowContent = document.getElementById('cashflowData');
            const accumulationContent = document.getElementById('accumulationData');

            // Eğer Whale Signals tab'ındaysak, streaming kullan
            if (currentTab === 'accumulation') {
                startStreamingScan();
                return;
            }

            // Cash Flow için eski method
            // Ayarları kaydet
            saveSettings();

            // Butonu disable et
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '⏳ Yükleniyor...';

            // Loading göster
            loading.classList.add('active');
            cashflowContent.style.display = 'none';
            accumulationContent.style.display = 'none';

            try {
                const params = new URLSearchParams({
                    top_n: document.getElementById('topN').value,
                    volume_threshold: document.getElementById('volumeThreshold').value,
                    price_threshold: document.getElementById('priceThreshold').value,
                    buy_pressure_min: document.getElementById('buyPressureMin').value,
                    buy_pressure_max: document.getElementById('buyPressureMax').value,
                    trade_threshold: document.getElementById('tradeThreshold').value
                });

                const response = await fetch(`/api/refresh?${params}`);
                const data = await response.json();

                if (data.status === 'success') {
                    // Cash Flow sonuçları
                    cashflowContent.innerHTML = data.cashflow_html;

                    // Accumulation sonuçları
                    if (data.accumulation_signals && data.accumulation_signals.length > 0) {
                        let accHtml = '<h2 style="color: #667eea; margin-bottom: 20px;">🐋 Whale Akümülasyon Sinyalleri</h2>';
                        accHtml += '<div class="accumulation-grid">';

                        data.accumulation_signals.forEach(signal => {
                            const highScore = signal.accumulation_score >= 70;
                            const pricePos = signal.price_position || 50;
                            const priceChange30d = signal.price_change_30d || 0;
                            const positionLabel = pricePos < 30 ? '🟢DİP' : pricePos < 60 ? '🟡ORTA' : '🔴TEPE';

                            accHtml += `
                                <div class="accumulation-card ${highScore ? 'high-score' : ''}">
                                    <h3>${signal.symbol}</h3>
                                    <div class="score">${signal.accumulation_score.toFixed(1)}/100 ⭐</div>
                                    <div class="metrics">
                                        <div class="metric">
                                            <strong>Hacim:</strong>
                                            <span>$${signal.volume_24h.toLocaleString('en-US', {maximumFractionDigits: 0})}</span>
                                        </div>
                                        <div class="metric">
                                            <strong>Vol Artış:</strong>
                                            <span>${signal.volume_increase > 0 ? '+' : ''}${signal.volume_increase.toFixed(1)}% ${signal.volume_increase > 100 ? '🔥' : '📈'}</span>
                                        </div>
                                        <div class="metric">
                                            <strong>Fiyat 30d:</strong>
                                            <span>${priceChange30d > 0 ? '+' : ''}${priceChange30d.toFixed(1)}%</span>
                                        </div>
                                        <div class="metric">
                                            <strong>Pozisyon:</strong>
                                            <span>${pricePos.toFixed(0)}% ${positionLabel}</span>
                                        </div>
                                        <div class="metric">
                                            <strong>Fiyat 24h:</strong>
                                            <span>${signal.price_change > 0 ? '+' : ''}${signal.price_change.toFixed(2)}% ${Math.abs(signal.price_change) < 3 ? '✅' : '📊'}</span>
                                        </div>
                                        <div class="metric">
                                            <strong>Alım:</strong>
                                            <span>${signal.buy_pressure.toFixed(1)}% ${signal.buy_pressure >= 52 && signal.buy_pressure <= 58 ? '🟢' : '🟡'}</span>
                                        </div>
                                        <div class="metric">
                                            <strong>Trade:</strong>
                                            <span>+${signal.trade_count_increase.toFixed(1)}% ${signal.trade_count_increase > 50 ? '🔥' : '📈'}</span>
                                        </div>
                                        <div class="metric">
                                            <strong>OBV:</strong>
                                            <span>${signal.obv_trend}</span>
                                        </div>
                                    </div>
                                    <div class="criteria">
                                        ✅ Kriterler: ${signal.criteria_met.join(', ')}
                                    </div>
                                </div>
                            `;
                        });

                        accHtml += '</div>';
                        accumulationContent.innerHTML = accHtml;
                    } else {
                        accumulationContent.innerHTML = '<p class="empty-state">❌ Akümülasyon sinyali bulunamadı.<br>Kriterleri gevşeterek tekrar deneyin.</p>';
                    }

                    // Status bilgilerini güncelle
                    document.getElementById('lastUpdate').textContent = new Date().toLocaleString('tr-TR');
                    document.getElementById('riskLevel').textContent = data.risk.toUpperCase();
                    document.getElementById('dominance').textContent = `%${data.dominance}`;
                    document.getElementById('totalCoins').textContent = data.total_coins;
                    document.getElementById('whaleSignals').textContent = data.accumulation_count;

                    // Risk rengini ayarla
                    const riskElement = document.getElementById('riskLevel');
                    riskElement.style.color = data.risk === 'low' ? '#4CAF50' :
                                               data.risk === 'medium' ? '#FF9800' : '#f44336';
                } else {
                    cashflowContent.innerHTML = `<div class="error">❌ Hata: ${data.message}</div>`;
                    accumulationContent.innerHTML = `<div class="error">❌ Hata: ${data.message}</div>`;
                }
            } catch (error) {
                cashflowContent.innerHTML = `<div class="error">❌ Bağlantı hatası: ${error.message}</div>`;
                accumulationContent.innerHTML = `<div class="error">❌ Bağlantı hatası: ${error.message}</div>`;
            } finally {
                // Loading gizle
                loading.classList.remove('active');
                cashflowContent.style.display = 'block';
                accumulationContent.style.display = 'block';

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

        // İlk veri yüklemesi manuel - Kullanıcı "Yenile" butonuna basacak
        // Otomatik yükleme kaldırıldı (takılma sorunu)
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Ana sayfa"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/scan_stream')
def api_scan_stream():
    """REAL-TIME Accumulation Scan - Server-Sent Events (SSE)"""
    def generate():
        try:
            # Parametreleri al
            max_coins_param = request.args.get('max_coins', 0, type=int)
            volume_threshold = request.args.get('volume_threshold', 50.0, type=float)
            price_threshold = request.args.get('price_threshold', 5.0, type=float)
            buy_pressure_min = request.args.get('buy_pressure_min', 52.0, type=float)
            buy_pressure_max = request.args.get('buy_pressure_max', 60.0, type=float)
            trade_threshold = request.args.get('trade_threshold', 30.0, type=float)

            # max_coins: 0 = TÜM coinler (None), >0 = belirtilen sayı
            max_coins = None if max_coins_param == 0 else max_coins_param

            # STREAMING scan başlat
            for event in accumulation_detector.scan_stream(
                min_volume_usd=100000,
                max_coins=max_coins,
                volume_increase_threshold=volume_threshold,
                price_change_threshold=price_threshold,
                buy_pressure_min=buy_pressure_min,
                buy_pressure_max=buy_pressure_max,
                trade_count_threshold=trade_threshold
            ):
                # Server-Sent Events formatı
                yield f"data: {json.dumps(event)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@app.route('/api/refresh')
def api_refresh():
    """Veri yenileme API endpoint'i - Cash Flow + Accumulation"""
    try:
        # Parametreleri al
        top_n = request.args.get('top_n', 30, type=int)
        volume_threshold = request.args.get('volume_threshold', 50.0, type=float)
        price_threshold = request.args.get('price_threshold', 5.0, type=float)
        buy_pressure_min = request.args.get('buy_pressure_min', 52.0, type=float)
        buy_pressure_max = request.args.get('buy_pressure_max', 60.0, type=float)
        trade_threshold = request.args.get('trade_threshold', 30.0, type=float)

        # 1. Cash Flow Analizi
        cashflow_report = cash_flow_analyzer.analyze(top_n=top_n, timeframe='15m', format='html')

        if cashflow_report['status'] != 'success':
            return jsonify({
                'status': 'error',
                'message': cashflow_report.get('message', 'Cash flow analizi başarısız')
            })

        # 2. Accumulation Detection (OLD METHOD - artık streaming kullanılmalı)
        accumulation_result = accumulation_detector.scan(
            min_volume_usd=100000,
            max_coins=200,
            volume_increase_threshold=volume_threshold,
            price_change_threshold=price_threshold,
            buy_pressure_min=buy_pressure_min,
            buy_pressure_max=buy_pressure_max,
            trade_count_threshold=trade_threshold
        )

        # Sonuçları birleştir
        return jsonify({
            'status': 'success',
            'cashflow_html': cashflow_report['text_report'],
            'risk': cashflow_report['risk_assessment']['level'],
            'dominance': f"{cashflow_report['top_10_dominance']:.1f}",
            'total_coins': cashflow_report['total_coins'],
            'accumulation_signals': accumulation_result['signals'][:top_n],  # Top N göster
            'accumulation_count': len(accumulation_result['signals']),
            'timestamp': cashflow_report['timestamp']
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
    print("=" * 70)
    print("💰 Market Analyzer - Cash Flow & Whale Hunter")
    print("=" * 70)
    print()
    print("🌐 Server başlatılıyor...")
    print("📍 URL: http://localhost:5000")
    print()
    print("💡 Özellikler:")
    print("   - Cash Flow Analizi (nakit akışı, momentum)")
    print("   - Whale Hunter (akümülasyon tespiti)")
    print("   - İki analiz aynı anda çalışır!")
    print("   - Parametreleri UI'den ayarlayabilirsiniz")
    print()
    print("⏹️  Durdurmak için: Ctrl+C")
    print("=" * 70)
    print()

    # Browser'ı otomatik aç
    threading.Thread(target=open_browser, daemon=True).start()

    # Flask server başlat
    app.run(host='0.0.0.0', port=5000, debug=False)
