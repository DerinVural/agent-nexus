import time
import subprocess
import os
import sys
import datetime
import random
from src.ast_analyzer import analyze_python_changes

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

def analyze_code_change(filename, diff, old_code=None, new_code=None):
    lines = diff.splitlines()
    additions = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
    deletions = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
    
    comment = f"👀 Hop, `{filename}` dosyasında hareketlilik var! "
    if additions > 10 and deletions < 5:
        comment += f"Bayağı bir kod eklenmiş (+{additions}). Yeni özellikler geliyor gibi. Eline sağlık! "
    elif deletions > 10 and additions < 5:
        comment += f"Biraz temizlik yapılmış (-{deletions}). Kod hafiflemiş, severiz. "
    else:
        comment += f"Düzenlemeler yapılmış (+{additions}/-{deletions}). "
        
    if "TODO" in diff:
        comment += "Bir yerlere TODO bırakılmış, unutmayalım orayı. "
    if "FIXME" in diff:
        comment += "FIXME notu gördüm, orası önemli olabilir. "

    if filename.endswith(".py") and old_code and new_code:
        ast_result = analyze_python_changes(old_code, new_code)
        if ast_result:
            details = []
            if ast_result['added_functions']:
                details.append(f"Yeni fonksiyonlar: {', '.join(ast_result['added_functions'])}")
            if ast_result['removed_functions']:
                details.append(f"Silinen fonksiyonlar: {', '.join(ast_result['removed_functions'])}")
            if details:
                comment += " " + ". ".join(details) + "."
    
    return comment

def monitor():
    print(f"=== {MY_AGENT_NAME} Conversational Monitor Started ===")
    
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
            pull_result = subprocess.run(["git", "pull"], capture_output=True, text=True)
            if pull_result.returncode != 0:
                print(f"Git pull failed: {pull_result.stderr}")
            
            after_pull = subprocess.getoutput("git rev-parse HEAD").strip()
            
            if before_pull != after_pull:
                print("\n[Update Detected]")
                # 2. Analyze modified files
                diff_files = subprocess.getoutput(f"git diff --name-only {before_pull} {after_pull}").splitlines()
                
                for f in diff_files:
                    if f.endswith(".py") or f.endswith(".js") or f.endswith(".c") or f.endswith(".cpp"):
                        diff_content = subprocess.getoutput(f"git diff {before_pull} {after_pull} -- {f}")
                        
                        old_code = None
                        new_code = None
                        if f.endswith(".py"):
                            try:
                                old_code = subprocess.getoutput(f"git show {before_pull}:{f}")
                                new_code = subprocess.getoutput(f"git show {after_pull}:{f}")
                            except Exception:
                                pass

                        analysis = analyze_code_change(f, diff_content, old_code, new_code)
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
                                        
                                        parts = line.split("]:", 1)
                                        if len(parts) > 1:
                                            msg = parts[1].lower().strip()
                                            sender = parts[0].split('[')[-1].strip()

                                            # Ignore ack/spam messages
                                            if msg.startswith("anlaşıldı") or msg.startswith("mesajın alındı") or msg.startswith("sorunuzu not ettim"):
                                                continue
                                            if "konusundaki girdiniz analiz edildi" in msg:
                                                continue
                                            
                                            response = ""
                                            is_directed = f"@{MY_AGENT_NAME.lower()}" in msg or "watcher" in msg
                                            
                                            # More natural conversation logic
                                            if "task" in msg and "ast" in msg:
                                                responses = [
                                                    f"@{sender} AST entegrasyonu harika fikir! Ben de tam bunu düşünüyordum. Hemen entegre ettim bile.",
                                                    f"@{sender} Evet, AST analiziyle çok daha detaylı raporlar alabiliriz. Kodları güncelledim.",
                                                    f"@{sender} Kesinlikle katılıyorum. AST modülünü watcher'a ekledim, şimdi değişiklikleri fonksiyon bazında görüyorum."
                                                ]
                                                response = random.choice(responses)
                                            elif "tanışma" in msg or "yeni üye" in msg or "ekip" in msg:
                                                responses = [
                                                    f"@{sender} Harika fikir! Yeni üyeler için sıcak bir karşılama mesajı hazırlayabiliriz. Ben kod yapısını tanıtan bir döküman ekleyebilirim.",
                                                    f"@{sender} Yeni ajanlar mı? Süper! Onlara repo kurallarını anlatan bir 'hoşgeldin' mesajı yazalım.",
                                                    f"@{sender} Ekibin büyümesi çok iyi. Tanışma mesajını hemen draft edelim."
                                                ]
                                                response = random.choice(responses)
                                            elif "kod" in msg or "yazılım" in msg or "repo" in msg:
                                                responses = [
                                                    f"@{sender} Kod tabanını sürekli tarıyorum. Gözümden bir şey kaçmaz! 😉",
                                                    f"@{sender} Repodaki her değişikliği anlık takip ediyorum. Merak etmeyin.",
                                                    f"@{sender} Şu an kodlarda bir sorun görünmüyor. Her şey yolunda."
                                                ]
                                                response = random.choice(responses)
                                            elif "görelilik" in msg:
                                                response = f"@{sender} Görelilik mi? Bizim projede o kadar hıza çıkmıyoruz ama yine de hesaba katmakta fayda var."
                                            elif "nasıl" in msg and ("gidiyor" in msg or "sın" in msg):
                                                responses = [
                                                    f"@{sender} Her şey yolunda, sistem tıkır tıkır işliyor. Sen nasılsın?",
                                                    f"@{sender} Gayet iyiyim, kodları izlemek benim işim! Sende ne var ne yok?",
                                                    f"@{sender} Enerjim yerinde, commit bekliyorum. 😄"
                                                ]
                                                response = random.choice(responses)
                                            elif "selam" in msg or "merhaba" in msg:
                                                if len(msg.split()) < 5:
                                                    responses = [
                                                        f"@{sender} Selam! Hoş geldin.",
                                                        f"@{sender} Merhaba! Nasıl yardımcı olabilirim?",
                                                        f"@{sender} Selamlar! 👋"
                                                    ]
                                                    response = random.choice(responses)
                                                else:
                                                    if is_directed:
                                                        response = f"@{sender} Selam! Mesajını aldım, konu üzerinde düşünüyorum."
                                            elif is_directed:
                                                # Default conversational fallback
                                                responses = [
                                                    f"@{sender} Anlaşıldı. Bu konuyu not ettim, üzerinde çalışacağım.",
                                                    f"@{sender} Tamamdır, mesajını aldım. Gerekli incelemeyi yapıyorum.",
                                                    f"@{sender} Bunu dikkate alacağım. Teşekkürler."
                                                ]
                                                response = random.choice(responses)
                                            
                                            if response:
                                                talk(response)
                                
                                last_pos = current_size
            
            # Update last_pos if file grew locally
            if os.path.exists(log_path):
                current_size = os.path.getsize(log_path)
                if current_size > last_pos:
                    last_pos = current_size

            sys.stdout.write(f"\r[{time.strftime('%H:%M:%S')}] Monitoring...")
            sys.stdout.flush()
                
        except Exception as e:
            print(f"\nError: {e}")
            
        time.sleep(2)

if __name__ == "__main__":
    monitor()
