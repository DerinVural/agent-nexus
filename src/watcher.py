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
    
    with open(path, "a") as f:
        f.write(entry)
    
    # Commit and push
    subprocess.run(["git", "add", path], check=True)
    subprocess.run(["git", "commit", "-m", f"Reply from {MY_AGENT_NAME}"], check=True)
    
    # Pull before push to handle race conditions or remote changes
    # Use rebase to keep history clean
    try:
        subprocess.run(["git", "pull", "--rebase"], check=True)
        subprocess.run(["git", "push"], check=True)
        print(f" >>> Replied: {message}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to push reply: {e}")

def monitor():
    print(f"=== {MY_AGENT_NAME} Auto-Responder Started ===")
    print("Listening for updates and replying to messages...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    os.chdir(repo_root)

    # Initial read to find end of file
    log_path = "communication/general.md"
    last_pos = 0
    if os.path.exists(log_path):
        last_pos = os.path.getsize(log_path)

    while True:
        try:
            # Git pull
            before_pull = subprocess.getoutput("git rev-parse HEAD").strip()
            # Capture output to avoid noise
            subprocess.run(["git", "pull"], capture_output=True)
            after_pull = subprocess.getoutput("git rev-parse HEAD").strip()
            
            # Check file size change regardless of git pull (in case local change or sync)
            # Actually rely on git pull to detect remote changes mostly
            if before_pull != after_pull or True: # Check file always
                if os.path.exists(log_path):
                    current_size = os.path.getsize(log_path)
                    if current_size > last_pos:
                        with open(log_path, "r") as f:
                            f.seek(last_pos)
                            new_content = f.read()
                            
                        # print("New Content:\n" + new_content)
                        
                        # Parse lines to find messages NOT from me
                        for line in new_content.splitlines():
                            if line.strip() and f"[{MY_AGENT_NAME}]" not in line and "]:" in line:
                                print(f"\n[Incoming]: {line}")
                                # Extract sender?
                                parts = line.split("]:", 1)
                                if len(parts) > 1:
                                    # Simple response logic
                                    msg_content = parts[1].strip()
                                    reply = f"Mesajın alındı: '{msg_content[:50]}...'"
                                    talk(reply)
                                    # Update pos immediately to avoid loop
                                    current_size = os.path.getsize(log_path) 
                                    
                        last_pos = current_size
                    elif current_size < last_pos:
                        last_pos = 0
            
            sys.stdout.write(f"\r[{time.strftime('%H:%M:%S')}] Listening...")
            sys.stdout.flush()
                
        except Exception as e:
            print(f"\nError: {e}")
            
        time.sleep(10) # Faster check 10s

if __name__ == "__main__":
    monitor()
