/**
 * Simple i18n (internationalization) system
 * Supports Turkish and English
 */

export type Language = 'en' | 'tr';

export interface Translations {
  // Navigation
  nav: {
    dashboard: string;
    downloadData: string;
    trainModels: string;
    aiAnalysis: string;
    backtest: string;
    advancedChart: string;
    portfolio: string;
    pdfLearning: string;
  };

  // Common
  common: {
    loading: string;
    error: string;
    success: string;
    cancel: string;
    save: string;
    delete: string;
    edit: string;
    add: string;
    refresh: string;
    close: string;
    search: string;
    settings: string;
    language: string;
  };

  // Dashboard
  dashboard: {
    title: string;
    subtitle: string;
    marketCap: string;
    btcDominance: string;
    altcoinMarketCap: string;
    quickSelect: string;
    customSymbols: string;
    customSymbolsPlaceholder: string;
    selectCoins: string;
  };

  // Download Data
  download: {
    title: string;
    subtitle: string;
    symbols: string;
    interval: string;
    market: string;
    dateRange: string;
    allTime: string;
    customRange: string;
    startDate: string;
    endDate: string;
    download: string;
    downloading: string;
    spot: string;
    futures: string;
    quickSelect: string;
    customSymbols: string;
    customSymbolsPlaceholder: string;
    configuration: string;
    configDescription: string;
    startDownload: string;
    downloadProgress: string;
    successMessage: string;
    errorMessage: string;
    noOutputYet: string;
    availableTimeframes: string;
  };

  // Training
  training: {
    title: string;
    subtitle: string;
    symbols: string;
    timeframes: string;
    modelType: string;
    epochs: string;
    useGPU: string;
    startTraining: string;
    training: string;
    trainingLog: string;
    allModels: string;
    ensemble: string;
    lstm: string;
    transformer: string;
    ppo: string;
    gpuRecommended: string;
    gpuRequired: string;
  };

  // AI Analysis
  analysis: {
    title: string;
    subtitle: string;
    marketBias: string;
    confidence: string;
    summary: string;
    tradingSignal: string;
    action: string;
    entry: string;
    stopLoss: string;
    takeProfit: string;
    riskReward: string;
    conclusion: string;
    technicalAnalysis: string;
    riskAssessment: string;
    riskLevel: string;
    positionSize: string;
  };

  // Portfolio
  portfolio: {
    title: string;
    subtitle: string;
    realPortfolio: string;
    paperTrading: string;
    totalValue: string;
    totalCost: string;
    totalPnL: string;
    pnlPercent: string;
    addCoin: string;
    myHoldings: string;
    noHoldings: string;
    coin: string;
    amount: string;
    avgBuy: string;
    current: string;
    value: string;
    actions: string;
    exposure: string;
    addHolding: string;
    editHolding: string;
    symbol: string;
    exchange: string;
    marketType: string;
    avgBuyPrice: string;
    updateHolding: string;
  };

  // Advanced Chart
  chart: {
    title: string;
    subtitle: string;
    chartControls: string;
    fitContent: string;
    fullscreen: string;
    exitFullscreen: string;
    patterns: string;
    symbol: string;
    timeframe: string;
    loadChart: string;
    patternLegend: string;
    orderBlocks: string;
    fairValueGaps: string;
    liquiditySweeps: string;
    breakOfStructure: string;
  };

  // PDF Learning
  pdfLearning: {
    title: string;
    subtitle: string;
    uploadPDFs: string;
    uploadDescription: string;
    uploading: string;
    clickToUpload: string;
    supportedFormats: string;
    uploadedDocuments: string;
    manageDocuments: string;
    askQuestions: string;
    askDescription: string;
    askPlaceholder: string;
    aiThinking: string;
    noMessages: string;
    exampleQuestions: string;
  };

  // Backtest
  backtest: {
    title: string;
    subtitle: string;
    strategy: string;
    symbols: string;
    timeframe: string;
    dateRange: string;
    startDate: string;
    endDate: string;
    initialCapital: string;
    positionSize: string;
    commission: string;
    runBacktest: string;
    running: string;
    results: string;
    noResults: string;
    totalReturn: string;
    sharpeRatio: string;
    maxDrawdown: string;
    winRate: string;
    totalTrades: string;
  };
}

export const translations: Record<Language, Translations> = {
  en: {
    nav: {
      dashboard: 'Dashboard',
      downloadData: 'Download Data',
      trainModels: 'Train Models',
      aiAnalysis: 'AI Analysis',
      backtest: 'Backtest',
      advancedChart: 'Advanced Chart',
      portfolio: 'Portfolio',
      pdfLearning: 'PDF Learning',
    },
    common: {
      loading: 'Loading...',
      error: 'Error',
      success: 'Success',
      cancel: 'Cancel',
      save: 'Save',
      delete: 'Delete',
      edit: 'Edit',
      add: 'Add',
      refresh: 'Refresh',
      close: 'Close',
      search: 'Search',
      settings: 'Settings',
      language: 'Language',
    },
    dashboard: {
      title: 'Dashboard',
      subtitle: 'Multi-coin tracking with AI-powered predictions',
      marketCap: 'Total Market Cap',
      btcDominance: 'BTC Dominance',
      altcoinMarketCap: 'Altcoin Market Cap',
      quickSelect: 'Quick Select',
      customSymbols: 'Custom Symbols',
      customSymbolsPlaceholder: 'Add custom symbols (e.g., ADAUSDT, DOTUSDT)',
      selectCoins: 'Select coins to track',
    },
    download: {
      title: 'Download Data',
      subtitle: 'Download historical OHLCV data from Binance',
      symbols: 'Symbols',
      interval: 'Interval',
      market: 'Market',
      dateRange: 'Date Range',
      allTime: 'All-Time',
      customRange: 'Custom Range',
      startDate: 'Start Date',
      endDate: 'End Date',
      download: 'Download',
      downloading: 'Downloading...',
      spot: 'Spot',
      futures: 'Futures',
      quickSelect: 'Quick Select',
      customSymbols: 'Custom Symbols',
      customSymbolsPlaceholder: 'Add custom symbols (comma separated)',
      configuration: 'Download Configuration',
      configDescription: 'Select market type, symbols, exchange, and timeframes',
      startDownload: 'Start Download',
      downloadProgress: 'Download Progress',
      successMessage: 'Data download completed successfully! You can now train models with this data.',
      errorMessage: 'Download failed. Please check the logs and try again.',
      noOutputYet: 'No output yet. Click "Start Download" to begin.',
      availableTimeframes: 'Available',
    },
    training: {
      title: 'Train Models',
      subtitle: 'Train machine learning models on historical data',
      symbols: 'Symbols',
      timeframes: 'Timeframes',
      modelType: 'Model Type',
      epochs: 'Epochs',
      useGPU: 'Use GPU',
      startTraining: 'Start Training',
      training: 'Training...',
      trainingLog: 'Training Log',
      allModels: 'All Models (Sequential)',
      ensemble: 'Ensemble',
      lstm: 'LSTM',
      transformer: 'Transformer',
      ppo: 'PPO (RL)',
      gpuRecommended: 'GPU Recommended',
      gpuRequired: 'GPU Required',
    },
    analysis: {
      title: 'AI Analysis',
      subtitle: 'Real-time AI predictions and market analysis',
      marketBias: 'Market Bias',
      confidence: 'Confidence',
      summary: 'Summary',
      tradingSignal: 'Trading Signal',
      action: 'Action',
      entry: 'Entry',
      stopLoss: 'Stop Loss',
      takeProfit: 'Take Profit',
      riskReward: 'Risk/Reward',
      conclusion: 'Conclusion',
      technicalAnalysis: 'Technical Analysis',
      riskAssessment: 'Risk Assessment',
      riskLevel: 'Risk Level',
      positionSize: 'Position Size',
    },
    portfolio: {
      title: 'Portfolio',
      subtitle: 'Track your real holdings and AI-powered paper trading',
      realPortfolio: 'Real Portfolio',
      paperTrading: 'Paper Trading',
      totalValue: 'Total Value',
      totalCost: 'Total Cost',
      totalPnL: 'Total P&L',
      pnlPercent: 'P&L %',
      addCoin: 'Add Coin',
      myHoldings: 'My Holdings',
      noHoldings: 'No holdings yet. Click "Add Coin" to start tracking.',
      coin: 'Coin',
      amount: 'Amount',
      avgBuy: 'Avg Buy',
      current: 'Current',
      value: 'Value',
      actions: 'Actions',
      exposure: 'Exposure Breakdown',
      addHolding: 'Add Holding',
      editHolding: 'Edit Holding',
      symbol: 'Symbol',
      exchange: 'Exchange',
      marketType: 'Market Type',
      avgBuyPrice: 'Average Buy Price ($)',
      updateHolding: 'Update Holding',
    },
    chart: {
      title: 'Advanced Chart',
      subtitle: 'Professional charting with pattern detection and technical indicators',
      chartControls: 'Chart Controls',
      fitContent: 'Fit Content',
      fullscreen: 'Fullscreen',
      exitFullscreen: 'Exit Fullscreen',
      patterns: 'Patterns',
      symbol: 'Symbol',
      timeframe: 'Timeframe',
      loadChart: 'Load Chart',
      patternLegend: 'Pattern Legend & Indicators',
      orderBlocks: 'Order Blocks',
      fairValueGaps: 'Fair Value Gaps',
      liquiditySweeps: 'Liquidity Sweeps',
      breakOfStructure: 'Break of Structure',
    },
    pdfLearning: {
      title: 'PDF Learning (RAG)',
      subtitle: 'Upload PDF documents and ask questions using AI-powered retrieval',
      uploadPDFs: 'Upload PDFs',
      uploadDescription: 'Upload technical analysis books, research papers, or trading guides',
      uploading: 'Uploading...',
      clickToUpload: 'Click to upload PDFs',
      supportedFormats: 'Supports multiple files, max 50MB each',
      uploadedDocuments: 'Uploaded Documents',
      manageDocuments: 'Manage your PDF knowledge base',
      askQuestions: 'Ask Questions',
      askDescription: 'Ask questions about your uploaded PDFs using AI',
      askPlaceholder: 'Ask a question about your PDFs...',
      aiThinking: 'AI is thinking...',
      noMessages: 'Upload PDFs and start asking questions.',
      exampleQuestions: 'Try: "What are the key support and resistance concepts?" or "Explain the Elliott Wave Theory"',
    },
    backtest: {
      title: 'Backtest',
      subtitle: 'Test trading strategies on historical data',
      strategy: 'Strategy',
      symbols: 'Symbols',
      timeframe: 'Timeframe',
      dateRange: 'Date Range',
      startDate: 'Start Date',
      endDate: 'End Date',
      initialCapital: 'Initial Capital',
      positionSize: 'Position Size %',
      commission: 'Commission %',
      runBacktest: 'Run Backtest',
      running: 'Running...',
      results: 'Results',
      noResults: 'No results yet. Configure and run a backtest.',
      totalReturn: 'Total Return',
      sharpeRatio: 'Sharpe Ratio',
      maxDrawdown: 'Max Drawdown',
      winRate: 'Win Rate',
      totalTrades: 'Total Trades',
    },
  },
  tr: {
    nav: {
      dashboard: 'Gösterge Paneli',
      downloadData: 'Veri İndir',
      trainModels: 'Model Eğit',
      aiAnalysis: 'AI Analiz',
      backtest: 'Geri Test',
      advancedChart: 'Gelişmiş Grafik',
      portfolio: 'Portföy',
      pdfLearning: 'PDF Öğrenme',
    },
    common: {
      loading: 'Yükleniyor...',
      error: 'Hata',
      success: 'Başarılı',
      cancel: 'İptal',
      save: 'Kaydet',
      delete: 'Sil',
      edit: 'Düzenle',
      add: 'Ekle',
      refresh: 'Yenile',
      close: 'Kapat',
      search: 'Ara',
      settings: 'Ayarlar',
      language: 'Dil',
    },
    dashboard: {
      title: 'Gösterge Paneli',
      subtitle: 'AI destekli tahminlerle çoklu coin takibi',
      marketCap: 'Toplam Piyasa Değeri',
      btcDominance: 'BTC Dominansı',
      altcoinMarketCap: 'Altcoin Piyasa Değeri',
      quickSelect: 'Hızlı Seçim',
      customSymbols: 'Özel Semboller',
      customSymbolsPlaceholder: 'Özel sembol ekle (örn: ADAUSDT, DOTUSDT)',
      selectCoins: 'Takip edilecek coinleri seçin',
    },
    download: {
      title: 'Veri İndir',
      subtitle: 'Binance\'den geçmiş OHLCV verilerini indirin',
      symbols: 'Semboller',
      interval: 'Aralık',
      market: 'Piyasa',
      dateRange: 'Tarih Aralığı',
      allTime: 'Tüm Zamanlar',
      customRange: 'Özel Aralık',
      startDate: 'Başlangıç Tarihi',
      endDate: 'Bitiş Tarihi',
      download: 'İndir',
      downloading: 'İndiriliyor...',
      spot: 'Spot',
      futures: 'Vadeli',
      quickSelect: 'Hızlı Seçim',
      customSymbols: 'Özel Semboller',
      customSymbolsPlaceholder: 'Özel sembol ekle (virgülle ayırın)',
      configuration: 'İndirme Yapılandırması',
      configDescription: 'Piyasa türü, sembol, borsa ve zaman dilimlerini seçin',
      startDownload: 'İndirmeyi Başlat',
      downloadProgress: 'İndirme İlerlemesi',
      successMessage: 'Veri indirme başarıyla tamamlandı! Artık bu verilerle model eğitebilirsiniz.',
      errorMessage: 'İndirme başarısız oldu. Lütfen günlükleri kontrol edin ve tekrar deneyin.',
      noOutputYet: 'Henüz çıktı yok. Başlamak için "İndirmeyi Başlat" düğmesine tıklayın.',
      availableTimeframes: 'Mevcut',
    },
    training: {
      title: 'Model Eğit',
      subtitle: 'Geçmiş veriler üzerinde makine öğrenmesi modelleri eğitin',
      symbols: 'Semboller',
      timeframes: 'Zaman Dilimleri',
      modelType: 'Model Tipi',
      epochs: 'Epoch Sayısı',
      useGPU: 'GPU Kullan',
      startTraining: 'Eğitimi Başlat',
      training: 'Eğitiliyor...',
      trainingLog: 'Eğitim Günlüğü',
      allModels: 'Tüm Modeller (Sıralı)',
      ensemble: 'Ensemble',
      lstm: 'LSTM',
      transformer: 'Transformer',
      ppo: 'PPO (RL)',
      gpuRecommended: 'GPU Önerilir',
      gpuRequired: 'GPU Gerekli',
    },
    analysis: {
      title: 'AI Analiz',
      subtitle: 'Gerçek zamanlı AI tahminleri ve piyasa analizi',
      marketBias: 'Piyasa Eğilimi',
      confidence: 'Güven',
      summary: 'Özet',
      tradingSignal: 'İşlem Sinyali',
      action: 'Aksiyon',
      entry: 'Giriş',
      stopLoss: 'Zarar Durdur',
      takeProfit: 'Kar Al',
      riskReward: 'Risk/Ödül',
      conclusion: 'Sonuç',
      technicalAnalysis: 'Teknik Analiz',
      riskAssessment: 'Risk Değerlendirmesi',
      riskLevel: 'Risk Seviyesi',
      positionSize: 'Pozisyon Boyutu',
    },
    portfolio: {
      title: 'Portföy',
      subtitle: 'Gerçek varlıklarınızı ve AI destekli kağıt ticaretinizi takip edin',
      realPortfolio: 'Gerçek Portföy',
      paperTrading: 'Kağıt Ticaret',
      totalValue: 'Toplam Değer',
      totalCost: 'Toplam Maliyet',
      totalPnL: 'Toplam Kar/Zarar',
      pnlPercent: 'Kar/Zarar %',
      addCoin: 'Coin Ekle',
      myHoldings: 'Varlıklarım',
      noHoldings: 'Henüz varlık yok. Takip başlatmak için "Coin Ekle" tıklayın.',
      coin: 'Coin',
      amount: 'Miktar',
      avgBuy: 'Ort. Alış',
      current: 'Güncel',
      value: 'Değer',
      actions: 'İşlemler',
      exposure: 'Dağılım',
      addHolding: 'Varlık Ekle',
      editHolding: 'Varlık Düzenle',
      symbol: 'Sembol',
      exchange: 'Borsa',
      marketType: 'Piyasa Tipi',
      avgBuyPrice: 'Ortalama Alış Fiyatı ($)',
      updateHolding: 'Varlığı Güncelle',
    },
    chart: {
      title: 'Gelişmiş Grafik',
      subtitle: 'Patern tespiti ve teknik göstergelerle profesyonel grafik',
      chartControls: 'Grafik Kontrolleri',
      fitContent: 'İçeriğe Sığdır',
      fullscreen: 'Tam Ekran',
      exitFullscreen: 'Tam Ekrandan Çık',
      patterns: 'Paternler',
      symbol: 'Sembol',
      timeframe: 'Zaman Dilimi',
      loadChart: 'Grafik Yükle',
      patternLegend: 'Patern Açıklaması & Göstergeler',
      orderBlocks: 'Emir Blokları',
      fairValueGaps: 'Adil Değer Boşlukları',
      liquiditySweeps: 'Likidite Süpürmeleri',
      breakOfStructure: 'Yapı Kırılması',
    },
    pdfLearning: {
      title: 'PDF Öğrenme (RAG)',
      subtitle: 'PDF belgeleri yükleyin ve AI destekli sorgulama yapın',
      uploadPDFs: 'PDF Yükle',
      uploadDescription: 'Teknik analiz kitapları, araştırma makaleleri veya işlem rehberleri yükleyin',
      uploading: 'Yükleniyor...',
      clickToUpload: 'PDF yüklemek için tıklayın',
      supportedFormats: 'Birden fazla dosya desteklenir, her biri max 50MB',
      uploadedDocuments: 'Yüklenen Belgeler',
      manageDocuments: 'PDF bilgi tabanınızı yönetin',
      askQuestions: 'Soru Sorun',
      askDescription: 'Yüklediğiniz PDF\'ler hakkında AI kullanarak soru sorun',
      askPlaceholder: 'PDF\'leriniz hakkında bir soru sorun...',
      aiThinking: 'AI düşünüyor...',
      noMessages: 'PDF yükleyin ve soru sormaya başlayın.',
      exampleQuestions: 'Örnek: "Anahtar destek ve direnç kavramları nelerdir?" veya "Elliott Dalga Teorisi\'ni açıklayın"',
    },
    backtest: {
      title: 'Geri Test',
      subtitle: 'Geçmiş veriler üzerinde işlem stratejilerini test edin',
      strategy: 'Strateji',
      symbols: 'Semboller',
      timeframe: 'Zaman Dilimi',
      dateRange: 'Tarih Aralığı',
      startDate: 'Başlangıç Tarihi',
      endDate: 'Bitiş Tarihi',
      initialCapital: 'Başlangıç Sermayesi',
      positionSize: 'Pozisyon Boyutu %',
      commission: 'Komisyon %',
      runBacktest: 'Geri Test Başlat',
      running: 'Çalışıyor...',
      results: 'Sonuçlar',
      noResults: 'Henüz sonuç yok. Yapılandırın ve bir geri test çalıştırın.',
      totalReturn: 'Toplam Getiri',
      sharpeRatio: 'Sharpe Oranı',
      maxDrawdown: 'Maksimum Düşüş',
      winRate: 'Kazanma Oranı',
      totalTrades: 'Toplam İşlem',
    },
  },
};

// Get translation for current language
export function getTranslations(language: Language): Translations {
  return translations[language];
}

// Storage key for language preference
export const LANGUAGE_STORAGE_KEY = 'dosya_app_language';

// Get saved language or default to English
export function getSavedLanguage(): Language {
  try {
    const saved = localStorage.getItem(LANGUAGE_STORAGE_KEY);
    if (saved === 'tr' || saved === 'en') {
      return saved;
    }
  } catch (error) {
    console.error('Failed to load language from localStorage:', error);
  }
  return 'en';
}

// Save language preference
export function saveLanguage(language: Language): void {
  try {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  } catch (error) {
    console.error('Failed to save language to localStorage:', error);
  }
}
