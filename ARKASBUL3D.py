#apps untuk  telaah arus kas bulanan
import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import locale

# Konfigurasi API Groq - Mengambil dari secrets
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]  # API Key Groq dari secrets
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
# Menggunakan model yang tersedia di Groq
MODEL_NAME = "llama3-70b-8192"  # Model alternatif yang tersedia di Groq

# Fungsi untuk mendapatkan respons dari model Groq
def get_groq_response(prompt, max_tokens=512):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "top_p": 0.9
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"Error: {response.status_code}, {response.text}"
    except Exception as e:
        return f"Error connecting to Groq API: {str(e)}"

# Inisialisasi session state untuk menyimpan data
if 'has_analyzed' not in st.session_state:
    st.session_state.has_analyzed = False
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = ""
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'user_inputs_rp' not in st.session_state:
    st.session_state.user_inputs_rp = []
if 'gaji' not in st.session_state:
    st.session_state.gaji = 0
if 'insentif' not in st.session_state:
    st.session_state.insentif = 0
if 'persentase_dari_gaji' not in st.session_state:
    st.session_state.persentase_dari_gaji = []
if 'previous_question' not in st.session_state:
    st.session_state.previous_question = ""

# Callback untuk memproses pertanyaan chat
def process_chat_question():
    if st.session_state.chat_input and st.session_state.chat_input != st.session_state.previous_question:
        user_question = st.session_state.chat_input
        st.session_state.previous_question = user_question

        chat_prompt = f"""
        Berdasarkan data keuangan berikut:

        Gaji bulanan: Rp {format_number(st.session_state.gaji)}
        Insentif/lembur: Rp {format_number(st.session_state.insentif)}

        Alokasi dana pengguna:
        """

        for i, kategori_item in enumerate(kategori):
            if i < len(st.session_state.persentase_dari_gaji) and i < len(st.session_state.user_inputs_rp):
                chat_prompt += f"- {kategori_item}: {st.session_state.persentase_dari_gaji[i]:.2f}% (Rp {format_number(st.session_state.user_inputs_rp[i])})\n"

        chat_prompt += f"""
        Pertanyaan pengguna: {user_question}

        Berikan jawaban yang informatif dan bermanfaat dalam Bahasa Indonesia:
        """

        try:
            with st.spinner("Memproses pertanyaan Anda..."):
                response = get_groq_response(chat_prompt)
                if response.startswith("Error"):
                    st.error(response)
                    # Fallback ke respons sederhana
                    response = f"Untuk pertanyaan '{user_question}': Untuk mengelola keuangan dengan lebih baik, pertimbangkan untuk membuat anggaran bulanan yang detail dan melacak semua pengeluaran Anda. Prioritaskan pembayaran hutang dan tabungan darurat sebelum meningkatkan pengeluaran gaya hidup."
        except Exception as e:
            st.error(f"Error saat mengakses API: {str(e)}")
            # Fallback ke respons sederhana
            response = f"Untuk pertanyaan '{user_question}': Untuk mengelola keuangan dengan lebih baik, pertimbangkan untuk membuat anggaran bulanan yang detail dan melacak semua pengeluaran Anda. Prioritaskan pembayaran hutang dan tabungan darurat sebelum meningkatkan pengeluaran gaya hidup."

        # Tambahkan ke riwayat chat
        st.session_state.chat_history.append((user_question, response))

        # Reset input field
        st.session_state.chat_input = ""

# Definisi kategori pengeluaran (global untuk digunakan dalam callback)
kategori = [
    "Investasi atau tabungan untuk masa depan",
    "Cicilan, pinjaman, Asuransi, arisan, dll",
    "Pengeluaran Rumah Tangga",
    "Penguatan Dana \"Keranjang Aman\"",
    "Zakat dan biaya sosial",
    "Biaya pendidikan anak",
    "Hidup Gaya"
]

# Fungsi untuk memformat angka dengan titik sebagai pemisah ribuan
def format_number(number):
    return f"{number:,.0f}".replace(",", ".")

def main():
    st.set_page_config(
        page_title="Aplikasi Manajemen Keuangan",
        page_icon="💰",
        layout="wide"
    )

    st.title("💰 Aplikasi Manajemen Keuangan")

    # Sidebar untuk informasi
    with st.sidebar:
        st.header("Informasi")
        st.info("""
        Aplikasi ini membantu Anda mengelola keuangan dengan membagi pengeluaran
        berdasarkan kategori yang direkomendasikan.

        Masukkan gaji bulanan Anda dan aplikasi akan memberikan rekomendasi
        alokasi dana berdasarkan persentase yang disarankan.
        """)

    # CSS untuk memformat input angka dengan pemisah ribuan
    st.markdown("""
    <style>
    /* Menyembunyikan tombol + dan - */
    [data-testid="stNumberInput"] button {
        display: none;
    }

    /* Mengubah tampilan input number agar terlihat seperti teks dengan pemisah ribuan */
    input[type="number"] {
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

    # Input gaji dan insentif dengan format angka
    col1, col2 = st.columns(2)
    with col1:
        # Tampilkan label dan field input terpisah
        st.markdown("**Besar Gaji per Bulan (Rp)**")
        # Gunakan text_input untuk menampilkan angka terformat
        gaji_str = st.text_input(
            "Gaji",
            value=format_number(st.session_state.gaji) if st.session_state.gaji > 0 else "0",
            label_visibility="collapsed",
            key="gaji_input_str"
        )

        # Konversi input string ke angka (hapus titik pemisah ribuan)
        try:
            gaji = int(gaji_str.replace(".", ""))
            st.session_state.gaji = gaji
        except ValueError:
            st.error("Masukkan angka yang valid untuk gaji")
            gaji = st.session_state.gaji

    with col2:
        # Tampilkan label dan field input terpisah
        st.markdown("**Insentif/Lembur Rata-rata (Rp)**")
        # Gunakan text_input untuk menampilkan angka terformat
        insentif_str = st.text_input(
            "Insentif",
            value=format_number(st.session_state.insentif) if st.session_state.insentif > 0 else "0",
            label_visibility="collapsed",
            key="insentif_input_str"
        )

        # Konversi input string ke angka (hapus titik pemisah ribuan)
        try:
            insentif = int(insentif_str.replace(".", ""))
            st.session_state.insentif = insentif
        except ValueError:
            st.error("Masukkan angka yang valid untuk insentif")
            insentif = st.session_state.insentif

    # Definisi contoh untuk setiap kategori
    contoh = [
        "Dana yang rutin disisihkan setiap bulan untuk beli LM, nabung, saham, dll. Bila tidak menentu masukan rata-rata setahun berapa dan bagilah dengan 12",
        "Cicilan motor, KPR, premi asuransi, arisan, kartu kredit dlsb. yang biasa di keluarkan per bulan saat ini",
        "Listrik, air, iuran RT/lingkungan, operasional rumah tangga, ART, Makan, transport sekeluarga, dlsb. setiap bulannya",
        "Uang jaga-jaga, tabungan yang disediakan secara khusus untuk menghadapi situasi darurat atau yang tidak biasanya. Bedakan dengan tabungan yang umumnya memang untuk \"dihabiskan\" misal tabungan motor/mobil, haji, liburan dlsb",
        "Zakat/perpuluhan, sumbangan, dll",
        "Uang sekolah/kuliah/SKS, les/bimba, kursus dll",
        "Nongkrong di kafe, beli barang mewah, hobby dlsb"
    ]

    rentang = [
        "10-20%",
        "15-25%",
        "30-40%",
        "5-10%",
        "5-10%",
        "10-20%",
        "5-10%"
    ]

    # Buat rentang minimum dan maksimum
    rentang_min = [10, 15, 30, 5, 5, 10, 5]
    rentang_max = [20, 25, 40, 10, 10, 20, 10]

    # Buat container untuk tabel input
    st.subheader("Alokasi Dana per Kategori")

    # Buat kolom untuk header tabel dengan urutan yang diubah
    cols = st.columns([1, 3, 5, 3])
    cols[0].markdown("**No**")
    cols[1].markdown("**Item**")
    cols[2].markdown("**Contoh**")
    cols[3].markdown("**Besar Pengeluaran per Bulan (Rp)**")

    # Inisialisasi user_inputs_rp jika belum ada
    if len(st.session_state.user_inputs_rp) != len(kategori):
        st.session_state.user_inputs_rp = [0] * len(kategori)

    # Buat baris untuk setiap kategori
    user_inputs_rp = []
    for i, (kat, cont) in enumerate(zip(kategori, contoh)):
        cols = st.columns([1, 3, 5, 3])
        cols[0].write(f"{i+1}")
        cols[1].write(kat)
        cols[2].write(cont)

        # Tampilkan input pengeluaran dengan format angka
        default_value = st.session_state.user_inputs_rp[i] if i < len(st.session_state.user_inputs_rp) else 0
        pengeluaran_str = cols[3].text_input(
            f"Pengeluaran untuk {kat} (Rp)",
            value=format_number(default_value) if default_value > 0 else "0",
            key=f"input_rp_str_{i}",
            label_visibility="collapsed"
        )

        # Konversi input string ke angka (hapus titik pemisah ribuan)
        try:
            pengeluaran_rp = int(pengeluaran_str.replace(".", ""))
        except ValueError:
            st.error(f"Masukkan angka yang valid untuk {kat}")
            pengeluaran_rp = default_value

        user_inputs_rp.append(pengeluaran_rp)

    # Tombol analisa
    if st.button("Analisa", type="primary"):
        # Simpan input pengguna ke session state
        st.session_state.user_inputs_rp = user_inputs_rp

        # Hitung persentase insentif terhadap gaji
        if gaji > 0:
            persen_insentif = (insentif / gaji) * 100
        else:
            persen_insentif = 0

        st.write(f"Insentif/lembur sebesar Rp {format_number(insentif)} adalah {persen_insentif:.2f}% dari gaji bulanan.")

        # Hitung persentase dari gaji untuk setiap input
        persentase_dari_gaji = []
        for pengeluaran in user_inputs_rp:
            if gaji > 0:
                persentase = (pengeluaran / gaji) * 100
            else:
                persentase = 0
            persentase_dari_gaji.append(persentase)

        # Simpan persentase ke session state
        st.session_state.persentase_dari_gaji = persentase_dari_gaji

        # Tampilkan ringkasan alokasi
        st.subheader("Ringkasan Alokasi Dana")

        # Buat dataframe untuk ringkasan
        ringkasan_df = pd.DataFrame({
            "No": range(1, len(kategori) + 1),
            "Item": kategori,
            "Besar Pengeluaran (Rp)": [f"Rp {format_number(val)}" for val in user_inputs_rp],
            "Rujukan (%)": rentang,
            "Hasil Simulasi (%)": [f"{val:.2f}%" for val in persentase_dari_gaji]
        })

        st.dataframe(ringkasan_df, use_container_width=True, hide_index=True)

        # Hitung total pengeluaran dan persentase
        total_pengeluaran = sum(user_inputs_rp)
        total_persen = sum(persentase_dari_gaji)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Gaji", f"Rp {format_number(gaji)}")
        with col2:
            # Modifikasi 1: Ubah warna panah berdasarkan apakah pengeluaran melebihi gaji
            delta_pengeluaran = total_pengeluaran - gaji
            delta_color = "inverse" if delta_pengeluaran > 0 else "normal"
            st.metric(
                "Total Pengeluaran",
                f"Rp {format_number(total_pengeluaran)}",
                f"Rp {format_number(delta_pengeluaran)}",
                delta_color=delta_color
            )
        with col3:
            # Modifikasi 1: Ubah warna panah berdasarkan apakah persentase melebihi 100%
            delta_persen = total_persen - 100
            delta_color = "inverse" if delta_persen > 0 else "normal"
            st.metric(
                "Total Persentase",
                f"{total_persen:.2f}%",
                f"{delta_persen:.2f}%",
                delta_color=delta_color
            )

        # Peringatan jika total pengeluaran melebihi gaji
        if total_pengeluaran > gaji:
            st.warning(f"Total pengeluaran (Rp {format_number(total_pengeluaran)}) melebihi gaji bulanan (Rp {format_number(gaji)}). Pertimbangkan untuk mengurangi beberapa pengeluaran.")

        # Analisis dan saran
        st.subheader("Analisis Keuangan")

        # Identifikasi item yang melebihi rentang
        items_melebihi = []
        items_dibawah = []
        for i, (min_val, max_val, persen, kat) in enumerate(zip(rentang_min, rentang_max, persentase_dari_gaji, kategori)):
            if persen > max_val:
                items_melebihi.append((kat, persen, max_val))
            elif persen < min_val:
                items_dibawah.append((kat, persen, min_val))

        # Buat prompt untuk model LLM
        prompt = f"""
        Analisis keuangan berdasarkan data berikut:

        Gaji bulanan: Rp {format_number(gaji)}
        Insentif/lembur: Rp {format_number(insentif)} ({persen_insentif:.2f}% dari gaji)
        Total pendapatan: Rp {format_number(gaji + insentif)}

        Alokasi dana berdasarkan input pengguna:
        """

        for i, kategori_item in enumerate(kategori):
            prompt += f"- {kategori_item}: Rp {format_number(user_inputs_rp[i])} ({persentase_dari_gaji[i]:.2f}% dari gaji, rujukan: {rentang[i]})\n"

        if items_melebihi:
            prompt += "\nItem yang melebihi rentang rujukan:\n"
            for item, persen, max_val in items_melebihi:
                prompt += f"- {item}: {persen:.2f}% (melebihi batas atas {max_val}%)\n"

        if items_dibawah:
            prompt += "\nItem yang di bawah rentang rujukan:\n"
            for item, persen, min_val in items_dibawah:
                prompt += f"- {item}: {persen:.2f}% (di bawah batas bawah {min_val}%)\n"

        if total_pengeluaran > gaji:
            prompt += f"\nTotal pengeluaran (Rp {format_number(total_pengeluaran)}) melebihi gaji bulanan (Rp {format_number(gaji)}).\n"

        prompt += """
        Berikan analisis singkat tentang alokasi keuangan ini dan saran untuk perbaikan.
        Fokus pada item yang melebihi atau di bawah rentang rujukan jika ada.
        Berikan juga saran pemanfaatan insentif/lembur yang optimal.
        Berikan jawaban dalam Bahasa Indonesia.
        """

        # Gunakan API Groq untuk mendapatkan analisis
        with st.spinner("Menganalisis data keuangan..."):
            try:
                analisis = get_groq_response(prompt)
                if analisis.startswith("Error"):
                    st.error(analisis)
                    # Fallback ke analisis sederhana
                    analisis = generate_simple_analysis(gaji, insentif, persen_insentif, items_melebihi, items_dibawah, total_pengeluaran)
            except Exception as e:
                st.error(f"Error saat mengakses API: {str(e)}")
                # Fallback ke analisis sederhana
                analisis = generate_simple_analysis(gaji, insentif, persen_insentif, items_melebihi, items_dibawah, total_pengeluaran)

        # Simpan hasil analisis ke session state
        st.session_state.analysis_result = analisis
        st.session_state.has_analyzed = True

        # Tampilkan analisis
        st.write(analisis)

    # Jika sudah pernah dianalisis, tampilkan hasil sebelumnya
    elif st.session_state.has_analyzed:
        # Hitung persentase insentif terhadap gaji
        if gaji > 0:
            persen_insentif = (insentif / gaji) * 100
        else:
            persen_insentif = 0

        st.write(f"Insentif/lembur sebesar Rp {format_number(insentif)} adalah {persen_insentif:.2f}% dari gaji bulanan.")

        # Tampilkan ringkasan alokasi
        st.subheader("Ringkasan Alokasi Dana")

        # Buat dataframe untuk ringkasan
        ringkasan_df = pd.DataFrame({
            "No": range(1, len(kategori) + 1),
            "Item": kategori,
            "Besar Pengeluaran (Rp)": [f"Rp {format_number(val)}" for val in st.session_state.user_inputs_rp],
            "Rujukan (%)": rentang,
            "Hasil Simulasi (%)": [f"{val:.2f}%" for val in st.session_state.persentase_dari_gaji]
        })

        st.dataframe(ringkasan_df, use_container_width=True, hide_index=True)

        # Hitung total pengeluaran dan persentase
        total_pengeluaran = sum(st.session_state.user_inputs_rp)
        total_persen = sum(st.session_state.persentase_dari_gaji)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Gaji", f"Rp {format_number(gaji)}")
        with col2:
            # Modifikasi 1: Ubah warna panah berdasarkan apakah pengeluaran melebihi gaji
            delta_pengeluaran = total_pengeluaran - gaji
            delta_color = "inverse" if delta_pengeluaran > 0 else "normal"
            st.metric(
                "Total Pengeluaran",
                f"Rp {format_number(total_pengeluaran)}",
                f"Rp {format_number(delta_pengeluaran)}",
                delta_color=delta_color
            )
        with col3:
            # Modifikasi 1: Ubah warna panah berdasarkan apakah persentase melebihi 100%
            delta_persen = total_persen - 100
            delta_color = "inverse" if delta_persen > 0 else "normal"
            st.metric(
                "Total Persentase",
                f"{total_persen:.2f}%",
                f"{delta_persen:.2f}%",
                delta_color=delta_color
            )

        # Peringatan jika total pengeluaran melebihi gaji
        if total_pengeluaran > gaji:
            st.warning(f"Total pengeluaran (Rp {format_number(total_pengeluaran)}) melebihi gaji bulanan (Rp {format_number(gaji)}). Pertimbangkan untuk mengurangi beberapa pengeluaran.")

        # Analisis dan saran
        st.subheader("Analisis Keuangan")
        st.write(st.session_state.analysis_result)

    # Tampilkan kolom chat jika sudah dianalisis
    if st.session_state.has_analyzed:
        st.subheader("Konsultasi Keuangan")

        # Modifikasi 2: Tampilkan riwayat chat secara langsung tanpa expander
        for i, (q, a) in enumerate(st.session_state.chat_history):
            st.markdown(f"**Pertanyaan {i+1}:**")
            st.markdown(f"{q}")
            st.markdown(f"**Jawaban:**")
            st.markdown(f"{a}")
            st.markdown("---")  # Garis pemisah antar pertanyaan

        # Input pertanyaan baru dengan callback
        st.text_input(
            "Tanyakan tentang keuangan Anda (tekan Enter untuk mengirim):",
            key="chat_input",
            on_change=process_chat_question
        )

        # Tambahkan disclaimer di bawah kolom chat
        st.info("""
        **Disclaimer:**
        - Sistem ini menggunakan AI-LLM dan dapat menghasilkan jawaban yang tidak selalu akurat.
        - Mohon verifikasi informasi penting dengan sumber terpercaya, seperti perencana keuangan, dan profesional lainnya.
        """)

def generate_simple_analysis(gaji, insentif, persen_insentif, items_melebihi, items_dibawah, total_pengeluaran):
    """Fungsi untuk menghasilkan analisis sederhana jika API tidak tersedia"""
    analisis = f"""
    Berdasarkan gaji bulanan Anda sebesar Rp {format_number(gaji)} dan insentif/lembur sebesar Rp {format_number(insentif)}, berikut adalah analisis keuangan Anda:

    1. Total pendapatan: Rp {format_number(gaji + insentif)}
    2. Total pengeluaran: Rp {format_number(total_pengeluaran)}
    """

    if total_pengeluaran > gaji:
        analisis += f"\nTotal pengeluaran Anda melebihi gaji bulanan sebesar Rp {format_number(total_pengeluaran - gaji)}. Sebaiknya kurangi beberapa pengeluaran atau gunakan insentif/lembur untuk menutupi kekurangan.\n"
    else:
        analisis += f"\nAnda memiliki sisa gaji sebesar Rp {format_number(gaji - total_pengeluaran)} yang dapat dialokasikan untuk tabungan tambahan atau kebutuhan lain.\n"

    if items_melebihi:
        analisis += "\nItem yang melebihi rentang rujukan:\n"
        for item, persen, max_val in items_melebihi:
            analisis += f"- {item}: {persen:.2f}% (melebihi batas atas {max_val}%)\n"
        analisis += "\nSebaiknya Anda mengurangi alokasi untuk item-item tersebut dan menyesuaikannya dengan rentang yang direkomendasikan.\n"

    if items_dibawah:
        analisis += "\nItem yang di bawah rentang rujukan:\n"
        for item, persen, min_val in items_dibawah:
            analisis += f"- {item}: {persen:.2f}% (di bawah batas bawah {min_val}%)\n"
        analisis += "\nSebaiknya Anda meningkatkan alokasi untuk item-item tersebut agar sesuai dengan rentang yang direkomendasikan.\n"

    analisis += f"""
    Rekomendasi:
    - Jika Anda memiliki cicilan yang besar, pertimbangkan untuk mengurangi pengeluaran gaya hidup
    - Pastikan dana "Keranjang Aman" mencukupi untuk 3-6 bulan pengeluaran
    - Investasi jangka panjang sangat penting untuk masa depan finansial Anda

    Dengan insentif/lembur sebesar {persen_insentif:.2f}% dari gaji, Anda dapat mengalokasikan tambahan ini untuk mempercepat pembayaran hutang atau meningkatkan investasi.
    """

    return analisis

if __name__ == "__main__":
    main()
