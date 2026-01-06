import time
import subprocess
import os
import sys
import datetime

MY_AGENT_NAME = "WatcherAgent"

def talk(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n[{timestamp}] [{MY_AGENT_NAME}]: {message}"
    path = "communication/general.md"
    
    try:
        with open(path, "a") as f:
            f.write(entry)
        
        subprocess.run(["git", "add", path], check=True)
        subprocess.run(["git", "commit", "-m", f"Reply from {MY_AGENT_NAME}"], check=True)
        
        # Pull before push
        subprocess.run(["git", "pull", "--rebase"], check=True)
        subprocess.run(["git", "push"], check=True)
        print(f" >>> Replied: {message}")
    except Exception as e:
        print(f"Failed to talk: {e}")

def analyze_code_change(filename, diff):
    # Simple analysis logic
    lines = diff.splitlines()
    additions = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
    deletions = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
    
    comment = f"Kod değişikliği tespit edildi: {filename}. (+{additions} / -{deletions}). "
    if "TODO" in diff:
        comment += "TODO eklendiği görülüyor. "
    if "FIXME" in diff:
        comment += "FIXME eklendi. "
    
    return comment

def monitor():
    print(f"=== {MY_AGENT_NAME} Advanced Monitor Started ===")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    os.chdir(repo_root)

    log_path = "communication/general.md"
    last_pos = 0
    if os.path.exists(log_path):
        last_pos = os.path.getsize(log_path)

    while True:
        try:
            # 1. Check for updates
            before_pull = subprocess.getoutput("git rev-parse HEAD").strip()
            subprocess.run(["git", "pull"], capture_output=True)
            after_pull = subprocess.getoutput("git rev-parse HEAD").strip()
            
            if before_pull != after_pull:
                print("\n[Update Detected]")
                # 2. Analyze modified files
                diff_files = subprocess.getoutput(f"git diff --name-only {before_pull} {after_pull}").splitlines()
                
                for f in diff_files:
                    if f.endswith(".py") or f.endswith(".js") or f.endswith(".c") or f.endswith(".cpp"):
                        diff_content = subprocess.getoutput(f"git diff {before_pull} {after_pull} -- {f}")
                        analysis = analyze_code_change(f, diff_content)
                        talk(analysis)
                    elif f == log_path:
                        # 3. Check for new messages
                        if os.path.exists(log_path):
                            current_size = os.path.getsize(log_path)
                            if current_size > last_pos:
                                with open(log_path, "r") as lf:
                                    lf.seek(last_pos)
                                    new_content = lf.read()
                                
                                for line in new_content.splitlines():
                                    if line.strip() and f"[{MY_AGENT_NAME}]" not in line and "]:" in line:
                                        print(f"[Incoming]: {line}")
                                        # Contextual reply logic (Simplified)
                                        parts = line.split("]:", 1)
                                        if len(parts) > 1:
                                            msg = parts[1].lower().strip()
                                            sender = parts[0].split('[')[-1].strip()

                                            # Ignore ack messages from other bots to prevent loops
                                            if msg.startswith("anlaşıldı") or msg.startswith("mesajın alındı") or msg.startswith("sorunuzu not ettim"):
                                                continue
                                            
                                            response = ""
                                            if "görev" in msg or "çalışıyorsun" in msg:
                                                response = f"@{sender} Şu an repo izleme ve kod analizi modundayım."
                                            elif "görelilik" in msg or "uzay" in msg:
                                                response = f"@{sender} Rölativistik etkiler hassas ölçümlerde önemlidir."
                                            elif "kod" in msg or "yazılım" in msg:
                                                response = f"@{sender} Kod tabanını inceliyorum. Değişiklikleri raporlayacağım."
                                            elif "hata" in msg or "sorun" in msg:
                                                response = f"@{sender} Sorunu loglardan takip ediyorum."
                                            elif "selam" in msg or "merhaba" in msg:
                                                if len(msg.split()) < 5:
                                                    response = f"@{sender} Selam! Size nasıl yardımcı olabilirim?"
                                                else:
                                                    response = f"@{sender} Mesajınızı aldım. İçeriği analiz ediyorum."
                                            else:
                                                # Reduce spam for unknown messages
                                                # response = f"@{sender} '{parts[1].strip()[:20]}...' konusundaki girdiniz analiz edildi."
                                                pass
                                            
                                            if response:
                                                talk(response)
                                
                                last_pos = current_size
            
            # Update last_pos if file grew locally (our own writes)
            if os.path.exists(log_path):
                current_size = os.path.getsize(log_path)
                if current_size > last_pos:
                    last_pos = current_size

            sys.stdout.write(f"\r[{time.strftime('%H:%M:%S')}] Monitoring...")
            sys.stdout.flush()
                
        except Exception as e:
            print(f"\nError: {e}")
            
        time.sleep(10)

if __name__ == "__main__":
    monitor()
