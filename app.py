from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from collections import defaultdict, OrderedDict
from difflib import get_close_matches
import os

app = Flask(__name__)

# 🔗 Setup Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)

# 🔍 Buka Google Sheets
SHEET_ID = "1cpzDf5mI1bm6U5JlfMvxolltI4Abrch2Ed4JQF4RoiA"
sheet = client.open_by_key(SHEET_ID).worksheet("Sheet2")

# 📅 Urutan bulan untuk penyortiran
URUTAN_BULAN = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12
}

# 🎯 Fungsi untuk mencari kata terdekat (Fuzzy Matching)
def find_closest_match(query, choices):
    matches = get_close_matches(query, choices, n=1, cutoff=0.6)
    return matches[0] if matches else query  # Jika tidak ada match, kembalikan input asli

@app.route('/')
def home():
    return jsonify({"message": "API Flask berjalan dengan baik!"})

# 🎤 Endpoint utama untuk pencarian STT berdasarkan kota asal & tujuan
@app.route('/search_all_months', methods=['GET'])
def search_all_months():
    kota_asal = request.args.get('Kota_Asal', '').strip()
    kota_tujuan = request.args.get('Kota_Tujuan', '').strip()

    if not kota_asal or not kota_tujuan:
        return jsonify({"error": "Kota_Asal dan Kota_Tujuan harus diisi"}), 400

    print(f"📌 Request masuk: Kota_Asal={kota_asal}, Kota_Tujuan={kota_tujuan}")

    # 🔄 Ambil data dari Google Sheets
    try:
        data = sheet.get_all_records()
        if not data:
            print("⚠️ Data di Google Sheet kosong!")
            return jsonify({"error": "Data tidak ditemukan di Google Sheet"}), 404
    except Exception as e:
        print(f"❌ Error mengambil data dari Google Sheets: {e}")
        return jsonify({"error": "Gagal mengambil data dari Google Sheets"}), 500

    # 🏙️ Ambil daftar kota untuk fuzzy matching
    daftar_kota_asal = {row["Kota Asal"].strip().lower() for row in data}
    daftar_kota_tujuan = {row["Kota Tujuan"].strip().lower() for row in data}

    # 🔍 Terapkan fuzzy matching pada input pengguna
    kota_asal = find_closest_match(kota_asal.lower(), daftar_kota_asal)
    kota_tujuan = find_closest_match(kota_tujuan.lower(), daftar_kota_tujuan)

    hasil_per_bulan = defaultdict(int)

    # 🔄 Looping untuk mencari data sesuai input pengguna
    for row in data:
        asal = row.get('Kota Asal', '').strip().lower()
        tujuan = row.get('Kota Tujuan', '').strip().lower()
        bulan = row.get('Bulan', '').strip().lower()
        jumlah_stt = row.get('Jumlah STT', 0)

        if asal == kota_asal and tujuan == kota_tujuan and bulan in URUTAN_BULAN:
            try:
                hasil_per_bulan[bulan] += int(jumlah_stt)
            except ValueError:
                print(f"⚠️ Data tidak valid untuk {row}")

    # 📊 Cek apakah ada hasil yang ditemukan
    if not hasil_per_bulan:
        print("❌ Tidak ada data yang cocok.")
        return jsonify({"error": "Tidak ada data untuk kota asal dan tujuan yang diminta"}), 404

    # 📅 Urutkan hasil berdasarkan urutan bulan
    hasil_terurut = OrderedDict(sorted(hasil_per_bulan.items(), key=lambda x: URUTAN_BULAN[x[0]]))

    # ✅ Response API JSON
    response_data = {
        "Kota_Asal": kota_asal.title(),
        "Kota_Tujuan": kota_tujuan.title(),
        "total_bulan_ditemukan": len(hasil_terurut),
        "total_stt_per_bulan": dict(hasil_terurut),
        "total_stt_semua_bulan": sum(hasil_terurut.values())
    }

    print(f"✅ Hasil pencarian: {response_data}")
    return jsonify(response_data)

# 🚀 Jalankan Flask (Gunakan Port dari Environment Variable agar bisa jalan di Render)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Render butuh port dari environment
    app.run(debug=True, host='0.0.0.0', port=port)
