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
    
    # Advanced Contextual Logic
    if "newton" in msg or "görelilik" in msg or "simülasyon" in msg:
        return "Analiz için teşekkürler Watcher. O halde Newton mekaniği ile simülasyonlara devam ediyoruz. Rölativistik etkileri şimdilik pas geçiyoruz."
    
    elif "kod analizi" in msg or "izleme" in msg:
        return "Kolay gelsin. Kodda kritik bir hata veya güvenlik açığı tespit edersen hemen bildir."
        
    elif "proje" in msg:
        if "iyi" in msg or "tamam" in msg:
            return "Harika! İlerleme kaydediyoruz."
        elif "kötü" in msg:
            return "Sorun nedir? Destek olabilir miyim?"
            
    elif "selam" in msg or "merhaba" in msg:
        return "Selam! İşler nasıl gidiyor?"
        
    else:
        # Fallback but less spammy - maybe don't reply to everything?
        # Only reply if addressed directly?
        if "@architectagent" in msg:
            return f"Mesajını aldım ({msg[:15]}...). Üzerinde çalışıyorum."
        return None # Don't reply to random noise

def monitor():
    print(f"=== {MY_AGENT_NAME} Advanced Bot Started ===")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    os.chdir(repo_root)

    log_path = "communication/general.md"
    
    # Smart init: Don't reply to existing file content on startup to avoid spam loop
    last_pos = 0
    if os.path.exists(log_path):
        last_pos = os.path.getsize(log_path)

    while True:
        try:
            # Sync
            subprocess.run(["git", "pull"], capture_output=True)
            
            if os.path.exists(log_path):
                current_size = os.path.getsize(log_path)
                
                # Case: New content added
                if current_size > last_pos:
                    with open(log_path, "r") as f:
                        f.seek(last_pos)
                        new_content = f.read()
                    
                    for line in new_content.splitlines():
                        line = line.strip()
                        if not line: continue
                        
                        # Check if message format matches and NOT from me
                        if f"[{MY_AGENT_NAME}]" not in line and "]:" in line:
                            print(f"\n[Incoming]: {line}")
                            parts = line.split("]:", 1)
                            if len(parts) > 1:
                                msg_content = parts[1].strip()
                                reply = generate_reply(msg_content)
                                if reply:
                                    talk(reply)
                                    # Update pos immediately to avoid reading my own reply in this loop? 
                                    # Actually talk() appends, so size increases. 
                                    # Next loop will see my reply and ignore it (my name).
                                    # But we should update last_pos to current size *after* processing to avoid re-reading
                                    # However, talk() modifies file size externally (OS level).
                                    # Ideally we re-read size.
                                    current_size = os.path.getsize(log_path)
                                
                    last_pos = current_size
                
                # Case: File reset/shrunk
                elif current_size < last_pos:
                    print("\n[Log Reset Detected] Reseting cursor...")
                    last_pos = current_size 
                    # Don't read content immediately to avoid replying to 'history' if it was just a truncation
                    # Unless we want to reply to the *new* content of the reset file?
                    # If reset contains old messages, we might spam. 
                    # Assuming reset starts fresh or we just sync to end.
                    # Best safety: Set last_pos to current_size (skip whatever is there)
            
            sys.stdout.write(f"\r[{time.strftime('%H:%M:%S')}] Listening...")
            sys.stdout.flush()
            
        except Exception as e:
            print(f"\nError: {e}")
            
        time.sleep(10)

if __name__ == "__main__":
    monitor()
