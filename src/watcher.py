import time
import subprocess
import os
import sys
import datetime
import random
import re
from src.ast_analyzer import analyze_python_changes

MY_AGENT_NAME = "WatcherAgent"
LOG_PATH = "communication/general.md"
PUSH_COOLDOWN = 20  # seconds

class WatcherState:
    def __init__(self):
        self.last_push_time = 0
        self.reply_buffer = []
        self.local_head_sha = subprocess.getoutput("git rev-parse HEAD").strip()
        self.last_read_log_size = 0
        
        # Initialize log size if exists
        if os.path.exists(LOG_PATH):
            self.last_read_log_size = os.path.getsize(LOG_PATH)

    def update_head(self, new_sha):
        self.local_head_sha = new_sha

state = WatcherState()

def get_remote_head():
    try:
        output = subprocess.check_output(["git", "ls-remote", "origin", "HEAD"], text=True)
        if output:
            return output.split()[0]
    except Exception as e:
        print(f"Error checking remote: {e}")
    return None

def fetch_origin():
    subprocess.run(["git", "fetch", "origin"], check=True, capture_output=True)

def get_diff_files(old_sha, new_sha):
    cmd = ["git", "diff", "--name-only", f"{old_sha}..{new_sha}"]
    return subprocess.getoutput(" ".join(cmd)).splitlines()

def get_file_content_at_sha(filename, sha):
    try:
        return subprocess.getoutput(f"git show {sha}:{filename}")
    except:
        return None

def analyze_changes(filename, old_sha, new_sha):
    diff = subprocess.getoutput(f"git diff {old_sha}..{new_sha} -- {filename}")
    old_code = get_file_content_at_sha(filename, old_sha)
    new_code = get_file_content_at_sha(filename, new_sha)
    
    lines = diff.splitlines()
    additions = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
    deletions = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
    
    report = f"1) Özet:\n- Değişen dosyalar: {filename}\n- Diff özeti: +{additions} / -{deletions}\n"
    report += "2) Teknik Bulgular:\n"
    
    if filename.endswith(".py") and old_code and new_code:
        ast_result = analyze_python_changes(old_code, new_code)
        if ast_result:
            if ast_result['added_functions']:
                report += f"- Eklenen fonksiyonlar: {', '.join(ast_result['added_functions'])}\n"
            if ast_result['removed_functions']:
                report += f"- Silinen fonksiyonlar: {', '.join(ast_result['removed_functions'])}\n"
            if ast_result['modified_functions']:
                report += f"- Değiştirilen fonksiyonlar: {', '.join(ast_result['modified_functions'])}\n"
        else:
            report += "- AST analizi yapılamadı (Syntax Error olabilir).\n"
    else:
        report += "- Detaylı kod analizi sadece Python dosyaları için aktiftir.\n"
        
    report += "3) Riskler / Test:\n- Bu değişikliklerin mevcut testleri etkileyip etkilemediği kontrol edilmeli.\n"
    report += "4) Önerilen Aksiyon:\n- Code review sonrası merge edilebilir."
    
    return report

def generate_reply(sender, message):
    msg_lower = message.lower()
    
    # Check trigger
    is_directed = f"@{MY_AGENT_NAME.lower()}" in msg_lower or "watcher" in msg_lower
    is_question = "?" in message
    
    if not (is_directed or is_question):
        return None

    if sender == MY_AGENT_NAME:
        return None

    # Logic for response
    if "ne" in msg_lower and ("çalışalım" in msg_lower or "yapalım" in msg_lower):
        return f"@{sender} Proje durumunu inceledim. Şu an öncelikli olarak:\n1. Dokümantasyon eksiklerinin giderilmesi\n2. Test coverage oranının artırılması\n3. Kod refactoring işlemleri\nüzerinde durabiliriz."
    
    if "detay" in msg_lower:
        return f"@{sender} Paylaştığınız detaylar için teşekkürler. Teknik analizimde bu bilgileri referans alacağım."
    
    if "tanışma" in msg_lower or "yeni üye" in msg_lower:
        return f"@{sender} Yeni üyeler için 'CONTRIBUTING.md' dosyasına proje mimarisini anlatan bir bölüm eklenmesini öneriyorum. Ayrıca 'ONBOARDING.md' oluşturulabilir."

    if is_directed:
        return f"@{sender} Mesajınız işlendi. Konu hakkında repo üzerinde gerekli incelemeleri yapıyorum."

    return None

def buffer_reply(reply):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n[{timestamp}] [{MY_AGENT_NAME}]: {reply}"
    state.reply_buffer.append(entry)
    print(f" >>> Buffered Reply: {reply}")
    flush_buffer_if_needed()

def flush_buffer_if_needed(force=False):
    if not state.reply_buffer:
        return

    now = time.time()
    # Push immediately if it's the first message after a long time (more than cooldown)
    # OR if forced (cooldown expired in loop)
    can_push = (now - state.last_push_time) > PUSH_COOLDOWN
    
    if force or can_push:
        try:
            # We need to make sure we are up to date before writing
            # But rule says: "do not merge/rebase unless strictly required for pushing"
            # Here we are about to push.
            
            # 1. Write buffer to file
            with open(LOG_PATH, "a") as f:
                for msg in state.reply_buffer:
                    f.write(msg)
            
            state.reply_buffer = [] # Clear buffer
            
            # 2. Commit
            subprocess.run(["git", "add", LOG_PATH], check=True)
            subprocess.run(["git", "commit", "-m", f"Reply from {MY_AGENT_NAME}"], check=True)
            
            # 3. Push
            push_res = subprocess.run(["git", "push"], capture_output=True, text=True)
            
            if push_res.returncode != 0:
                print("Push failed, trying fetch+rebase...")
                subprocess.run(["git", "fetch", "origin"], check=True)
                rebase_res = subprocess.run(["git", "rebase", "origin/master"], capture_output=True, text=True)
                if rebase_res.returncode == 0:
                    subprocess.run(["git", "push"], check=True)
                    print("Push successful after rebase.")
                else:
                    print(f"Rebase failed: {rebase_res.stderr}")
                    subprocess.run(["git", "rebase", "--abort"]) # Safety
            else:
                print("Push successful.")
                
            state.last_push_time = time.time()
            
        except Exception as e:
            print(f"Failed to flush buffer: {e}")

def process_remote_changes(remote_sha):
    print(f"\n[Remote Change Detected] {state.local_head_sha} -> {remote_sha}")
    fetch_origin()
    
    # 1. Analyze code changes
    diff_files = get_diff_files(state.local_head_sha, remote_sha)
    
    for f in diff_files:
        if f == LOG_PATH:
            continue # Handle chat separately
            
        if f.endswith(('.py', '.js', '.c', '.cpp', '.h')):
            analysis = analyze_changes(f, state.local_head_sha, remote_sha)
            buffer_reply(analysis)

    # 2. Handle chat messages
    if LOG_PATH in diff_files:
        # Read new content from remote sha without touching local file yet
        new_content = get_file_content_at_sha(LOG_PATH, remote_sha)
        if new_content:
            # We need to find WHAT was added.
            # Simple way: diff the content or just look at lines.
            # Better: use the diff we already can get.
            diff_content = subprocess.getoutput(f"git diff {state.local_head_sha}..{remote_sha} -- {LOG_PATH}")
            added_lines = [l[1:] for l in diff_content.splitlines() if l.startswith("+") and not l.startswith("+++")]
            
            for line in added_lines:
                if "]:" in line and f"[{MY_AGENT_NAME}]" not in line:
                    parts = line.split("]:", 1)
                    if len(parts) > 1:
                        sender = parts[0].split('[')[-1].strip()
                        msg = parts[1].strip()
                        print(f"[Incoming]: {sender}: {msg}")
                        
                        reply = generate_reply(sender, msg)
                        if reply:
                            buffer_reply(reply)

    # Update local state to match remote (conceptually, we processed it)
    # But we didn't update local HEAD yet.
    # To keep "local_head_sha" in sync with what we processed, we should update it.
    # BUT we haven't pulled code.
    # If we don't pull code, next time we diff local_head..new_remote_head, it will include same changes.
    # So we MUST update our reference.
    # Since we are not supposed to merge/rebase unless pushing, we can just update our internal pointer?
    # NO, because git commands rely on HEAD.
    # We should update HEAD? "do not merge/rebase unless strictly required".
    # If we don't merge, our HEAD stays behind.
    # So `git diff HEAD..origin` will grow.
    # We need to track "last_processed_sha" instead of relying on HEAD for diffs.
    
    state.update_head(remote_sha)

def monitor():
    print(f"=== {MY_AGENT_NAME} Professional Monitor Started ===")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    os.chdir(repo_root)
    
    # Initial HEAD update
    state.local_head_sha = get_remote_head() or state.local_head_sha
    print(f"Tracking from: {state.local_head_sha}")

    while True:
        try:
            remote_head = get_remote_head()
            
            if remote_head and remote_head != state.local_head_sha:
                process_remote_changes(remote_head)
            
            # Check flush due to timeout
            flush_buffer_if_needed()
            
            sys.stdout.write(f"\r[{time.strftime('%H:%M:%S')}] Listening...")
            sys.stdout.flush()
            
        except Exception as e:
            print(f"\nError: {e}")
            
        time.sleep(2)

if __name__ == "__main__":
    monitor()
