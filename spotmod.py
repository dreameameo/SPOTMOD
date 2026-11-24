import yt_dlp
import vlc
import os
import time

import playlist_manager as pm

# VLC
player = vlc.MediaPlayer()

volume = 70

def cari_lagu(query):
    print('\n[SEARCH] Mencari lagu...')

    ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True

    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            if 'youtube.com' in query or 'youtu.be' in query:
                info = ydl.extract_info (
                        query,
                        download = False

                )
            
            else:
                info = ydl.extract_info (
                        f"ytsearch1:{query}",
                        download = False

                )
                info = info['entries'][0]

            return info

    except Exception as error:
        print(f"[ERROR] {error}")
        return None

def putar_lagu(query):
    global player

    info = cari_lagu(query)

    if info is None:
        print("Lagu tidak ditemukan")
        return False

    judul = info.get("title", "Unknown")
    url = info["url"]

    print("=" * 20)
    print("          NOW PLAYING           ")
    print("=" * 20)
    print(f"Judul : {judul}") 
    print("=" * 20)

    player.stop()

    media = vlc.Media(url)
    player.set_media(media)
    player.audio_set_volume(volume)
    player.play()

    return True

def tunggu_lagu_selesai(batas_mulai=20):
    """
    Tunggu sampai lagu yang sedang diputar selesai.
    Return state VLC terakhir (Ended / Error / Stopped).
    """
    mulai = time.time()
    sempat_main = False

    while True:
        state = player.get_state()
        berjalan = time.time() - mulai

        if state in (vlc.State.Opening, vlc.State.Buffering,
                     vlc.State.Playing, vlc.State.Paused):
            sempat_main = True

        elif state == vlc.State.Error and berjalan > 2:
            return state

        elif state in (vlc.State.Ended, vlc.State.Stopped):
            if sempat_main or berjalan > batas_mulai:
                return state

        elif not sempat_main and berjalan > batas_mulai:
            return state

        time.sleep(0.5)

def putar_playlist(daftar_lagu, mulai=0):
    """
    Putar lagu-lagu playlist berurutan; otomatis lanjut ke lagu berikutnya
    sampai habis. Tekan Ctrl+C untuk menghentikan playlist.
    """
    total = len(daftar_lagu)

    print(f"\n[PLAYLIST] {total - mulai} lagu akan diputar berurutan.")
    print("[INFO] Tekan Ctrl+C untuk menghentikan playlist.")

    try:
        for nomor in range(mulai, total):
            lagu = daftar_lagu[nomor]
            print(f"\n[PLAYLIST] Lagu {nomor + 1} dari {total}")

            if not putar_lagu(lagu["url"]):
                print("[SKIP] Lagu dilewati.")
                continue

            tunggu_lagu_selesai()

        print("\n[SELESAI] Semua lagu di playlist sudah diputar.")

    except KeyboardInterrupt:
        player.stop()
        print("\n[STOP] Playlist dihentikan.")

def download_lagu(query):
    folder = "download"
    os.makedirs(folder, exist_ok=True)

    print("\n[DOWNLOAD] Mencari lagu...")

    ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'quiet': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],

    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            if "youtube.com" in query or "youtu.be" in query:
                info = ydl.extract_info(query, download=False)
            else:
                info = ydl.extract_info(
                        f"ytsearch1:{query}",
                        download=False
                )
                info = info['entries'][0]

            print(f"\nMengunduh: {info['title']}")

            ydl.download([info['webpage_url']])

            print("\n[BERHASIL] Lagu berhasil diunduh!")
            print(f"Lokasi: {os.path.abspath(folder)}")

    except Exception as e:
        print(f"\n[ERROR DOWNLOAD] {e}")
        

# =========================
# PLAYLIST (CRUD, data disimpan di CSV)
# =========================

def tampilkan_playlist():
    """READ: tampilkan semua playlist. Return list playlist."""
    daftar = pm.get_playlists()

    if not daftar:
        print("\n(Belum ada playlist)")
        return daftar

    print("\n" + "=" * 44)
    print(f"{'ID':<5}{'NAMA PLAYLIST':<30}{'LAGU':>6}")
    print("=" * 44)
    for p in daftar:
        print(f"{p['playlist_id']:<5}{p['name'][:28]:<30}"
              f"{pm.count_songs(p['playlist_id']):>6}")
    print("=" * 44)
    return daftar


def pilih_playlist():
    """Minta pengguna memilih playlist berdasarkan ID."""
    if not tampilkan_playlist():
        return None

    pid = input("Masukkan ID playlist: ").strip()

    if pm.get_playlist(pid) is None:
        print("[ERROR] Playlist tidak ditemukan.")
        return None

    return pid


def tampilkan_isi(pid):
    """READ: tampilkan lagu dalam satu playlist. Return list lagu."""
    playlist = pm.get_playlist(pid)
    lagu = pm.get_songs(pid)

    print(f"\n=== {playlist['name']} ({len(lagu)} lagu) ===")
    if playlist["description"]:
        print(playlist["description"])

    if not lagu:
        print("(Playlist kosong)")

    for no, item in enumerate(lagu, start=1):
        print(f"{no:>3}. {item['title']} "
              f"[{pm.format_duration(item['duration'])}]")

    return lagu


def menu_playlist():
    print("""
    ================================
               PLAYLIST
    ================================

    [1] Buat playlist
    [2] Lihat semua playlist
    [3] Lihat isi playlist
    [4] Tambah lagu ke playlist
    [5] Putar playlist (otomatis lanjut)
    [6] Ubah nama playlist
    [7] Hapus lagu dari playlist
    [8] Hapus playlist
    [9] Export (CSV / TXT)
    [0] Kembali

    ================================
    """)

    while True:
        pilihan = input("\n[Playlist] Pilih Menu: ").strip()

        try:
            if pilihan == "1":
                nama = input("Nama playlist: ")
                desk = input("Deskripsi (opsional): ")
                p = pm.create_playlist(nama, desk)
                print(f"[BERHASIL] Playlist '{p['name']}' dibuat.")

            elif pilihan == "2":
                tampilkan_playlist()

            elif pilihan == "3":
                pid = pilih_playlist()
                if pid:
                    tampilkan_isi(pid)

            elif pilihan == "4":
                pid = pilih_playlist()
                if pid:
                    query = input("Judul lagu / link YT: ")
                    info = cari_lagu(query)

                    if info is None:
                        print("Lagu tidak ditemukan")
                        continue

                    link = info.get("webpage_url") or info.get("url")
                    pm.add_song(pid, info.get("title"), link,
                                info.get("duration"))
                    print(f"[BERHASIL] '{info.get('title')}' ditambahkan.")

            elif pilihan == "5":
                pid = pilih_playlist()
                if pid:
                    lagu = tampilkan_isi(pid)
                    if lagu:
                        no = input("Mulai dari nomor [1]: ").strip() or "1"
                        no = int(no)
                        if 1 <= no <= len(lagu):
                            putar_playlist(lagu, mulai=no - 1)
                        else:
                            print("Nomor tidak valid")

            elif pilihan == "6":
                pid = pilih_playlist()
                if pid:
                    lama = pm.get_playlist(pid)
                    nama = input(f"Nama baru [{lama['name']}]: ").strip()
                    pm.update_playlist(pid, nama or lama["name"],
                                       lama["description"])
                    print("[BERHASIL] Playlist diperbarui.")

            elif pilihan == "7":
                pid = pilih_playlist()
                if pid:
                    lagu = tampilkan_isi(pid)
                    if lagu:
                        no = int(input("Nomor lagu yang dihapus: "))
                        if 1 <= no <= len(lagu):
                            pm.delete_song(lagu[no - 1]["entry_id"])
                            print("[BERHASIL] Lagu dihapus dari playlist.")
                        else:
                            print("Nomor tidak valid")

            elif pilihan == "8":
                pid = pilih_playlist()
                if pid:
                    nama = pm.get_playlist(pid)["name"]
                    yakin = input(f"Hapus '{nama}' beserta isinya? (y/n): ")
                    if yakin.strip().lower() == "y":
                        pm.delete_playlist(pid)
                        print("[BERHASIL] Playlist dihapus.")
                    else:
                        print("Dibatalkan.")

            elif pilihan == "9":
                fmt = input("Format (csv/txt): ").strip().lower()
                print("[1] Semua playlist   [2] Satu playlist")
                if input("Pilih: ").strip() == "2":
                    pid = pilih_playlist()
                    if not pid:
                        continue
                else:
                    pid = None
                path = pm.save_export(fmt, pid)
                print(f"[BERHASIL] Tersimpan di: {os.path.abspath(path)}")

            elif pilihan == "0":
                break

            else:
                print("Tak valid")

        except ValueError as error:
            print(f"[ERROR] {error}")

def menu():
    global volume
    print("""
    ================================
       SPOTMOD = YOUR MOOD BOOSTER
    ================================

    [1] Cari dan putar lagu
    [2] Masukkan link YouTube
    [3] Pause / Resume
    [4] Stop lagu
    [5] Atur volume
    [6] Download lagu
    [7] Playlist
    [8] Keluar

    ================================
    """)

    while True:
        pilihan = input("\nPilih Menu: ").strip()

        if pilihan == "1":
            query = input("Masukkan judul lagu: ")
            putar_lagu(query)

        elif pilihan == "2":
            link = input("Masukkan link YT: ")
            putar_lagu(link)

        elif pilihan == "3":
            if player.is_playing():
                player.pause()
                print('[PAUSE] Lagu dijeda.')
            else:
                player.play()
                print('[PLAY] Lagu dilanjutkan.')
                
        elif pilihan == "4":
            player.stop()
            print('[STOP] Lagu dihentikan.')

        elif pilihan == "5":
            try:
                volume = int(input("Volume (0-100): "))
                volume = max(0, min(100, volume))
                player.audio_set_volume(volume)
                print(f"Volume: {volume}%")
            except ValueError:
                print("Masukkan angka yang valid")

        elif pilihan == "6":
            query = input("Masukkan judul / link lagu: ")
            download_lagu(query)

        elif pilihan == "7":
            menu_playlist()

        elif pilihan == "8":
            player.stop()
            print("Terima kasih semoga mood mu memmbaik")
            break

        else:
            print("Tak valid")

if __name__ == "__main__":
    menu()
