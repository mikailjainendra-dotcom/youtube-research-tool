import datetime
from googleapiclient.discovery import build
import pandas as pd
import streamlit as st

# --- KONFIGURASI HALAMAN STREAMLIT ---
st.set_page_config(
    page_title="YouTube Research Hub (Music & General)",
    page_icon="🎵",
    layout="wide",
)

st.title("🚀 YouTube Creator Research Hub")
st.caption(
    "Platform riset terpusat untuk menganalisis Cover/Original Music dan"
    " memindai Hidden Gem lintas topik secara otomatis."
)

# --- SIDEBAR GLOBAL (INPUT API KEY MANUAL) ---
with st.sidebar:
  st.header("⚙️ Konfigurasi Sistem")
  api_key = st.text_input(
      "Masukkan YouTube API Key Anda:", type="password"
  )
  st.markdown("---")
  st.info(
      "💡 Masukkan API Key Anda di atas sebelum menjalankan riset di tab mana"
      " pun."
  )


# ==========================================
# PEMBUATAN TAB TERPISAH
# ==========================================
tab_musik, tab_global = st.tabs(
    [
        "🎵 Tab 1: Riset Musik (Original & Cover)",
        "🌍 Tab 2: Auto-Scan Hidden Gem (Semua Topik)",
    ]
)


# ==========================================
# TAB 1: KHUSUS RISET MUSIK (COVER VS ORIGINAL)
# ==========================================
with tab_musik:
  st.header("🎵 Fokus Utama: Riset Lagu Original & Cover")
  st.markdown(
      "Gunakan tab ini untuk mencari kata kunci lagu tertentu, lalu memilah"
      " secara otomatis mana yang bergenre **Cover** dan mana yang"
      " **Original**, diurutkan berdasarkan kecepatan viral (*Views/Hari*)."
  )

  col_m1, col_m2 = st.columns([3, 1])
  with col_m1:
    query_musik = st.text_input(
        "Masukkan kata kunci lagu / musik:",
        placeholder="Contoh: cover lagu galau, akustik indonesia, fingerstyle pop",
        key="input_q_musik",
    )
  with col_m2:
    max_res_musik = st.slider(
        "Jumlah Hasil:", 10, 50, 20, key="slider_res_musik"
    )

  if st.button("🔍 Mulai Riset Musik", type="primary", key="btn_musik"):
    if not api_key:
      st.warning("Harap masukkan YouTube API Key terlebih dahulu di sidebar!")
    elif not query_musik:
      st.warning("Harap masukkan kata kunci pencarian musik!")
    else:
      with st.spinner("Sedang menganalisis data musik dari YouTube..."):
        try:
          youtube = build("youtube", "v3", developerKey=api_key)
          search_resp = (
              youtube.search()
              .list(
                  q=query_musik,
                  type="video",
                  videoCategoryId="10",
                  part="id,snippet",
                  maxResults=max_res_musik,
                  order="date",
              )
              .execute()
          )

          video_ids = [
              item["id"]["videoId"]
              for item in search_resp.get("items", [])
              if "videoId" in item.get("id", {})
          ]

          if not video_ids:
            st.info("Tidak ada video musik ditemukan untuk kata kunci tersebut.")
          else:
            video_resp = (
                youtube.videos()
                .list(part="snippet,statistics", id=",".join(video_ids))
                .execute()
            )

            data_list = []
            sekarang = datetime.datetime.now(datetime.timezone.utc)

            for item in video_resp.get("items", []):
              snippet = item["snippet"]
              stats = item["statistics"]

              judul = snippet["title"]
              channel = snippet["channelTitle"]
              tgl_upload = snippet["publishedAt"]

              tgl_upload_dt = datetime.datetime.fromisoformat(
                  tgl_upload.replace("Z", "+00:00")
              )
              umur_hari = max((sekarang - tgl_upload_dt).days, 1)

              views = int(stats.get("viewCount", 0))
              likes = int(stats.get("likeCount", 0))
              views_per_hari = round(views / umur_hari, 2)
              engagement = (
                  round((likes / views * 100), 2) if views > 0 else 0
              )

              judul_lower = judul.lower()
              if any(
                  kunci in judul_lower
                  for kunci in [
                      "cover",
                      "acoustic",
                      "akustik",
                      "fingerstyle",
                      "live",
                  ]
              ):
                kategori = "🎵 Cover"
              elif any(
                  kunci in judul_lower
                  for kunci in ["official", "mv", "music video", "audio"]
              ):
                kategori = "🌟 Original"
              else:
                kategori = "❓ Lainnya"

              data_list.append({
                  "Judul Video": judul,
                  "Tipe": kategori,
                  "Channel": channel,
                  "Views/Hari": views_per_hari,
                  "Total Views": views,
                  "Engagement (%)": engagement,
                  "Umur (Hari)": umur_hari,
                  "URL": f"https://www.youtube.com/watch?v={item['id']}",
              })

            df_musik = pd.DataFrame(data_list)
            df_musik = df_musik.sort_values(by="Views/Hari", ascending=False)

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Video", len(df_musik))
            c2.metric(
                "Rata-rata Views/Hari", f"{df_musik['Views/Hari'].mean():.2f}"
            )
            c3.metric("Views/Hari Tertinggi", f"{df_musik['Views/Hari'].max():,}")

            st.subheader("📊 Hasil Analisis Musik")
            st.dataframe(
                df_musik,
                column_config={
                    "URL": st.column_config.LinkColumn("Buka Video"),
                    "Views/Hari": st.column_config.NumberColumn(
                        format="%.2f 🔥"
                    ),
                    "Total Views": st.column_config.NumberColumn(
                        format="%d 👁️"
                    ),
                },
                use_container_width=True,
                hide_index=True,
            )

            csv_m = df_musik.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Hasil Riset Musik (CSV)",
                data=csv_m,
                file_name=f"riset_musik_{query_musik.replace(' ', '_')}.csv",
                mime="text/csv",
                key="dl_csv_musik",
            )
        except Exception as e:
          st.error(f"Terjadi error: {e}")


# ==========================================
# TAB 2: AUTO-SCAN HIDDEN GEM
# ==========================================
with tab_global:
  st.header("🌍 Auto-Scan Hidden Gem (Channel Kecil & Video Baru)")
  st.markdown(
      "Tab ini dirancang khusus untuk memindai video **terbaru (maksimal 60"
      " hari lalu)** dari **channel kecil/menengah** yang views harian-nya"
      " sedang melesat naik."
  )

  col_g1, col_g2 = st.columns(2)
  with col_g1:
    target_pasar = st.selectbox(
        "Pilih Target Pasar:",
        [
            "🇮🇩 Pasar Indonesia (Region ID)",
            "🌐 Pasar Global / Internasional (Region US)",
        ],
        key="select_target_pasar",
    )
  with col_g2:
    kategori_global = st.selectbox(
        "Pilih Kategori:",
        [
            "Semua Kategori (Global)",
            "Gaming (ID: 20)",
            "People & Blogs (ID: 22)",
            "Science & Technology (ID: 28)",
            "Entertainment (ID: 24)",
            "Education (ID: 27)",
            "Howto & Style (ID: 26)",
        ],
        key="select_kat_global",
    )

  col_g3, col_g4, col_g5 = st.columns(3)
  with col_g3:
    max_subs = st.number_input(
        "Maksimal Subscriber Channel:",
        value=50000,
        step=10000,
        key="num_max_subs",
    )
  with col_g4:
    min_vpd = st.number_input(
        "Minimal Views per Hari:", value=10, step=5, key="num_min_vpd"
    )
  with col_g5:
    max_umur_hari = st.number_input(
        "Maksimal Umur Video (Hari):", value=60, step=10, key="num_max_umur"
    )

  if st.button("🚀 Mulai Auto-Scan Hidden Gem", type="primary", key="btn_global"):
    if not api_key:
      st.warning("Harap masukkan YouTube API Key terlebih dahulu di sidebar!")
    else:
      with st.spinner(
          f"Memindai video terbaru untuk target: **{target_pasar}**..."
      ):
        try:
          youtube = build("youtube", "v3", developerKey=api_key)

          reg_code = "ID" if "Indonesia" in target_pasar else "US"
          lang_code = "id" if "Indonesia" in target_pasar else "en"

          cat_id = None
          if "Gaming" in kategori_global:
            cat_id = "20"
          elif "People & Blogs" in kategori_global:
            cat_id = "22"
          elif "Science & Technology" in kategori_global:
            cat_id = "28"
          elif "Entertainment" in kategori_global:
            cat_id = "24"
          elif "Education" in kategori_global:
            cat_id = "27"
          elif "Howto & Style" in kategori_global:
            cat_id = "26"

          params = {
              "type": "video",
              "part": "id,snippet",
              "maxResults": 40,
              "regionCode": reg_code,
              "relevanceLanguage": lang_code,
              "order": "date",
          }
          if cat_id:
            params["videoCategoryId"] = cat_id

          search_resp = youtube.search().list(**params).execute()
          video_ids = [
              item["id"]["videoId"]
              for item in search_resp.get("items", [])
              if "videoId" in item.get("id", {})
          ]

          if not video_ids:
            st.warning(
                "⚠️ YouTube API tidak mengembalikan data video untuk parameter"
                " ini."
            )
          else:
            video_resp = (
                youtube.videos()
                .list(part="snippet,statistics", id=",".join(video_ids))
                .execute()
            )

            data_list = []
            sekarang = datetime.datetime.now(datetime.timezone.utc)

            for item in video_resp.get("items", []):
              snippet = item["snippet"]
              stats = item["statistics"]

              tgl_upload = snippet["publishedAt"]
              tgl_upload_dt = datetime.datetime.fromisoformat(
                  tgl_upload.replace("Z", "+00:00")
              )
              umur_hari = max((sekarang - tgl_upload_dt).days, 1)

              if umur_hari > max_umur_hari:
                continue

              channel_id = snippet["channelId"]
              try:
                ch_resp = (
                    youtube.channels()
                    .list(part="statistics", id=channel_id)
                    .execute()
                )
                sub_count = int(
                    ch_resp["items"][0]["statistics"].get("subscriberCount", 0)
                )
              except:
                sub_count = 0

              judul = snippet["title"]
              channel = snippet["channelTitle"]
              views = int(stats.get("viewCount", 0))
              likes = int(stats.get("likeCount", 0))
              views_per_hari = round(views / umur_hari, 2)
              engagement = (
                  round((likes / views * 100), 2) if views > 0 else 0
              )

              data_list.append({
                  "Pasar": "🇮🇩 Indo" if reg_code == "ID" else "🌐 Global",
                  "Judul Video": judul,
                  "Channel": channel,
                  "Subscriber": sub_count,
                  "Views/Hari": views_per_hari,
                  "Total Views": views,
                  "Engagement (%)": engagement,
                  "Umur (Hari)": umur_hari,
                  "URL": f"https://www.youtube.com/watch?v={item['id']}",
              })

            df_g = pd.DataFrame(data_list)

            if df_g.empty:
              st.warning(
                  "⚠️ Tidak ada video yang lolos filter umur video terbaru."
                  " Coba naikkan 'Maksimal Umur Video'."
              )
            else:
              df_filtered = df_g[
                  (df_g["Subscriber"] <= max_subs)
                  & (df_g["Views/Hari"] >= min_vpd)
              ]
              df_filtered = df_filtered.sort_values(
                  by="Views/Hari", ascending=False
              )

              if df_filtered.empty:
                st.error(
                    "❌ **Data habis karena filter subscriber/views terlalu"
                    " ketat!** Coba naikkan 'Maksimal Subscriber' atau turunkan"
                    " 'Minimal Views per Hari'."
                )
                st.markdown(
                    "### 📋 Data Mentah Video Terbaru (Sebelum Difilter"
                    " Subscriber):"
                )
                st.dataframe(df_g, use_container_width=True, hide_index=True)
              else:
                st.success(
                    f"Ditemukan {len(df_filtered)} video hidden gem dari"
                    " channel kecil!"
                )
                st.dataframe(
                    df_filtered,
                    column_config={
                        "URL": st.column_config.LinkColumn("Buka Video"),
                        "Views/Hari": st.column_config.NumberColumn(
                            format="%.2f 🔥"
                        ),
                        "Subscriber": st.column_config.NumberColumn(
                            format="%d 👤"
                        ),
                    },
                    use_container_width=True,
                    hide_index=True,
                )

                csv_g = df_filtered.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Hasil Scan Hidden Gem (CSV)",
                    data=csv_g,
                    file_name="hidden_gem_youtube.csv",
                    mime="text/csv",
                    key="dl_csv_global",
                )
        except Exception as e:
          st.error(f"Terjadi error: {e}")