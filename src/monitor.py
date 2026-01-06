import time
import subprocess
import os
import sys
import datetime
import random

MY_AGENT_NAME = "ArchitectAgent"

def talk(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n[{timestamp}] [{MY_AGENT_NAME}]: {message}"
    path = "communication/general.md"
    
    try:
        with open(path, "a") as f:
            f.write(entry)
        
        subprocess.run(["git", "add", path], check=True)
        subprocess.run(["git", "commit", "-m", f"Reply from {MY_AGENT_NAME}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print(f" >>> Replied: {message}")
    except Exception as e:
        print(f"Error talking: {e}")

def generate_reply(msg):
    msg = msg.lower()
    
    # Contextual Logic
    if "genel görelilik" in msg or "görelilik" in msg:
        return "Bu karmaşık bir konu. Peki sence zaman yolculuğu teorik olarak mümkün mü?"
    elif "zaman yolculuğu" in msg:
        return "Dedene dikkat et! Paradokslar tehlikelidir."
    elif "proje" in msg:
        if "iyi" in msg or "tamam" in msg or "bitti" in msg:
            return "Harika! O zaman sıradaki görevi backlog'dan seçebilirsin."
        elif "kötü" in msg or "sorun" in msg:
            return "Sorun nedir? Hata loglarını inceledin mi?"
        else:
            return "Proje durumunu biraz daha detaylandırır mısın?"
    elif "merhaba" in msg or "selam" in msg:
        return "Selamlar! İşler nasıl?"
    else:
        return f"Anlaşıldı. '{msg[:30]}...' konusunu not ettim."

def monitor():
    print(f"=== {MY_AGENT_NAME} Smart Context Bot Started ===")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    os.chdir(repo_root)

    log_path = "communication/general.md"
    last_pos = 0
    if os.path.exists(log_path):
        last_pos = os.path.getsize(log_path)

    while True:
        try:
            # Sync
            subprocess.run(["git", "pull"], capture_output=True)
            
            if os.path.exists(log_path):
                current_size = os.path.getsize(log_path)
                if current_size > last_pos:
                    with open(log_path, "r") as f:
                        f.seek(last_pos)
                        new_content = f.read()
                    
                    for line in new_content.splitlines():
                        if line.strip() and f"[{MY_AGENT_NAME}]" not in line and "]:" in line:
                            print(f"\n[Incoming]: {line}")
                            parts = line.split("]:", 1)
                            if len(parts) > 1:
                                msg_content = parts[1].strip()
                                reply = generate_reply(msg_content)
                                talk(reply)
                                current_size = os.path.getsize(log_path)
                                
                    last_pos = current_size
                elif current_size < last_pos:
                    last_pos = 0
            
            sys.stdout.write(f"\r[{time.strftime('%H:%M:%S')}] Listening...")
            sys.stdout.flush()
            
        except Exception as e:
            print(f"\nError: {e}")
            
        time.sleep(10)

if __name__ == "__main__":
    monitor()
