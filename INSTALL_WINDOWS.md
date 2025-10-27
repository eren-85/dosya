# Windows Kurulum Rehberi

## Python 3.12 için TA-Lib Kurulumu

TA-Lib Windows'ta C++ derlemesi gerektirdiği için binary wheel dosyası kullanmanız gerekiyor.

### Adım 1: TA-Lib Wheel Dosyasını İndirin

Python versiyonunuzu kontrol edin:
```powershell
python --version
# Örnek çıktı: Python 3.12.x
```

[Unofficial Windows Binaries](https://github.com/cgohlke/talib-build/releases) sayfasından Python versiyonunuza uygun wheel dosyasını indirin:

**Python 3.12 için:**
- `TA_Lib‑0.4.32‑cp312‑cp312‑win_amd64.whl`

**Python 3.11 için:**
- `TA_Lib‑0.4.32‑cp311‑cp311‑win_amd64.whl`

**Python 3.10 için:**
- `TA_Lib‑0.4.32‑cp310‑cp310‑win_amd64.whl`

### Adım 2: TA-Lib'i Manuel Kurun

İndirilen wheel dosyasının bulunduğu dizinde:

```powershell
pip install TA_Lib-0.4.32-cp312-cp312-win_amd64.whl
```

### Adım 3: Diğer Paketleri Kurun

```powershell
pip install -r requirements.txt
```

## Alternatif: TA-Lib Olmadan Kurulum

Eğer TA-Lib kurulumunda sorun yaşıyorsanız, pandas-ta kütüphanesi çoğu teknik indikatörü destekler:

```powershell
# requirements.txt'ten ta-lib satırını yoruma alın veya atlayın
pip install -r requirements.txt
```

Sistemde sadece pandas-ta kullanılacaktır (200+ indikatör içerir).

## Tam Kurulum Süreci

```powershell
# 1. Virtual environment oluştur
python -m venv venv

# 2. Virtual environment'ı aktif et
.\venv\Scripts\activate

# 3. Pip'i güncelle
python -m pip install --upgrade pip

# 4. TA-Lib wheel'i kur (indirdiğiniz dizinde)
pip install TA_Lib-0.4.32-cp312-cp312-win_amd64.whl

# 5. Diğer paketleri kur
pip install -r requirements.txt

# 6. Kurulumu test et
python -c "import talib; import pandas_ta; print('✅ TA-Lib ve Pandas-TA başarıyla kuruldu!')"
```

## Yaygın Hatalar ve Çözümler

### Hata: "Could not find a version that satisfies the requirement ta-lib"

**Çözüm:** Binary wheel dosyasını manuel olarak kurmanız gerekiyor (yukarıdaki adımları takip edin).

### Hata: "pandas-ta==0.3.14b0 bulunamıyor"

**Çözüm:** requirements.txt güncellenmiş durumda, `pandas-ta==0.4.71b0` kullanıyor.

### Hata: Python versiyonu uyumsuzluğu

**Çözüm:** Python 3.10, 3.11 veya 3.12 kullanın. `python --version` ile kontrol edin.

### Hata: "Microsoft Visual C++ 14.0 or greater is required"

**Çözüm:** Binary wheel kullanarak bu hatayı atlayabilirsiniz. Eğer kaynak koddan derlemeniz gerekirse:
- [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) indirin ve kurun

## PostgreSQL & Redis Kurulumu (Docker ile)

```powershell
# Docker Desktop'ın kurulu olduğundan emin olun
docker --version

# Veritabanlarını başlat
docker-compose up -d postgres redis

# Durumu kontrol et
docker-compose ps
```

## Sorun Giderme

### TA-Lib import hatası

```python
# Eğer TA-Lib kurulmadıysa, backend/data/processors/technical_indicators.py
# içinde pandas-ta fallback'i otomatik olarak devreye girer
```

### Paket çakışmaları

```powershell
# Temiz kurulum için venv'i sil ve yeniden oluştur
deactivate
Remove-Item -Recurse -Force venv
python -m venv venv
.\venv\Scripts\activate
pip install --upgrade pip
# Kurulum adımlarını tekrarla
```

## Doğrulama

Kurulum tamamlandıktan sonra:

```powershell
python -c "
import fastapi
import pandas
import numpy
import torch
import ccxt
import anthropic
print('✅ Tüm kritik paketler başarıyla yüklendi!')
print(f'FastAPI: {fastapi.__version__}')
print(f'Pandas: {pandas.__version__}')
print(f'PyTorch: {torch.__version__}')
"
```

## Ek Kaynaklar

- [TA-Lib GitHub](https://github.com/TA-Lib/ta-lib-python)
- [Unofficial Windows Binaries](https://www.lfd.uci.edu/~gohlke/pythonlibs/)
- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)

## Destek

Sorun yaşarsanız, GitHub Issues'a detaylı hata mesajı ile birlikte bildirebilirsiniz.
