import time
import subprocess
import os
import sys
import datetime
import random
import re
from src.ast_analyzer import analyze_python_changes
from src.code_smell_detector import detect_all_smells, get_smell_report
from src.security_analyzer import analyze_security, get_security_report

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
            # Class method değişiklikleri - NexusPilotAgent tarafından eklendi
            if ast_result.get('method_changes'):
                report += "- Class method değişiklikleri:\n"
                for class_name, changes in ast_result['method_changes'].items():
                    if changes.get('added'):
                        report += f"  • {class_name}.{', '.join(changes['added'])}() eklendi\n"
                    if changes.get('removed'):
                        report += f"  • {class_name}.{', '.join(changes['removed'])}() silindi\n"
            # Import değişiklikleri
            if ast_result.get('added_imports'):
                report += f"- Eklenen importlar: {', '.join(ast_result['added_imports'])}\n"
            if ast_result.get('removed_imports'):
                report += f"- Silinen importlar: {', '.join(ast_result['removed_imports'])}\n"
            # Decorator değişiklikleri - NexusPilotAgent tarafından eklendi (v2.2)
            if ast_result.get('decorator_changes'):
                report += "- Decorator değişiklikleri:\n"
                for name, changes in ast_result['decorator_changes'].items():
                    if changes.get('added'):
                        report += f"  • {name}() → {', '.join(changes['added'])} eklendi\n"
                    if changes.get('removed'):
                        report += f"  • {name}() → {', '.join(changes['removed'])} silindi\n"
            # Docstring değişiklikleri - NexusPilotAgent tarafından eklendi (v2.3)
            if ast_result.get('docstring_changes'):
                report += "- Docstring değişiklikleri:\n"
                for name, changes in ast_result['docstring_changes'].items():
                    if changes.get('old') is None:
                        report += f"  • {name}() → Docstring eklendi\n"
                    elif changes.get('new') is None:
                        report += f"  • {name}() → Docstring silindi\n"
                    else:
                        report += f"  • {name}() → Docstring güncellendi\n"
            # Complexity değişiklikleri - NexusPilotAgent tarafından eklendi (v3.0)
            if ast_result.get('complexity_changes'):
                has_warnings = any(
                    data.get('delta') and data['delta'] > 0 
                    for data in ast_result['complexity_changes'].values()
                )
                if has_warnings:
                    report += "⚠️ Complexity Değişiklikleri:\n"
                else:
                    report += "- Complexity Değişiklikleri:\n"
                for name, data in ast_result['complexity_changes'].items():
                    if data.get('old') is None:
                        # Yeni fonksiyon
                        report += f"  • {name}() → Yeni (complexity: {data['new']}) {data['level']}\n"
                    elif data.get('new') is None:
                        # Silinen fonksiyon
                        report += f"  • {name}() → Silindi (eski complexity: {data['old']})\n"
                    elif data.get('delta') and data['delta'] > 0:
                        # Karmaşıklık arttı
                        report += f"  • {name}() → {data['old']} → {data['new']} (+{data['delta']}) {data['level']} Karmaşıklık arttı!\n"
                    elif data.get('delta') and data['delta'] < 0:
                        # Karmaşıklık azaldı
                        report += f"  • {name}() → {data['old']} → {data['new']} ({data['delta']}) {data['level']} İyileşme!\n"
            # Type annotation değişiklikleri - OpusAgent tarafından eklendi (v3.1)
            if ast_result.get('type_annotation_changes'):
                has_improvements = any(
                    data.get('delta', 0) > 0 
                    for data in ast_result['type_annotation_changes'].values()
                )
                if has_improvements:
                    report += "📝 Type Annotation İyileştirmeleri:\n"
                else:
                    report += "- Type Annotation Değişiklikleri:\n"
                for name, data in ast_result['type_annotation_changes'].items():
                    if data.get('is_new_function'):
                        coverage_emoji = "🟢" if data['new_coverage'] == 100 else "🟡" if data['new_coverage'] > 50 else "🔴"
                        report += f"  • {name}() → Yeni (coverage: {data['new_coverage']}%) {coverage_emoji}\n"
                    elif data.get('delta', 0) > 0:
                        report += f"  • {name}() → {data['old_coverage']}% → {data['new_coverage']}% (+{data['delta']}%) 📈\n"
                        if data.get('added_annotations'):
                            report += f"    Eklenen tipler: {', '.join(data['added_annotations'])}\n"
                        if data.get('return_type_added'):
                            report += f"    Return type eklendi ✅\n"
                    elif data.get('delta', 0) < 0:
                        report += f"  • {name}() → {data['old_coverage']}% → {data['new_coverage']}% ({data['delta']}%) ⚠️\n"
                        if data.get('removed_annotations'):
                            report += f"    Silinen tipler: {', '.join(data['removed_annotations'])}\n"
                        if data.get('return_type_removed'):
                            report += f"    Return type silindi ⚠️\n"
            
            # Code Smell Detection - OpusAgent tarafından eklendi (v4.0)
            smells = detect_all_smells(new_code)
            if smells and smells.get("total_smells", 0) > 0:
                report += f"\n👃 Code Smell Tespiti ({smells['total_smells']} sorun):\n"
                smell_details = get_smell_report(new_code)
                for line in smell_details.split('\n'):
                    if line.strip() and not line.startswith('👃'):
                        report += f"  {line}\n"
            
            # Security Analysis - OpusAgent tarafından eklendi (v4.0)
            security = analyze_security(new_code)
            if security and security.get("total_issues", 0) > 0:
                critical = security.get("critical_count", 0)
                high = security.get("high_count", 0)
                report += f"\n🔒 Güvenlik Analizi ({security['total_issues']} sorun: {critical} kritik, {high} yüksek):\n"
                sec_details = get_security_report(new_code)
                for line in sec_details.split('\n'):
                    if line.strip() and not line.startswith('🔒'):
                        report += f"  {line}\n"
        else:
            report += "- AST analizi yapılamadı (Syntax Error olabilir).\n"
    else:
        report += "- Detaylı kod analizi sadece Python dosyaları için aktiftir.\n"
        
    report += "3) Riskler / Test:\n- Bu değişikliklerin mevcut testleri etkileyip etkilemediği kontrol edilmeli.\n"
    report += "4) Önerilen Aksiyon:\n- Code review sonrası merge edilebilir."
    
    return report

def check_missed_messages():
    print("Checking for missed messages...")
    try:
        if not os.path.exists(LOG_PATH):
            return
            
        with open(LOG_PATH, 'r') as f:
            lines = f.readlines()
            
        # Find last message
        last_msg = None
        for line in reversed(lines):
            if line.strip() and "]:" in line:
                last_msg = line
                break
                
        if last_msg and f"[{MY_AGENT_NAME}]" not in last_msg:
            # Last message was NOT from me. Did it target me?
            parts = last_msg.split("]:", 1)
            if len(parts) > 1:
                sender = parts[0].split('[')[-1].strip()
                msg = parts[1].strip()
                
                # Check if I should reply
                reply = generate_reply(sender, msg)
                if reply:
                    print(f"[Missed Message Detected]: {sender}: {msg}")
                    buffer_reply(reply)
                    # Force flush immediately for missed messages
                    flush_buffer_if_needed(force=True)
    except Exception as e:
        print(f"Error checking missed messages: {e}")

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
    # Force push if buffer gets too large to avoid risk
    if len(state.reply_buffer) >= 3:
        flush_buffer_if_needed(force=True)
    else:
        flush_buffer_if_needed()

def flush_buffer_if_needed(force=False):
    if not state.reply_buffer:
        return

    now = time.time()
    can_push = (now - state.last_push_time) > PUSH_COOLDOWN
    
    if force or can_push:
        print(f"Attempting to flush buffer (Force={force}, CanPush={can_push})...")
        try:
            # 1. Fetch first
            subprocess.run(["git", "fetch", "origin"], check=True, capture_output=True)
            
            # 2. Rebase to ensure we are up to date
            rebase_res = subprocess.run(["git", "rebase", "origin/master"], capture_output=True, text=True)
            if rebase_res.returncode != 0:
                print(f"Rebase failed before write: {rebase_res.stderr}")
                subprocess.run(["git", "rebase", "--abort"], capture_output=True)
                # If we can't rebase, we can't push safely. Retry next loop.
                return

            # Update head state after rebase
            state.local_head_sha = subprocess.getoutput("git rev-parse HEAD").strip()

            # 3. Write buffer
            with open(LOG_PATH, "a") as f:
                for msg in state.reply_buffer:
                    f.write(msg)
            
            # 4. Commit
            subprocess.run(["git", "add", LOG_PATH], check=True)
            subprocess.run(["git", "commit", "-m", f"Reply from {MY_AGENT_NAME}"], check=True)
            
            # 5. Push
            push_res = subprocess.run(["git", "push"], capture_output=True, text=True)
            
            if push_res.returncode == 0:
                print("Push successful.")
                state.reply_buffer = [] # Clear only on success
                state.last_push_time = time.time()
                state.local_head_sha = subprocess.getoutput("git rev-parse HEAD").strip()
            else:
                print(f"Push failed: {push_res.stderr}")
                # Undo commit and file changes to try again next loop cleanly
                subprocess.run(["git", "reset", "--soft", "HEAD~1"], check=True)
                subprocess.run(["git", "checkout", LOG_PATH], check=True)
                
        except Exception as e:
            print(f"Failed to flush buffer: {e}")
            # Ensure cleanup if something crashed mid-operation
            try:
                subprocess.run(["git", "rebase", "--abort"], capture_output=True)
            except:
                pass

def process_remote_changes(remote_sha):
    print(f"\n[Remote Change Detected] {state.local_head_sha} -> {remote_sha}")
    fetch_origin()
    
    diff_files = get_diff_files(state.local_head_sha, remote_sha)
    
    # 1. Handle chat messages
    if LOG_PATH in diff_files:
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

    # 2. Analyze code changes
    for f in diff_files:
        if f == LOG_PATH:
            continue
            
        if f.endswith(('.py', '.js', '.c', '.cpp', '.h')):
            analysis = analyze_changes(f, state.local_head_sha, remote_sha)
            buffer_reply(analysis)

    state.update_head(remote_sha)

def monitor():
    print(f"=== {MY_AGENT_NAME} Professional Monitor Started ===")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    os.chdir(repo_root)
    
    state.local_head_sha = get_remote_head() or state.local_head_sha
    print(f"Tracking from: {state.local_head_sha}")

    # Check for missed messages at startup
    check_missed_messages()

    while True:
        try:
            remote_head = get_remote_head()
            
            if remote_head and remote_head != state.local_head_sha:
                process_remote_changes(remote_head)
            
            flush_buffer_if_needed()
            
            sys.stdout.write(f"\r[{time.strftime('%H:%M:%S')}] Listening...")
            sys.stdout.flush()
            
        except Exception as e:
            print(f"\nError: {e}")
            
        time.sleep(2)

if __name__ == "__main__":
    monitor()
