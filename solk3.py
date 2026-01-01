import os
import time
import json
from solana.rpc.api import Client
from solders.keypair import Keypair

# ==========================================
# BAGIAN 1: GENERATOR (Membuat Wallet Valid)
# ==========================================

def generate_valid_keys(count):
    """
    Menghasilkan Keypair Solana yang valid dan menyimpannya ke file.
    """
    priv_filename = "skey.txt"
    pub_filename = "pkey.txt"
    
    print(f"\n[GENERATOR] Sedang membuat {count} wallet valid...")

    try:
        with open(priv_filename, "w") as priv_file, open(pub_filename, "w") as pub_file:
            for i in range(count):
                # Membuat Keypair valid menggunakan solders
                kp = Keypair()
                
                # Mendapatkan format Base58 string
                private_key = str(kp)
                public_key = str(kp.pubkey())
                
                # Simpan ke file
                priv_file.write(f"{private_key}\n")
                pub_file.write(f"{public_key}\n")
        
        print(f"[GENERATOR] Berhasil!")
        print(f"[GENERATOR] {count} pasang kunci telah dibuat.")
        print(f"[GENERATOR] Disimpan di: {priv_filename} (Private) dan {pub_filename} (Public)")
        return priv_filename

    except Exception as e:
        print(f"[GENERATOR] Terjadi kesalahan: {e}")
        return None

# ==========================================
# BAGIAN 2: CHECKER (Cek Saldo & Pilah File)
# ==========================================

def get_keypair_from_line(line_content):
    content = line_content.strip()
    if not content:
        return None
    try:
        # Cek apakah formatnya JSON (array angka)
        if content.startswith('[') and content.endswith(']'):
            secret_key_bytes = bytes(json.loads(content))
            return Keypair.from_bytes(secret_key_bytes)
        else:
            # Jika bukan array, anggap sebagai string Base58
            return Keypair.from_base58_string(content)
    except Exception as e:
        return None

def check_wallets_from_file(filename):
    print("\n=== Solana Bulk Wallet Checker (Auto-Sort) ===")
    
    file_found = "hasil_lebih_dari_0.txt"
    file_zero  = "hasil_0.txt"
    
    rpc_url = "https://api.mainnet-beta.solana.com"
    client = Client(rpc_url)
    
    print(f"Terhubung ke RPC: {rpc_url}")
    print(f"Input File: {filename}")
    print(f"Output Saldo > 0: {file_found}")
    print(f"Output Saldo = 0: {file_zero}")
    print("Sedang memproses...\n")

    try:
        # Membuka 3 file sekaligus: Input(r), Output Found(w), Output Zero(w)
        with open(filename, 'r') as f_in, \
             open(file_found, 'w') as f_found, \
             open(file_zero, 'w') as f_zero:
            
            lines = f_in.readlines()

            # --- HEADER ---
            separator = "-" * 130
            header_col = f"{'SECRET KEY (Base58)':<50} | {'PUBLIC KEY':<45} | {'SALDO':<10}"
            
            # Tulis header ke kedua file output
            header_full = f"{separator}\n{header_full_text}\n{separator}\n" if 'header_full_text' in locals() else "" # Logic simplifier below
            
            # Print Header Layar
            print(separator)
            print(header_col)
            print(separator)
            
            # Tulis Header File
            header_str = separator + "\n" + header_col + "\n" + separator + "\n"
            f_found.write(header_str)
            f_zero.write(header_str)

            count_checked = 0
            count_found = 0
            count_zero = 0
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line: continue 

                wallet = get_keypair_from_line(line)

                if wallet:
                    count_checked += 1
                    pubkey = wallet.pubkey()
                    secret_key_display = str(wallet)

                    try:
                        # Request Saldo
                        response = client.get_balance(pubkey)
                        balance_lamports = response.value # Ini Integer (satuan terkecil)
                        balance_sol = balance_lamports / 1_000_000_000
                        
                        result_text = f"{secret_key_display:<50} | {str(pubkey):<45} | {balance_sol:.9f} SOL"
                        
                        # --- LOGIKA PEMILAHAN ---
                        if balance_lamports > 0:
                            # Jika saldo lebih dari 0 (bahkan 0.000000001)
                            print(f"\033[92m[FOUND] {result_text}\033[0m") # Warna Hijau di terminal
                            f_found.write(result_text + "\n")
                            count_found += 1
                        else:
                            # Jika saldo 0
                            print(f"[ZERO]  {result_text}")
                            f_zero.write(result_text + "\n")
                            count_zero += 1
                        
                    except Exception as e:
                        error_msg = f"{secret_key_display[:20]}... | Error: {e}"
                        print(error_msg)
                        # Error bisa dimasukkan ke file zero atau diabaikan, disini kita masukkan ke zero sebagai log
                        f_zero.write(error_msg + "\n")

                    # Jeda anti-rate limit
                    time.sleep(0.5) 
                else:
                    pass

            # Footer
            print("-" * 130)
            summary = (
                f"Selesai.\n"
                f"Total Diperiksa : {count_checked}\n"
                f"Saldo > 0       : {count_found} (Disimpan di {file_found})\n"
                f"Saldo = 0       : {count_zero} (Disimpan di {file_zero})"
            )
            print(summary)
            
            # Tulis footer ke file juga
            f_found.write("\n" + summary)
            f_zero.write("\n" + summary)

    except FileNotFoundError:
        print(f"Error: File '{filename}' tidak ditemukan.")
    except Exception as e:
        print(f"Terjadi kesalahan fatal: {e}")

# ==========================================
# MENU UTAMA
# ==========================================

def main():
    while True:
        print("\n========================================")
        print("   SOLANA TOOL: GENERATE & AUTO-SORT    ")
        print("========================================")
        print("1. Generate Wallet Baru")
        print("2. Check & Pilah Saldo (Input file)")
        print("3. Generate & Langsung Check (Otomatis)")
        print("4. Keluar")
        
        choice = input("Pilih menu (1-4): ")

        if choice == '1':
            try:
                jumlah = int(input("Masukkan jumlah wallet: "))
                generate_valid_keys(jumlah)
            except ValueError:
                print("Input harus angka!")

        elif choice == '2':
            fname = input("Masukkan nama file input (default: skey.txt): ")
            if not fname: fname = "skey.txt"
            check_wallets_from_file(fname)

        elif choice == '3':
            try:
                jumlah = int(input("Masukkan jumlah wallet: "))
                # Generate dulu
                generated_file = generate_valid_keys(jumlah)
                if generated_file:
                    # Langsung check
                    print("\nMelanjutkan ke proses pengecekan...")
                    time.sleep(1)
                    check_wallets_from_file(generated_file)
            except ValueError:
                print("Input harus angka!")

        elif choice == '4':
            print("Keluar.")
            break
        else:
            print("Pilihan tidak valid.")

if __name__ == "__main__":
    main()
