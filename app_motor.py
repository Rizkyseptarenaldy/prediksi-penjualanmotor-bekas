import streamlit as st
import pandas as pd
import plotly.express as px
from statsmodels.tsa.arima.model import ARIMA
from datetime import timedelta
import os
import warnings
import random
warnings.filterwarnings("ignore")

# =====================================================
# 1️⃣ KONFIGURASI HALAMAN
# =====================================================
st.set_page_config(page_title="🏍️ Dashboard Penjualan Motor", layout="wide")

# =====================================================
# 2️⃣ UPLOAD / BACA DATA OTOMATIS
# =====================================================
st.sidebar.title("📂 Upload / Pilih Dataset")

uploaded_file = st.sidebar.file_uploader(
    "Unggah file data penjualan motor (CSV/XLSX):",
    type=["csv", "xlsx"]
)

# URL dataset default (online)
DATA_URL = "https://raw.githubusercontent.com/zaedulislam/motorcycle-sales-dataset/main/motor_sales_sample.csv"

@st.cache_data
def load_data(file):
    """Membaca data dari file CSV/XLSX"""
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
        st.info("📄 Membaca data dari file CSV yang diunggah.")
    elif file.name.endswith(".xlsx"):
        df = pd.read_excel(file)
        st.info("📘 Membaca data dari file Excel yang diunggah.")
    else:
        st.error("❌ Format file tidak didukung.")
        st.stop()
    return df

@st.cache_data
def load_default_data():
    """Memuat dataset default dari GitHub jika tidak ada file"""
    try:
        df = pd.read_csv(DATA_URL)
        st.sidebar.success("🌐 Menggunakan dataset default dari sistem.")
        return df
    except Exception as e:
        st.error(f"Gagal memuat dataset default dari internet: {e}")
        st.stop()

# Prioritas: upload → lokal → online
if uploaded_file:
    data = load_data(uploaded_file)
else:
    BASENAME = "motor_clean_fixed"
    CSV_PATH = f"{BASENAME}.csv"
    XLSX_PATH = f"{BASENAME}.xlsx"
    if os.path.exists(CSV_PATH):
        data = pd.read_csv(CSV_PATH)
        st.sidebar.success(f"📄 Membaca data dari file lokal: {CSV_PATH}")
    elif os.path.exists(XLSX_PATH):
        data = pd.read_excel(XLSX_PATH)
        st.sidebar.success(f"📘 Membaca data dari file lokal: {XLSX_PATH}")
    else:
        data = load_default_data()

# =====================================================
# 3️⃣ PERSIAPAN DATA
# =====================================================
if "Tanggal" not in data.columns:
    # Jika dataset tidak punya kolom tanggal, buat tanggal acak
    st.warning("Kolom 'Tanggal' tidak ditemukan, membuat kolom tanggal otomatis.")
    data["Tanggal"] = pd.date_range("2023-01-01", periods=len(data), freq="D")

data["Tanggal"] = pd.to_datetime(data["Tanggal"], errors="coerce")
data = data.dropna(subset=["Tanggal"]).sort_values("Tanggal")

# Tambahkan kolom wajib jika belum ada
wilayah_list = ["Jakarta", "Bandung", "Surabaya", "Medan", "Yogyakarta"]
if "Wilayah" not in data.columns:
    data["Wilayah"] = [random.choice(wilayah_list) for _ in range(len(data))]

if "Promosi" not in data.columns:
    data["Promosi"] = [random.choice([0, 1]) for _ in range(len(data))]

if "Penjualan" not in data.columns:
    data["Penjualan"] = [random.randint(20, 200) for _ in range(len(data))]

if "Nama_Produk" not in data.columns:
    data["Nama_Produk"] = [f"Motor-{i%5+1}" for i in range(len(data))]

# =====================================================
# 4️⃣ MENU NAVIGASI
# =====================================================
st.sidebar.title("🏍️ Menu Navigasi")
menu = st.sidebar.radio("Pilih Halaman:", [
    "Dashboard Penjualan",
    "Analisis Produk",
    "Prediksi Demand",
    "Rekomendasi Promosi",
    "Insight Otomatis"
])

# =====================================================
# 5️⃣ DASHBOARD PENJUALAN
# =====================================================
if menu == "Dashboard Penjualan":
    st.title("📊 Dashboard Penjualan Motor")
    st.markdown("Menampilkan tren penjualan dan distribusi berdasarkan wilayah.")

    fig_total = px.line(
        data, x="Tanggal", y="Penjualan", color="Nama_Produk",
        title="📈 Tren Penjualan Harian per Motor", markers=True
    )
    st.plotly_chart(fig_total, use_container_width=True)

    top_produk = data.groupby("Nama_Produk")["Penjualan"].sum().nlargest(5).reset_index()
    fig_top = px.bar(
        top_produk, x="Nama_Produk", y="Penjualan", color="Nama_Produk",
        text="Penjualan", title="🏆 Top 5 Motor Terlaris"
    )
    fig_top.update_traces(textposition="outside")
    st.plotly_chart(fig_top, use_container_width=True)

    wilayah_penjualan = data.groupby("Wilayah")["Penjualan"].sum().reset_index()
    fig_wilayah = px.pie(
        wilayah_penjualan, names="Wilayah", values="Penjualan",
        title="🌍 Distribusi Penjualan Berdasarkan Wilayah"
    )
    st.plotly_chart(fig_wilayah, use_container_width=True)

# =====================================================
# 6️⃣ ANALISIS PRODUK
# =====================================================
elif menu == "Analisis Produk":
    st.title("🔍 Analisis Penjualan per Motor")

    produk = st.selectbox("Pilih Motor:", data["Nama_Produk"].unique())
    df_produk = data[data["Nama_Produk"] == produk]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Penjualan", f"{df_produk['Penjualan'].sum()} unit")
    col2.metric("Rata-rata Harian", f"{df_produk['Penjualan'].mean():.2f} unit/hari")
    col3.metric("Wilayah Terbanyak", df_produk["Wilayah"].mode()[0])

    fig_tren = px.line(df_produk, x="Tanggal", y="Penjualan", markers=True,
                       title=f"📈 Tren Penjualan Harian: {produk}")
    st.plotly_chart(fig_tren, use_container_width=True)

    st.subheader("📋 Data Penjualan Motor")
    st.dataframe(df_produk, use_container_width=True)

# =====================================================
# 7️⃣ PREDIKSI DEMAND
# =====================================================
elif menu == "Prediksi Demand":
    st.title("📈 Prediksi Demand (7 Hari ke Depan)")
    st.markdown("Prediksi dilakukan menggunakan model **ARIMA** berdasarkan data historis.")

    produk = st.selectbox("Pilih Motor:", data["Nama_Produk"].unique())
    df_produk = data[data["Nama_Produk"] == produk]

    try:
        model = ARIMA(df_produk["Penjualan"], order=(1, 1, 1))
        fit = model.fit()
        forecast = fit.forecast(steps=7)

        forecast_df = pd.DataFrame({
            "Tanggal": pd.date_range(df_produk["Tanggal"].max() + timedelta(days=1), periods=7),
            "Prediksi_Penjualan": forecast
        })

        st.subheader(f"📅 Prediksi Penjualan 7 Hari ke Depan untuk {produk}")
        fig_forecast = px.line(forecast_df, x="Tanggal", y="Prediksi_Penjualan", markers=True,
                               title="🔮 Hasil Prediksi Demand")
        st.plotly_chart(fig_forecast, use_container_width=True)
        st.dataframe(forecast_df)

        # Tombol download CSV hasil prediksi
        csv = forecast_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="💾 Download Hasil Prediksi (CSV)",
            data=csv,
            file_name=f"prediksi_{produk}.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"Model gagal dijalankan: {e}")

# =====================================================
# 8️⃣ REKOMENDASI PROMOSI
# =====================================================
elif menu == "Rekomendasi Promosi":
    st.title("💡 Rekomendasi Promosi Motor")

    promo_avg = data[data["Promosi"] == 1]["Penjualan"].mean()
    non_promo_avg = data[data["Promosi"] == 0]["Penjualan"].mean()

    col1, col2 = st.columns(2)
    col1.metric("Rata-rata Saat Promosi", f"{promo_avg:.2f} unit")
    col2.metric("Rata-rata Tanpa Promosi", f"{non_promo_avg:.2f} unit")

    if promo_avg > non_promo_avg:
        st.success("✅ Promosi efektif! Pertahankan strategi promosi.")
    else:
        st.warning("⚠️ Promosi belum berdampak signifikan, perlu evaluasi.")

    promo_df = data.groupby(["Nama_Produk", "Promosi"])["Penjualan"].mean().reset_index()
    fig_promo = px.bar(promo_df, x="Nama_Produk", y="Penjualan", color="Promosi",
                       barmode="group", title="📊 Rata-rata Penjualan Saat Promosi vs Tidak Promosi")
    st.plotly_chart(fig_promo, use_container_width=True)

# =====================================================
# 9️⃣ INSIGHT OTOMATIS
# =====================================================
elif menu == "Insight Otomatis":
    st.title("🤖 Insight Otomatis Mingguan")
    cutoff = data["Tanggal"].max() - timedelta(days=7)
    recent_data = data[data["Tanggal"] >= cutoff]

    if len(recent_data) > 0:
        top_produk = recent_data.groupby("Nama_Produk")["Penjualan"].sum().nlargest(1).index[0]
        total_penjualan = recent_data["Penjualan"].sum()
        wilayah_terbaik = recent_data.groupby("Wilayah")["Penjualan"].sum().idxmax()

        st.success(f"🔥 Dalam 7 hari terakhir, motor **{top_produk}** paling laris!")
        st.info(f"Total penjualan minggu ini: **{total_penjualan} unit**, wilayah terbaik: **{wilayah_terbaik}**.")

        top5_recent = recent_data.groupby("Nama_Produk")["Penjualan"].sum().nlargest(5).reset_index()
        fig_bar = px.bar(top5_recent, x="Nama_Produk", y="Penjualan", color="Nama_Produk",
                         text="Penjualan", title="🏆 Top 5 Motor Terlaris Minggu Ini")
        fig_bar.update_traces(textposition="outside")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("❌ Tidak ada data penjualan 7 hari terakhir.")

# =====================================================
# 🔚 FOOTER
# =====================================================
st.markdown("---")
st.caption("🏍️ Dashboard Penjualan Motor | © 2025 Rizky Septa Renaldy - 411222068")
