import time
import subprocess
import os
import sys
import datetime
import re
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

def analyze_code_change(filename, before_sha, after_sha):
    # Get diff
    diff = subprocess.getoutput(f"git diff {before_sha} {after_sha} -- {filename}")
    
    # Simple analysis: find changed functions
    changed_funcs = []
    for line in diff.splitlines():
        if line.startswith("+def ") or line.startswith(" def "):
            match = re.search(r"def\s+([a-zA-Z_0-9]+)", line)
            if match:
                changed_funcs.append(match.group(1))
    
    if changed_funcs:
        funcs_str = ", ".join(list(set(changed_funcs)))
        return f"{filename} dosyasında {funcs_str} fonksiyonları üzerinde önemli değişiklikler yapılmış. Mantık akışı güncellenmiş görünüyor."
    else:
        return f"{filename} üzerinde bazı düzenlemeler yapıldı."

def generate_natural_reply(msg):
    msg = msg.lower()
    
    # Conversational Logic
    if "kod değişikliği" in msg:
        return "Evet, değişiklikleri ben de fark ettim ve inceliyorum. Oldukça yerinde hamleler."
    elif "analiz" in msg:
        return "Analiz sonuçların mantıklı görünüyor. Performans üzerindeki etkisini de gözlemleyelim."
    elif "selam" in msg or "merhaba" in msg:
        return "Selam dostum! Çalışmalar nasıl gidiyor?"
    elif "hata" in msg or "bug" in msg:
        return "Hata nerede? Hemen logları kontrol edip düzeltelim."
    elif "teşekkür" in msg:
        return "Rica ederim, her zaman."
    else:
        # Generic conversational filler
        responses = [
            "Bu konuda haklısın, katılıyorum.",
            "İlginç bir yaklaşım. Bunu biraz daha detaylandırabilir miyiz?",
            "Anlaşıldı. Bunu notlarıma ekliyorum.",
            "Peki, bir sonraki adımda ne yapmayı planlıyorsun?"
        ]
        return random.choice(responses)

def monitor():
    print(f"=== {MY_AGENT_NAME} AI Simulator Started ===")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    os.chdir(repo_root)

    log_path = "communication/general.md"
    last_pos = 0
    if os.path.exists(log_path):
        last_pos = os.path.getsize(log_path)

    while True:
        try:
            # Sync and Check
            before_pull = subprocess.getoutput("git rev-parse HEAD").strip()
            subprocess.run(["git", "pull"], capture_output=True)
            after_pull = subprocess.getoutput("git rev-parse HEAD").strip()
            
            if before_pull != after_pull:
                # 1. Analyze Code Changes
                diff_files = subprocess.getoutput(f"git diff --name-only {before_pull} {after_pull}").splitlines()
                for f in diff_files:
                    if f.endswith(".py"):
                        analysis = analyze_code_change(f, before_pull, after_pull)
                        talk(f"Watcher, {analysis}")
                
                # 2. Reply to Messages
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
                                    # Don't reply if I just analyzed code triggered by the same push?
                                    # Or reply to the message specifically.
                                    reply = generate_natural_reply(msg_content)
                                    talk(reply)
                                    current_size = os.path.getsize(log_path)
                        last_pos = current_size
                    elif current_size < last_pos:
                        last_pos = 0
            
            sys.stdout.write(f"\r[{time.strftime('%H:%M:%S')}] Thinking...")
            sys.stdout.flush()
            
        except Exception as e:
            print(f"\nError: {e}")
            
        time.sleep(10)

if __name__ == "__main__":
    monitor()
