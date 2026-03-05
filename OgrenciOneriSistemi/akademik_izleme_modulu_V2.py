from __future__ import annotations
import datetime
import statistics
from typing import List, Dict, Tuple, Any, Optional

# Veri Analizi ve Görselleştirme Kütüphaneleri
try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import PolynomialFeatures
    from sklearn.metrics import r2_score
    from scipy import stats  # İstatistiksel hesaplamalar için eklendi
    from math import pi

    LIBRARIES_AVAILABLE = True
except ImportError:
    LIBRARIES_AVAILABLE = False
    print("UYARI: Gerekli kütüphaneler (pandas, matplotlib, seaborn, numpy, sklearn, scipy) eksik.")


# -----------------------------------------------------------------------------
# YARDIMCI FONKSİYONLAR (JSON GÜVENLİĞİ)
# -----------------------------------------------------------------------------

def _safe_float(val: Any) -> Optional[float]:
    """
    Değeri güvenli bir float'a çevirir. NaN veya Infinity ise None döner.
    JSON serileştirme hatalarını (Out of range float values) önler.
    """
    if val is None:
        return None
    try:
        # Numpy tiplerini python float'a çevir
        f_val = float(val)
        # NaN ve Infinity kontrolü
        if np.isnan(f_val) or np.isinf(f_val):
            return None
        return f_val
    except (ValueError, TypeError):
        return None


# -----------------------------------------------------------------------------
# 1. VERİ YAPILARI (DATA STRUCTURES)
# -----------------------------------------------------------------------------

class DersSonuc:
    """Tek bir dersin sonuçlarını tutar."""

    def __init__(self, ders_adi: str, dogru: int, yanlis: int, bos: int):
        self.ders_adi = ders_adi
        self.dogru = dogru
        self.yanlis = yanlis
        self.bos = bos

    @property
    def net(self) -> float:
        return self.dogru - (self.yanlis * 0.25)

    @property
    def toplam_soru(self) -> int:
        return self.dogru + self.yanlis + self.bos

    @property
    def basari_orani(self) -> float:
        if self.toplam_soru == 0:
            return 0.0
        return (self.dogru / self.toplam_soru) * 100


class DenemeSinavi:
    """Bir deneme sınavının tamamını tutar."""

    def __init__(self, ad: str, tarih: str):
        self.ad = ad
        self.tarih = tarih
        self.dersler: Dict[str, DersSonuc] = {}

    def ders_ekle(self, ders: DersSonuc):
        self.dersler[ders.ders_adi] = ders

    def toplam_net(self) -> float:
        return sum(d.net for d in self.dersler.values())


# -----------------------------------------------------------------------------
# 2. İSTATİSTİK MOTORU (Calculation Layer - API Helper)
# -----------------------------------------------------------------------------

class IstatistikMotoru:
    """API ve Analiz için saf istatistiksel hesaplamalar yapar."""

    @staticmethod
    def temel_istatistikler(seri: pd.Series) -> Dict[str, Optional[float]]:
        if len(seri) == 0: return {}
        # Tüm hesaplamalar _safe_float ile sarmalandı
        return {
            "Ortalama": _safe_float(seri.mean()),
            "Medyan": _safe_float(seri.median()),
            "StdSapma": _safe_float(seri.std(ddof=0)),
            "Min": _safe_float(seri.min()),
            "Max": _safe_float(seri.max()),
            "Carpiklik": _safe_float(seri.skew()) if len(seri) > 2 else 0.0,
            "Basiklik": _safe_float(seri.kurt()) if len(seri) > 2 else 0.0,
        }

    @staticmethod
    def yuzdelik_dilim_hesapla(gecmis_netler: List[float], son_net: float) -> Optional[float]:
        """Son netin geçmiş içindeki yüzdelik dilimi (Percentile Rank)."""
        if not gecmis_netler: return 100.0
        try:
            val = stats.percentileofscore(gecmis_netler, son_net, kind='weak')
            return _safe_float(val)
        except:
            return None

    @staticmethod
    def korelasyon_analizi(df: pd.DataFrame) -> Dict[str, Dict[str, Optional[float]]]:
        """Dersler arası korelasyon matrisi."""
        if df.empty: return {}
        pivot = df.pivot(index="DenemeIndex", columns="Ders", values="Net")
        if len(pivot) < 3: return {}

        corr_matrix = pivot.corr(method='pearson').fillna(0)
        # NaN değerleri temizle
        return corr_matrix.applymap(lambda x: _safe_float(x)).to_dict()

    @staticmethod
    def momentum_serisi(netler: List[float]) -> int:
        """Ardışık artış veya azalış serisi (Streak)."""
        if len(netler) < 2: return 0
        streak = 0
        yon = 0  # 1: Artış, -1: Düşüş

        for i in range(len(netler) - 1, 0, -1):
            fark = netler[i] - netler[i - 1]
            if fark > 0:
                if yon == -1: break
                yon = 1
                streak += 1
            elif fark < 0:
                if yon == 1: break
                yon = -1
                streak -= 1
            else:
                break
        return streak * yon


# -----------------------------------------------------------------------------
# 3. ANALİZ MOTORU (VERİ İŞLEME & API RESPONSE)
# -----------------------------------------------------------------------------

class AnalizMotoru:
    def __init__(self, denemeler: List[DenemeSinavi]):
        self.denemeler = denemeler or []
        self.satirlar = self._satirlar_olustur()
        self.df = self._dataframe_olustur()

    def _satirlar_olustur(self) -> List[Dict[str, Any]]:
        data: List[Dict[str, Any]] = []
        if not self.denemeler:
            return data

        for i, deneme in enumerate(self.denemeler):
            for ders_adi, sonuc in deneme.dersler.items():
                data.append({
                    "DenemeIndex": i + 1,
                    "Deneme": deneme.ad,
                    "Tarih": deneme.tarih,
                    "Ders": ders_adi,
                    "Dogru": sonuc.dogru,
                    "Yanlis": sonuc.yanlis,
                    "Bos": sonuc.bos,
                    "Net": sonuc.net,
                    "BasariOrani": sonuc.basari_orani,
                    "ToplamNet": deneme.toplam_net()
                })
        return data

    def _dataframe_olustur(self):
        if not LIBRARIES_AVAILABLE or not self.satirlar:
            return None
        return pd.DataFrame(self.satirlar)

    def get_api_response_model(self) -> Dict[str, Any]:
        """
        API'ye (FastAPI) dönecek JSON uyumlu veri yapısını hazırlar.
        Tüm numpy/pandas tiplerini native python tiplerine dönüştürür.
        """
        if self.df is None or self.df.empty:
            return {"error": "Analiz edilecek veri yok."}

        # 1. Genel Özet Verileri
        ozet_df = self.df.groupby(["DenemeIndex", "Deneme", "Tarih"])["Net"].sum().reset_index().sort_values(
            "DenemeIndex")
        netler = ozet_df["Net"].tolist()

        genel_istatistik = IstatistikMotoru.temel_istatistikler(ozet_df["Net"])
        son_net = _safe_float(netler[-1])
        percentile = IstatistikMotoru.yuzdelik_dilim_hesapla(netler, son_net if son_net is not None else 0.0)
        streak = IstatistikMotoru.momentum_serisi(netler)

        # 2. Ders Bazlı Detaylar
        ders_detaylari = {}
        dersler = self.df["Ders"].unique()

        for ders in dersler:
            d_df = self.df[self.df["Ders"] == ders].sort_values("DenemeIndex")
            d_netler = d_df["Net"].tolist()

            # Ders trendi (basit slope)
            x = np.arange(len(d_netler))
            slope = 0.0
            if len(d_netler) > 1:
                slope = float(np.polyfit(x, d_netler, 1)[0])

            ders_detaylari[ders] = {
                "istatistikler": IstatistikMotoru.temel_istatistikler(d_df["Net"]),
                "trend_egimi": _safe_float(slope),
                "son_net": _safe_float(d_netler[-1]),
                "ortalama_basari_orani": _safe_float(d_df["BasariOrani"].mean()),
                "net_gecmisi": [_safe_float(n) for n in d_netler]
            }

        # 3. Gelecek Tahmini
        tahmin = TahminMotoru.gelecek_tahmini_yap(self.df)

        # Güvenli erişim ve tip dönüşümü
        gelecek_net = None
        if tahmin.get("Durum") == "Basarili" and "Tahminler" in tahmin:
            val = tahmin["Tahminler"]
            # Liste ise ilk eleman, değilse kendisi
            gelecek_net = _safe_float(val[0] if isinstance(val, (list, np.ndarray)) else val)

        guven_alt = None
        if tahmin.get("Durum") == "Basarili" and "GuvenAraligiAlt" in tahmin:
            val = tahmin["GuvenAraligiAlt"]
            guven_alt = _safe_float(val[0] if isinstance(val, (list, np.ndarray)) else val)

        guven_ust = None
        if tahmin.get("Durum") == "Basarili" and "GuvenAraligiUst" in tahmin:
            val = tahmin["GuvenAraligiUst"]
            guven_ust = _safe_float(val[0] if isinstance(val, (list, np.ndarray)) else val)

        # 4. Final Yapı
        return {
            "meta": {
                "toplam_deneme_sayisi": len(netler),
                "analiz_tarihi": datetime.datetime.now().isoformat(),
                "son_deneme_tarihi": str(ozet_df.iloc[-1]["Tarih"])
            },
            "genel_performans": {
                "net_gecmisi": [_safe_float(n) for n in netler],
                "deneme_isimleri": ozet_df["Deneme"].tolist(),
                "temel_istatistikler": genel_istatistik,
                "son_durum": {
                    "son_net": son_net,
                    "yuzdelik_sira": percentile,
                    "momentum_serisi": streak
                }
            },
            "ders_analizleri": ders_detaylari,
            "iliskisel_analizler": {
                "ders_korelasyonlari": IstatistikMotoru.korelasyon_analizi(self.df)
            },
            "gelecek_projeksiyonu": {
                "durum": tahmin.get("Durum"),
                "tahmin_modeli": tahmin.get("SecilenModel"),
                "r2_skoru": _safe_float(tahmin["R2_Skoru"]) if tahmin.get("R2_Skoru") is not None else 0.0,
                "beklenen_gelecek_net": gelecek_net,
                "guven_araligi": {
                    "alt": guven_alt,
                    "ust": guven_ust
                }
            }
        }


# -----------------------------------------------------------------------------
# 4. TAHMİN MOTORU (REGRESSION ENGINE)
# -----------------------------------------------------------------------------

class TahminMotoru:
    """Gelecek sınavlar için net tahmini yapar (Regresyon Modelleri)."""

    @staticmethod
    def gelecek_tahmini_yap(df: pd.DataFrame, gelecek_adim: int = 3) -> Dict[str, Any]:
        ozet_df = (
            df.groupby(["DenemeIndex", "Deneme", "Tarih"])["Net"]
            .sum()
            .reset_index()
            .sort_values("DenemeIndex")
        )
        X = ozet_df["DenemeIndex"].values.reshape(-1, 1)
        y = ozet_df["Net"].values

        if len(X) < 3:
            return {"Durum": "Yetersiz Veri", "Mesaj": "Tahmin için en az 3 sınav verisi gereklidir."}

        # 1. Lineer
        lin_reg = LinearRegression()
        lin_reg.fit(X, y)
        y_pred_lin = lin_reg.predict(X)
        r2_lin = r2_score(y, y_pred_lin)

        # 2. Polinom
        poly = PolynomialFeatures(degree=2)
        X_poly = poly.fit_transform(X)
        poly_reg = LinearRegression()
        poly_reg.fit(X_poly, y)
        y_pred_poly = poly_reg.predict(X_poly)
        r2_poly = r2_score(y, y_pred_poly)

        if r2_poly > r2_lin + 0.05:
            secilen_model = "Polinom (Eğrisel)"
            model = poly_reg
            transform = poly
            r2 = r2_poly
        else:
            secilen_model = "Lineer (Doğrusal)"
            model = lin_reg
            transform = None
            r2 = r2_lin

        son_index = X[-1][0]
        gelecek_indexler = np.arange(son_index + 1, son_index + gelecek_adim + 1).reshape(-1, 1)

        if transform:
            gelecek_X = transform.transform(gelecek_indexler)
            gelecek_y = model.predict(gelecek_X)
        else:
            gelecek_y = model.predict(gelecek_indexler)

        kalintilar = y - (y_pred_poly if transform else y_pred_lin)
        std_hata = np.std(kalintilar)

        # Güvenli listeye çevirme
        return {
            "Durum": "Basarili",
            "SecilenModel": secilen_model,
            "R2_Skoru": _safe_float(r2),
            "GelecekIndexler": gelecek_indexler.flatten().tolist(),
            "Tahminler": [_safe_float(x) for x in gelecek_y.tolist()],
            "GuvenAraligiAlt": [_safe_float(x) for x in (gelecek_y - 2 * std_hata).tolist()],
            "GuvenAraligiUst": [_safe_float(x) for x in (gelecek_y + 2 * std_hata).tolist()]
        }


# -----------------------------------------------------------------------------
# 5. GRAFİK AÇIKLAMA SİSTEMİ
# -----------------------------------------------------------------------------

class GrafikAciklayici:

    @staticmethod
    def trend_yorumu_getir(df: pd.DataFrame) -> str:
        ozet_df = (
            df.groupby(["DenemeIndex", "Deneme", "Tarih"])["Net"]
            .sum()
            .reset_index()
            .sort_values("DenemeIndex")
        )
        netler = ozet_df["Net"].tolist()
        if len(netler) < 2: return "Yetersiz veri."

        x = np.arange(len(netler))
        egim = np.polyfit(x, netler, 1)[0]
        baslangic, son = netler[0], netler[-1]

        yorum = f"Başlangıç: {baslangic:.2f} -> Son: {son:.2f} Net.\n"
        if egim > 2.0:
            yorum += f"🚀 HARİKA GELİŞİM: Her sınavda ortalama +{egim:.2f} net artışın var."
        elif egim > 0.5:
            yorum += f"📈 İSTİKRARLI YÜKSELİŞ: Yönün yukarı (Eğim: +{egim:.2f})."
        elif egim > -0.5:
            yorum += "➡️ YATAY SEYİR: Netlerin belirli bir aralıkta."
        else:
            yorum += f"🔻 DÜŞÜŞ EĞİLİMİ: Ortalama {abs(egim):.2f} net kayıp var."
        return yorum

    @staticmethod
    def tahmin_yorumu_getir(tahmin_verisi: Dict[str, Any]) -> str:
        if tahmin_verisi.get("Durum") != "Basarili":
            return f"Tahmin oluşturulamadı: {tahmin_verisi.get('Mesaj', 'Bilinmeyen hata')}"

        # _safe_float uygulanmış verilerle çalışır
        tahmin_degeri = tahmin_verisi["Tahminler"][0]
        alt_sinir = tahmin_verisi["GuvenAraligiAlt"][0]
        ust_sinir = tahmin_verisi["GuvenAraligiUst"][0]
        r2 = tahmin_verisi["R2_Skoru"]
        model = tahmin_verisi["SecilenModel"]

        if tahmin_degeri is None: return "Tahmin hesaplanamadı."

        yorum = f"🔮 GELECEK VİZYONU ({model}):\n"
        yorum += f"   • Beklenen Net: {tahmin_degeri:.2f}\n"
        if alt_sinir is not None and ust_sinir is not None:
            yorum += f"   • Güven Aralığı (%95): {alt_sinir:.2f} - {ust_sinir:.2f}\n"
        if r2 is not None:
            yorum += f"   • Model Güvenilirliği: %{r2 * 100:.1f}"
        return yorum

    @staticmethod
    def ders_trend_detay_yorumu_getir(df: pd.DataFrame) -> str:
        yorumlar = []
        for ders in df["Ders"].unique():
            ders_df = df[df["Ders"] == ders]
            if len(ders_df) < 2: continue

            ders_df = ders_df.sort_values("DenemeIndex")
            x = np.arange(len(ders_df))
            egim = np.polyfit(x, ders_df["Net"], 1)[0]

            if egim > 0.5:
                yorumlar.append(f"📈 {ders}: Yükselişte")
            elif egim < -0.5:
                yorumlar.append(f"🔻 {ders}: Düşüşte")

        if not yorumlar:
            return "Ders bazlı belirgin bir trend değişimi gözlenmedi, yatay seyir."
        return " | ".join(yorumlar)

    @staticmethod
    def radar_yorumu_getir(df: pd.DataFrame) -> str:
        if df is None or len(df) == 0: return "Veri yok."
        ders_basari = df.groupby("Ders")["BasariOrani"].mean().sort_values(ascending=False)
        en_iyi = ders_basari.index[0]
        en_kotu = ders_basari.index[-1]
        return f"🎯 YETKİNLİK ANALİZİ:\n   • En Güçlü Ders: {en_iyi} (%{ders_basari[en_iyi]:.1f} Başarı)\n   • Gelişim Alanı: {en_kotu} (%{ders_basari[en_kotu]:.1f} Başarı)"

    @staticmethod
    def risk_yonetimi_yorumu_getir(df: pd.DataFrame) -> str:
        if df is None or len(df) == 0: return "Veri yok."
        ozet = df.groupby("Ders")[["Yanlis", "Bos"]].mean()
        agresif = []
        temkinli = []
        for ders in ozet.index:
            y = ozet.loc[ders, "Yanlis"]
            b = ozet.loc[ders, "Bos"]
            if y > b * 1.5 and y > 2:
                agresif.append(ders)
            elif b > y * 1.5 and b > 2:
                temkinli.append(ders)

        yorum = "🎲 RİSK PROFİLİ:\n"
        if agresif: yorum += f"   • Yüksek Risk (Agresif): {', '.join(agresif)}\n"
        if temkinli: yorum += f"   • Düşük Risk (Temkinli): {', '.join(temkinli)}\n"
        if not agresif and not temkinli: yorum += "   • Dengeli bir risk yönetimi izleniyor."
        return yorum


# -----------------------------------------------------------------------------
# 6. ÖZET MOTORU (SUMMARY ENGINE)
# -----------------------------------------------------------------------------

class OzetMotoru:
    @staticmethod
    def genel_ozet_raporu_olustur(motor: AnalizMotoru) -> str:
        df = motor.df
        if (df is None or len(df) == 0) and not motor.satirlar:
            return "Özet oluşturulacak veri bulunamadı."

        if df is not None and len(df) > 0:
            ozet_df = df.groupby(["DenemeIndex", "Deneme", "Tarih"])["Net"].sum().reset_index().sort_values(
                "DenemeIndex")
            ilk_net = float(ozet_df["Net"].iloc[0])
            son_net = float(ozet_df["Net"].iloc[-1])
            en_yuksek_net = float(ozet_df["Net"].max())
            ders_ort = df.groupby("Ders")["Net"].mean().sort_values(ascending=False)
            en_iyi_ders = ders_ort.index[0]
            en_kotu_ders = ders_ort.index[-1]
            ders_std = df.groupby("Ders")["Net"].std().fillna(0).sort_values()
            en_istikrarli = ders_std.index[0]
            toplam_yanlis = int(df["Yanlis"].sum())
            toplam_bos = int(df["Bos"].sum())
        else:
            return "Yetersiz Veri"

        degisim = son_net - ilk_net
        degisim_yuzde = (degisim / ilk_net * 100) if ilk_net > 0 else 0
        risk_durumu = "Agresif (Bol Yanlış)" if toplam_yanlis > toplam_bos * 1.5 else \
            "Temkinli (Bol Boş)" if toplam_bos > toplam_yanlis * 1.5 else "Dengeli"

        rapor = []
        rapor.append("\n" + "#" * 70)
        rapor.append("🎓 AKADEMİK PERFORMANS KARNESİ VE FİNAL ÖZETİ 🎓")
        rapor.append("#" * 70)
        rapor.append(f"\n📊 1. GELİŞİM TABLOSU:")
        rapor.append(f"   • Başlangıç Neti: {ilk_net:.2f}")
        rapor.append(f"   • Son Deneme Neti: {son_net:.2f}")
        rapor.append(f"   • Zirve Netin: {en_yuksek_net:.2f}")
        rapor.append(f"   • Toplam Değişim: {degisim:+.2f} Net (%{degisim_yuzde:+.1f})")
        rapor.append(f"\n📚 2. DERS DETAYLARI:")
        rapor.append(f"   • 🏆 Amiral Gemisi (En İyi): {en_iyi_ders} ({ders_ort[en_iyi_ders]:.1f} Ort. Net)")
        rapor.append(f"   • ⚠️ Gelişim Alanı (En Düşük): {en_kotu_ders} ({ders_ort[en_kotu_ders]:.1f} Ort. Net)")
        rapor.append(f"   • ⚓ En İstikrarlı Ders: {en_istikrarli}")
        rapor.append(f"\n🧠 3. SINAV STRATEJİSİ:")
        rapor.append(f"   • Tarzın: {risk_durumu}")
        rapor.append(f"   • Genel Profil: {toplam_yanlis} Yanlış, {toplam_bos} Boş (Toplam Veri)")

        if df is not None and len(df) > 0 and LIBRARIES_AVAILABLE:
            tahmin = TahminMotoru.gelecek_tahmini_yap(df)
            if tahmin["Durum"] == "Basarili":
                rapor.append(f"\n🔮 4. GELECEK VİZYONU:")
                # Güvenli erişim
                alt = tahmin['GuvenAraligiAlt'][0] if tahmin['GuvenAraligiAlt'] else 0
                ust = tahmin['GuvenAraligiUst'][0] if tahmin['GuvenAraligiUst'] else 0
                if alt is not None and ust is not None:
                    rapor.append(f"   • Hedef Tahmini: **{alt:.1f}** ile **{ust:.1f}** aralığında.")

        rapor.append(f"\n💡 5. KİŞİSELLEŞTİRİLMİŞ ÇALIŞMA TAVSİYESİ:")
        if son_net < ilk_net:
            tavsiye = "   🚨 DURUM: Netlerde gerileme var. Temel konularda unutmalar başlamış olabilir.\n   REÇETE: Yeni konu çalışmayı durdur. Genel Tekrar Kampı yap."
        elif son_net < en_yuksek_net - 5:
            tavsiye = "   📉 DURUM: Zirveden uzaklaşmışsın (Dalgalanma).\n   REÇETE: Branş denemelerine ağırlık ver."
        elif degisim > 15:
            tavsiye = "   🚀 DURUM: Harika bir ivme yakaladın!\n   REÇETE: Aynı tempoda devam et."
        else:
            tavsiye = "   ➡️ DURUM: İstikrarlı ama yatay bir seyir.\n   REÇETE: Zayıf derse haftalık %30 daha fazla yer ayır."
        rapor.append(tavsiye)
        rapor.append("#" * 70 + "\n")
        return "\n".join(rapor)


# -----------------------------------------------------------------------------
# 7. GRAFİK MOTORU (GÖRSELLEŞTİRME VE SUNUM)
# -----------------------------------------------------------------------------

class GrafikRaporlayici:
    @staticmethod
    def rapor_olustur(motor: AnalizMotoru):
        if not LIBRARIES_AVAILABLE or motor.df is None: return

        df = motor.df
        tahmin_verisi = TahminMotoru.gelecek_tahmini_yap(df)

        sns.set_theme(style="whitegrid", palette="deep")
        plt.rcParams['font.family'] = 'sans-serif'

        print("\n" + "#" * 60)
        print("   BÖLÜM 1: GELECEK VE TREND ANALİZİ (YOL HARİTASI)")
        print("#" * 60)
        GrafikRaporlayici._baslik_yaz("1.1. TAHMİNLİ GENEL NET TRENDİ")
        print(GrafikAciklayici.trend_yorumu_getir(df))
        print(GrafikAciklayici.tahmin_yorumu_getir(tahmin_verisi))
        GrafikRaporlayici._ciz_tahminli_trend(df, tahmin_verisi)

        GrafikRaporlayici._baslik_yaz("1.2. DERS BAZLI DETAYLI TRENDLER")
        print(GrafikAciklayici.ders_trend_detay_yorumu_getir(df))
        GrafikRaporlayici._ciz_ders_trendleri_grid(df)

        print("\n" + "#" * 60)
        print("   BÖLÜM 2: AKADEMİK PERFORMANS VE YETKİNLİK")
        print("#" * 60)
        GrafikRaporlayici._baslik_yaz("2.1. AKADEMİK YETKİNLİK RADARI")
        print(GrafikAciklayici.radar_yorumu_getir(df))
        GrafikRaporlayici._ciz_radar(df)

        GrafikRaporlayici._baslik_yaz("2.2. DERS PERFORMANS ISI HARİTASI")
        GrafikRaporlayici._ciz_heatmap(df)

        print("\n" + "#" * 60)
        print("   BÖLÜM 3: RİSK VE STRATEJİ YÖNETİMİ")
        print("#" * 60)
        GrafikRaporlayici._baslik_yaz("3.1. RİSK MATRİSİ (YANLIŞ vs BOŞ)")
        print(GrafikAciklayici.risk_yonetimi_yorumu_getir(df))
        GrafikRaporlayici._ciz_risk_scatter(df)

    @staticmethod
    def _baslik_yaz(baslik):
        print("\n" + "-" * 40 + f"\n {baslik} \n" + "-" * 40)

    @staticmethod
    def _ciz_tahminli_trend(df, tahmin_verisi):
        plt.figure(figsize=(10, 6))
        ozet_df = (
            df.groupby(["DenemeIndex", "Deneme"])["Net"]
            .sum()
            .reset_index()
            .sort_values("DenemeIndex")
        )
        plt.plot(ozet_df["DenemeIndex"], ozet_df["Net"], 'o-', linewidth=2, label='Gerçekleşen', color='#2c3e50')
        if tahmin_verisi["Durum"] == "Basarili":
            gelecek_x = tahmin_verisi["GelecekIndexler"]
            gelecek_y = tahmin_verisi["Tahminler"]
            alt = tahmin_verisi["GuvenAraligiAlt"]
            ust = tahmin_verisi["GuvenAraligiUst"]

            # _safe_float sonucu None dönebilir, grafikte hata vermemesi için kontrol
            if gelecek_y and gelecek_y[0] is not None:
                plt.plot(gelecek_x, gelecek_y, 'o--', linewidth=2, color='#e67e22', label='Tahmin')
                if alt and ust and alt[0] is not None and ust[0] is not None:
                    plt.fill_between(gelecek_x, alt, ust, color='#e67e22', alpha=0.2, label='%95 Güven Aralığı')
                plt.plot([ozet_df["DenemeIndex"].iloc[-1], gelecek_x[0]],
                         [ozet_df["Net"].iloc[-1], gelecek_y[0]], '--', color='#e67e22', alpha=0.5)

        for x, y in zip(ozet_df["DenemeIndex"], ozet_df["Net"]):
            plt.text(x, y + 1, f"{y:.1f}", ha='center', fontweight='bold')
        plt.title("Net Gelişimi ve Gelecek Tahmini", fontsize=14, fontweight='bold')
        plt.xlabel("Deneme Sırası")
        plt.ylabel("Toplam Net")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def _ciz_radar(df):
        ders_basari = df.groupby("Ders")["BasariOrani"].mean().reset_index()
        kategoriler = ders_basari["Ders"].tolist()
        degerler = ders_basari["BasariOrani"].tolist()
        degerler += degerler[:1]
        angles = [n / float(len(kategoriler)) * 2 * pi for n in range(len(kategoriler))]
        angles += angles[:1]
        plt.figure(figsize=(8, 8))
        ax = plt.subplot(111, polar=True)
        plt.xticks(angles[:-1], kategoriler, color='black', size=12)
        ax.set_rlabel_position(0)
        plt.yticks([25, 50, 75, 100], ["25", "50", "75", "100"], color="grey", size=10)
        plt.ylim(0, 100)
        ax.plot(angles, degerler, linewidth=2, linestyle='solid', color='#3498db')
        ax.fill(angles, degerler, '#3498db', alpha=0.4)
        plt.title("Akademik Yetkinlik Radarı (% Başarı)", size=15, color='#2c3e50', y=1.1)
        plt.show()

    @staticmethod
    def _ciz_ders_trendleri_grid(df):
        df_plot = df.sort_values(["Ders", "DenemeIndex"])
        g = sns.FacetGrid(df_plot, col="Ders", col_wrap=2, height=4, aspect=1.5, sharey=False)
        g.map(sns.lineplot, "DenemeIndex", "Net", marker="o", linewidth=2.5)
        for ax, (ders_adi, ders_df) in zip(g.axes.flat, df_plot.groupby("Ders")):
            x_vals = ders_df["DenemeIndex"].to_numpy()
            if len(x_vals) > 1:
                z = np.polyfit(x_vals, ders_df["Net"], 1)
                p = np.poly1d(z)
                ax.plot(x_vals, p(x_vals), "r--", alpha=0.5, linewidth=1.5)
            ax.set_title(f"{ders_adi} Trendi", fontweight='bold')
            ax.grid(True, linestyle='--', alpha=0.5)
        plt.subplots_adjust(top=0.9)
        g.fig.suptitle('Ders Bazlı Net Gelişim Trendleri', fontsize=16, fontweight='bold')
        plt.show()

    @staticmethod
    def _ciz_risk_scatter(df):
        ozet = df.groupby("Ders")[["Yanlis", "Bos"]].mean().reset_index()
        plt.figure(figsize=(10, 8))
        sns.scatterplot(data=ozet, x="Bos", y="Yanlis", hue="Ders", s=200, style="Ders", palette="deep")
        limit = max(ozet["Bos"].max(), ozet["Yanlis"].max()) + 2
        plt.plot([0, limit], [0, limit], 'k--', alpha=0.3, label="Denge Çizgisi")
        plt.text(limit * 0.8, limit * 0.2, "TEMKİNLİ (Çok Boş)", fontsize=12, color='green', ha='center', alpha=0.5)
        plt.text(limit * 0.2, limit * 0.8, "RİSKLİ (Çok Yanlış)", fontsize=12, color='red', ha='center', alpha=0.5)
        for i in range(len(ozet)):
            plt.text(ozet.Bos[i] + 0.2, ozet.Yanlis[i], ozet.Ders[i], fontsize=10, fontweight='bold')
        plt.title("Risk Yönetimi Matrisi: Yanlış vs Boş", fontsize=14, fontweight='bold')
        plt.xlabel("Ortalama Boş Sayısı")
        plt.ylabel("Ortalama Yanlış Sayısı")
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def _ciz_heatmap(df):
        plt.figure(figsize=(10, 6))
        pivot_table = df.pivot(index="Ders", columns="DenemeIndex", values="Net").sort_index(axis=1)
        deneme_isimleri = df[["DenemeIndex", "Deneme"]].drop_duplicates("DenemeIndex").sort_values("DenemeIndex")
        pivot_table.columns = deneme_isimleri["Deneme"].tolist()
        sns.heatmap(pivot_table, annot=True, fmt=".1f", cmap="YlGnBu", linewidths=.5, cbar_kws={'label': 'Net'})
        plt.title("Ders Bazlı Performans Isı Haritası", fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.show()


# -----------------------------------------------------------------------------
# 8. SİMÜLASYON VERİLERİ VE ÇALIŞTIRMA
# -----------------------------------------------------------------------------

def ornek_veri_olustur() -> List[DenemeSinavi]:
    denemeler = []
    # Veri seti: [Türkçe(D,Y,B), Mat(D,Y,B), Sosyal(D,Y,B), Fen(D,Y,B)]
    veri_seti = [
        ("Deneme-1", "01.10", [(25, 10, 5), (15, 5, 20), (10, 5, 5), (5, 5, 10)]),  # ~42 Net
        ("Deneme-2", "15.10", [(28, 8, 4), (18, 4, 18), (12, 4, 4), (7, 4, 9)]),  # Artış
        ("Deneme-3", "01.11", [(30, 7, 3), (20, 5, 15), (14, 3, 3), (9, 3, 8)]),  # İlk Zirve
        ("Deneme-4", "15.11", [(26, 12, 2), (15, 8, 17), (13, 5, 2), (6, 8, 6)]),  # Çöküş
        ("Deneme-5", "01.12", [(25, 10, 5), (12, 6, 22), (12, 4, 4), (5, 5, 10)]),  # Dip
        ("Deneme-6", "15.12", [(32, 5, 3), (18, 4, 18), (15, 2, 3), (8, 4, 8)]),  # Toparlanma
        ("Deneme-7", "01.01", [(34, 4, 2), (22, 3, 15), (16, 2, 2), (10, 3, 7)]),  # İvmelenme
        ("Deneme-8", "15.01", [(36, 3, 1), (25, 4, 11), (18, 1, 1), (12, 3, 5)]),  # Yeni Zirve
    ]
    ders_adlari = ["Türkçe", "Matematik", "Sosyal", "Fen"]
    for ad, tarih, sonuclar in veri_seti:
        deneme = DenemeSinavi(ad, tarih)
        for i, (d, y, b) in enumerate(sonuclar):
            deneme.ders_ekle(DersSonuc(ders_adlari[i], d, y, b))
        denemeler.append(deneme)
    return denemeler


if __name__ == "__main__":
    print("=== PROFESYONEL AKADEMİK İZLEME SİSTEMİ (API HAZIR) ===")
    motor = AnalizMotoru(ornek_veri_olustur())
    GrafikRaporlayici.rapor_olustur(motor)
    print(OzetMotoru.genel_ozet_raporu_olustur(motor))
    print("\n✅ Analiz tamamlandı. API Modeli 'motor.get_api_response_model()' ile çağrılabilir.")