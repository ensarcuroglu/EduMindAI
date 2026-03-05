import datetime
from typing import List, Dict, Tuple, Any

# Veri Analizi ve Görselleştirme Kütüphaneleri
try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import PolynomialFeatures
    from sklearn.metrics import r2_score
    from math import pi

    LIBRARIES_AVAILABLE = True
except ImportError:
    LIBRARIES_AVAILABLE = False
    print("UYARI: Gerekli kütüphaneler (pandas, matplotlib, seaborn, numpy, sklearn) eksik.")


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
# 2. ANALİZ MOTORU (VERİ İŞLEME)
# -----------------------------------------------------------------------------

class AnalizMotoru:
    def __init__(self, denemeler: List[DenemeSinavi]):
        self.denemeler = denemeler
        self.df = self._dataframe_olustur()

    def _dataframe_olustur(self):
        if not LIBRARIES_AVAILABLE or not self.denemeler:
            return None

        data = []
        for i, deneme in enumerate(self.denemeler):
            for ders_adi, sonuc in deneme.dersler.items():
                data.append({
                    "DenemeIndex": i + 1,  # Sayısal analiz için
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

        return pd.DataFrame(data)


# -----------------------------------------------------------------------------
# 3. TAHMİN MOTORU (REGRESSION ENGINE)
# -----------------------------------------------------------------------------

class TahminMotoru:
    """Gelecek sınavlar için net tahmini yapar (Regresyon Modelleri)."""

    @staticmethod
    def gelecek_tahmini_yap(df: pd.DataFrame, gelecek_adim: int = 3) -> Dict[str, Any]:
        ozet_df = df.groupby("DenemeIndex")["Net"].sum().reset_index()
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

        guven_araligi_ust = gelecek_y + (2 * std_hata)
        guven_araligi_alt = gelecek_y - (2 * std_hata)

        return {
            "Durum": "Basarili",
            "SecilenModel": secilen_model,
            "R2_Skoru": r2,
            "GelecekIndexler": gelecek_indexler.flatten(),
            "Tahminler": gelecek_y,
            "GuvenAraligiAlt": guven_araligi_alt,
            "GuvenAraligiUst": guven_araligi_ust
        }


# -----------------------------------------------------------------------------
# 4. GRAFİK AÇIKLAMA SİSTEMİ
# -----------------------------------------------------------------------------

class GrafikAciklayici:

    @staticmethod
    def trend_yorumu_getir(df: pd.DataFrame) -> str:
        ozet_df = df.groupby(["Deneme"])["Net"].sum().reset_index()
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
    def tahmin_yorumu_getir(tahmin_verisi: Dict) -> str:
        if tahmin_verisi["Durum"] != "Basarili":
            return tahmin_verisi["Mesaj"]

        sonraki_sinav = tahmin_verisi["Tahminler"][0]
        alt = tahmin_verisi["GuvenAraligiAlt"][0]
        ust = tahmin_verisi["GuvenAraligiUst"][0]
        r2 = tahmin_verisi["R2_Skoru"]

        yorum = f"🔮 ÖNGÖRÜ: Gelecek sınavda %95 ihtimalle **{alt:.1f} - {ust:.1f}** net aralığında olacaksın.\n"
        yorum += f"Modelin güvenilirliği: %{r2 * 100:.1f}."
        return yorum

    @staticmethod
    def radar_yorumu_getir(df: pd.DataFrame) -> str:
        # Son 3 sınavın ortalamasına göre yetkinlik analizi
        son_df = df.copy()  # Tüm veriyi kullanmak daha genel profil verir
        ders_basari = son_df.groupby("Ders")["BasariOrani"].mean()

        en_iyi = ders_basari.idxmax()
        en_kotu = ders_basari.idxmin()
        std_sapma = ders_basari.std()

        yorum = f"🎯 AKADEMİK DENGE: En güçlü kasın **{en_iyi}** (%{ders_basari[en_iyi]:.1f}), geliştirmen gereken ise **{en_kotu}** (%{ders_basari[en_kotu]:.1f}).\n"

        if std_sapma < 15:
            yorum += "⚖️ DENGELİ PROFİL: Dersler arasındaki başarı seviyen birbirine yakın. Dengeli bir çalışma programın var."
        else:
            yorum += "⚠️ DENGESİZ DAĞILIM: Bazı derslerde çok iyiyken bazılarında kopukluk var. Zayıf derslere ağırlık vererek toplam netini hızla artırabilirsin."
        return yorum

    @staticmethod
    def risk_yonetimi_yorumu_getir(df: pd.DataFrame) -> str:
        # Ders bazında ortalama yanlış ve boş sayıları
        ozet = df.groupby("Ders")[["Yanlis", "Bos"]].mean()

        agresif_dersler = ozet[ozet["Yanlis"] > ozet["Bos"] * 1.5].index.tolist()
        temkinli_dersler = ozet[ozet["Bos"] > ozet["Yanlis"] * 1.5].index.tolist()

        yorum = "🎲 RİSK VE STRATEJİ ANALİZİ:\n"
        if agresif_dersler:
            yorum += f"🔥 YÜKSEK RİSK (AGRESİF): **{', '.join(agresif_dersler)}**. Bu derslerde yanlış sayın boşlarından belirgin şekilde fazla. Emin olmadığın soruları işaretleme eğilimindesin.\n"

        if temkinli_dersler:
            yorum += f"🛡️ FAZLA TEMKİNLİ: **{', '.join(temkinli_dersler)}**. Bu derslerde boş bırakma oranın yüksek. Bilgi eksikliği veya süre yetmemesi olabilir, ancak sallama yapmıyorsun.\n"

        if not agresif_dersler and not temkinli_dersler:
            yorum += "✅ DENGELİ STRATEJİ: Yanlış ve boş sayıların makul bir dengede. Risk yönetimini iyi yapıyorsun."

        return yorum

    @staticmethod
    def ders_trend_detay_yorumu_getir(df: pd.DataFrame) -> str:
        # Her ders için eğim hesapla
        yorumlar = []
        for ders in df["Ders"].unique():
            ders_df = df[df["Ders"] == ders]
            if len(ders_df) < 2: continue

            x = np.arange(len(ders_df))
            egim = np.polyfit(x, ders_df["Net"], 1)[0]

            if egim > 0.5:
                yorumlar.append(f"📈 {ders}: Yükselişte")
            elif egim < -0.5:
                yorumlar.append(f"🔻 {ders}: Düşüşte")

        if not yorumlar:
            return "Ders bazlı belirgin bir trend değişimi gözlenmedi, yatay seyir."
        return " | ".join(yorumlar)


# -----------------------------------------------------------------------------
# 5. ÖZET MOTORU (SUMMARY ENGINE) - YENİ
# -----------------------------------------------------------------------------

class OzetMotoru:
    """Tüm analizleri derleyip konsola final özet raporu basar."""

    @staticmethod
    def genel_ozet_raporu_olustur(motor: AnalizMotoru) -> str:
        df = motor.df
        if df is None or len(df) == 0:
            return "Özet oluşturulacak veri bulunamadı."

        # --- Veri Hazırlığı ---
        # 1. Genel Gelişim
        ozet_df = df.groupby("Deneme")["Net"].sum()
        ilk_net = ozet_df.iloc[0]
        son_net = ozet_df.iloc[-1]
        en_yuksek_net = ozet_df.max()
        degisim = son_net - ilk_net
        degisim_yuzde = (degisim / ilk_net * 100) if ilk_net > 0 else 0

        # 2. Ders Performansları
        ders_ort = df.groupby("Ders")["Net"].mean().sort_values(ascending=False)
        en_iyi_ders = ders_ort.index[0]
        en_kotu_ders = ders_ort.index[-1]

        # 3. İstikrar (Standart Sapma)
        ders_std = df.groupby("Ders")["Net"].std().sort_values()
        en_istikrarli = ders_std.index[0]

        # 4. Risk Analizi
        toplam_yanlis = df["Yanlis"].sum()
        toplam_bos = df["Bos"].sum()
        risk_durumu = "Agresif (Bol Yanlış)" if toplam_yanlis > toplam_bos * 1.5 else \
            "Temkinli (Bol Boş)" if toplam_bos > toplam_yanlis * 1.5 else "Dengeli"

        # --- Rapor Metni Oluşturma ---
        rapor = []
        rapor.append("\n" + "#" * 70)
        rapor.append("🎓 AKADEMİK PERFORMANS KARNESİ VE FİNAL ÖZETİ 🎓")
        rapor.append("#" * 70)

        # Bölüm 1: Genel Karnesi
        rapor.append(f"\n📊 1. GELİŞİM TABLOSU:")
        rapor.append(f"   • Başlangıç Neti: {ilk_net:.2f}")
        rapor.append(f"   • Son Deneme Neti: {son_net:.2f}")
        rapor.append(f"   • Zirve Netin: {en_yuksek_net:.2f}")
        rapor.append(f"   • Toplam Değişim: {degisim:+.2f} Net (%{degisim_yuzde:+.1f})")

        # Bölüm 2: Ders Analizi
        rapor.append(f"\n📚 2. DERS DETAYLARI:")
        rapor.append(f"   • 🏆 Amiral Gemisi (En İyi): {en_iyi_ders} ({ders_ort[en_iyi_ders]:.1f} Ort. Net)")
        rapor.append(f"   • ⚠️ Gelişim Alanı (En Düşük): {en_kotu_ders} ({ders_ort[en_kotu_ders]:.1f} Ort. Net)")
        rapor.append(f"   • ⚓ En İstikrarlı Ders: {en_istikrarli}")

        # Bölüm 3: Sınav Karakteri
        rapor.append(f"\n🧠 3. SINAV STRATEJİSİ:")
        rapor.append(f"   • Tarzın: {risk_durumu}")
        rapor.append(f"   • Genel Profil: {toplam_yanlis} Yanlış, {toplam_bos} Boş (Toplam Veri)")

        # Bölüm 4: Gelecek Vizyonu
        tahmin = TahminMotoru.gelecek_tahmini_yap(df)
        if tahmin["Durum"] == "Basarili":
            rapor.append(f"\n🔮 4. GELECEK VİZYONU:")
            rapor.append(f"   • Hedef Tahmini: Önümüzdeki sınavda netlerinin istatistiksel olarak")
            rapor.append(
                f"     **{tahmin['GuvenAraligiAlt'][0]:.1f}** ile **{tahmin['GuvenAraligiUst'][0]:.1f}** aralığında gelmesi bekleniyor.")

        # Bölüm 5: Reçete (Tavsiye)
        rapor.append(f"\n💡 5. KİŞİSELLEŞTİRİLMİŞ ÇALIŞMA TAVSİYESİ:")
        tavsiye = ""

        # Senaryo Analizi
        if son_net < ilk_net:
            tavsiye = "   🚨 DURUM: Netlerde gerileme var. Temel konularda unutmalar başlamış olabilir.\n   REÇETE: Yeni konu çalışmayı durdur. Son 3 denemedeki yanlışlarını analiz et ve 'Genel Tekrar Kampı' yap."
        elif son_net < en_yuksek_net - 5:
            tavsiye = "   📉 DURUM: Zirveden uzaklaşmışsın (Dalgalanma). Odak veya kondisyon sorunu olabilir.\n   REÇETE: Branş denemelerine ağırlık vererek süre yönetimini ve sınav kondisyonunu geri kazan."
        elif degisim > 15:
            tavsiye = "   🚀 DURUM: Harika bir ivme yakaladın! Çalışma sistemin işliyor.\n   REÇETE: Aynı tempoda devam et. Artık daha zor kaynaklara veya süre kısaltma antrenmanlarına geçebilirsin."
        else:
            tavsiye = "   ➡️ DURUM: İstikrarlı ama yatay bir seyir. Sıçrama yapmak için bir şeyler değişmeli.\n   REÇETE: 'Gelişim Alanı' olarak belirlenen derse haftalık çalışma planında %30 daha fazla yer ayır."

        rapor.append(tavsiye)
        rapor.append("#" * 70 + "\n")

        return "\n".join(rapor)


# -----------------------------------------------------------------------------
# 6. GRAFİK MOTORU (GÖRSELLEŞTİRME VE SUNUM)
# -----------------------------------------------------------------------------

class GrafikRaporlayici:
    @staticmethod
    def rapor_olustur(motor: AnalizMotoru):
        if not LIBRARIES_AVAILABLE or motor.df is None: return

        df = motor.df
        tahmin_verisi = TahminMotoru.gelecek_tahmini_yap(df)

        sns.set_theme(style="whitegrid", palette="deep")
        plt.rcParams['font.family'] = 'sans-serif'

        # ==========================================
        # GRUP 1: GELECEK & TREND ANALİZİ
        # ==========================================
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

        # ==========================================
        # GRUP 2: AKADEMİK PERFORMANS VE YETKİNLİK
        # ==========================================
        print("\n" + "#" * 60)
        print("   BÖLÜM 2: AKADEMİK PERFORMANS VE YETKİNLİK")
        print("#" * 60)

        GrafikRaporlayici._baslik_yaz("2.1. AKADEMİK YETKİNLİK RADARI")
        print(GrafikAciklayici.radar_yorumu_getir(df))
        GrafikRaporlayici._ciz_radar(df)

        GrafikRaporlayici._baslik_yaz("2.2. DERS PERFORMANS ISI HARİTASI")
        print(
            "Isı haritası, hangi sınavda hangi derste performans düşüklüğü veya zirve yaşandığını renklerle gösterir.")
        GrafikRaporlayici._ciz_heatmap(df)

        # ==========================================
        # GRUP 3: RİSK VE STRATEJİ YÖNETİMİ
        # ==========================================
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
        ozet_df = df.groupby(["DenemeIndex", "Deneme"])["Net"].sum().reset_index()

        plt.plot(ozet_df["DenemeIndex"], ozet_df["Net"], 'o-', linewidth=2, label='Gerçekleşen', color='#2c3e50')

        if tahmin_verisi["Durum"] == "Basarili":
            gelecek_x = tahmin_verisi["GelecekIndexler"]
            gelecek_y = tahmin_verisi["Tahminler"]
            alt = tahmin_verisi["GuvenAraligiAlt"]
            ust = tahmin_verisi["GuvenAraligiUst"]

            plt.plot(gelecek_x, gelecek_y, 'o--', linewidth=2, color='#e67e22', label='Tahmin')
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
        # Veriyi Hazırla
        ders_basari = df.groupby("Ders")["BasariOrani"].mean().reset_index()
        kategoriler = ders_basari["Ders"].tolist()
        degerler = ders_basari["BasariOrani"].tolist()

        # Radar grafiği için veriyi dairesel kapatma
        degerler += degerler[:1]
        angles = [n / float(len(kategoriler)) * 2 * pi for n in range(len(kategoriler))]
        angles += angles[:1]

        plt.figure(figsize=(8, 8))
        ax = plt.subplot(111, polar=True)

        # Eksenleri çiz
        plt.xticks(angles[:-1], kategoriler, color='black', size=12)
        ax.set_rlabel_position(0)
        plt.yticks([25, 50, 75, 100], ["25", "50", "75", "100"], color="grey", size=10)
        plt.ylim(0, 100)

        # Veriyi çiz
        ax.plot(angles, degerler, linewidth=2, linestyle='solid', color='#3498db')
        ax.fill(angles, degerler, '#3498db', alpha=0.4)

        plt.title("Akademik Yetkinlik Radarı (% Başarı)", size=15, color='#2c3e50', y=1.1)
        plt.show()

    @staticmethod
    def _ciz_ders_trendleri_grid(df):
        # Her ders için ayrı bir çizgi grafik
        g = sns.FacetGrid(df, col="Ders", col_wrap=2, height=4, aspect=1.5, sharey=False)
        g.map(sns.lineplot, "Deneme", "Net", marker="o", linewidth=2.5)

        # Her grafiğe trend çizgisi ekle
        for ax, (ders_adi, ders_df) in zip(g.axes.flat, df.groupby("Ders")):
            x_vals = np.arange(len(ders_df))
            if len(x_vals) > 1:
                z = np.polyfit(x_vals, ders_df["Net"], 1)
                p = np.poly1d(z)
                ax.plot(x_vals, p(x_vals), "r--", alpha=0.5, linewidth=1.5)

            # Başlıkları düzenle
            ax.set_title(f"{ders_adi} Trendi", fontweight='bold')
            ax.grid(True, linestyle='--', alpha=0.5)

        plt.subplots_adjust(top=0.9)
        g.fig.suptitle('Ders Bazlı Net Gelişim Trendleri', fontsize=16, fontweight='bold')
        plt.show()

    @staticmethod
    def _ciz_risk_scatter(df):
        # Ortalama Yanlış ve Boş sayıları
        ozet = df.groupby("Ders")[["Yanlis", "Bos"]].mean().reset_index()

        plt.figure(figsize=(10, 8))
        sns.scatterplot(data=ozet, x="Bos", y="Yanlis", hue="Ders", s=200, style="Ders", palette="deep")

        # Bölge çizgisi (y=x)
        limit = max(ozet["Bos"].max(), ozet["Yanlis"].max()) + 2
        plt.plot([0, limit], [0, limit], 'k--', alpha=0.3, label="Denge Çizgisi")

        # Bölgeleri etiketle
        plt.text(limit * 0.8, limit * 0.2, "TEMKİNLİ BÖLGE\n(Çok Boş)", fontsize=12, color='green', ha='center',
                 alpha=0.5)
        plt.text(limit * 0.2, limit * 0.8, "RİSKLİ BÖLGE\n(Çok Yanlış)", fontsize=12, color='red', ha='center',
                 alpha=0.5)

        # Etiketler
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
        pivot_table = df.pivot(index="Ders", columns="Deneme", values="Net")
        sns.heatmap(pivot_table, annot=True, fmt=".1f", cmap="YlGnBu", linewidths=.5, cbar_kws={'label': 'Net'})
        plt.title("Ders Bazlı Performans Isı Haritası", fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.show()


# -----------------------------------------------------------------------------
# 7. SİMÜLASYON VERİLERİ
# -----------------------------------------------------------------------------

def ornek_veri_olustur() -> List[DenemeSinavi]:
    denemeler = []
    # Veri seti: [Türkçe(D,Y,B), Mat(D,Y,B), Sosyal(D,Y,B), Fen(D,Y,B)]
    # Senaryo: Başlangıç iyi, ortada (D4-D5) çöküş, sonda (D6-D8) toparlanma ve zirve
    veri_seti = [
        ("Deneme-1", "01.10", [(25, 10, 5), (15, 5, 20), (10, 5, 5), (5, 5, 10)]),  # ~42 Net
        ("Deneme-2", "15.10", [(28, 8, 4), (18, 4, 18), (12, 4, 4), (7, 4, 9)]),  # Artış
        ("Deneme-3", "01.11", [(30, 7, 3), (20, 5, 15), (14, 3, 3), (9, 3, 8)]),  # İlk Zirve
        ("Deneme-4", "15.11", [(26, 12, 2), (15, 8, 17), (13, 5, 2), (6, 8, 6)]),  # Çöküş Başlangıcı (Zor sınav)
        ("Deneme-5", "01.12", [(25, 10, 5), (12, 6, 22), (12, 4, 4), (5, 5, 10)]),  # Dip Noktası
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
    print("=== PROFESYONEL AKADEMİK İZLEME SİSTEMİ ===")
    motor = AnalizMotoru(ornek_veri_olustur())

    # 1. Grafikler ve Detaylı Analizler
    GrafikRaporlayici.rapor_olustur(motor)

    # 2. Final Özet Raporu (En Sonda)
    print(OzetMotoru.genel_ozet_raporu_olustur(motor))

    print("✅ Analiz tamamlandı.")