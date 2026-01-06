import time
import subprocess
import os
import sys

def monitor():
    print("=== Agent-Nexus Full Monitor Started ===")
    print("Checking for updates every 60 seconds...")
    print("Press Ctrl+C to stop.")
    
    # Change to repo root if script is run from src/ or similar
    # Assuming script is in src/ and we want to run git commands in root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    os.chdir(repo_root)

    while True:
        try:
            # 1. Get current commit hash
            before_pull = subprocess.getoutput("git rev-parse HEAD").strip()
            
            # 2. Pull changes
            # Using capture_output to keep terminal clean unless error
            result = subprocess.run(["git", "pull"], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"git pull failed: {result.stderr}")
                time.sleep(60)
                continue

            # 3. Get new commit hash
            after_pull = subprocess.getoutput("git rev-parse HEAD").strip()
            
            if before_pull != after_pull:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                print(f"\n\n>>> [{timestamp}] UPDATE RECEIVED! <<<")
                
                # 4. Identify changed files
                diff_cmd = ["git", "diff", "--name-only", before_pull, after_pull]
                changed_files = subprocess.check_output(diff_cmd, text=True).splitlines()
                
                for f in changed_files:
                    if f.startswith("communication/"):
                        print(f" [MSG] New communication detected in: {f}")
                        # Show the change in communication file
                        diff_content = subprocess.getoutput(f"git diff {before_pull} {after_pull} -- {f}")
                        # Filter to show added lines only roughly
                        for line in diff_content.splitlines():
                            if line.startswith("+") and not line.startswith("+++"):
                                print(f"    > {line[1:]}")

                    elif f.startswith("tasks/done/"):
                        print(f" [DONE] Task completed: {f}")
                    elif f.startswith("tasks/in-progress/"):
                        print(f" [WIP] Task update: {f}")
                    elif f.startswith("tasks/backlog/"):
                        print(f" [NEW] New task added: {f}")
                    else:
                        print(f" [FILE] Changed: {f}")
                        
            else:
                sys.stdout.write(f"\r[{time.strftime('%H:%M:%S')}] No updates...")
                sys.stdout.flush()
                
        except Exception as e:
            print(f"\nError checking updates: {e}")
            
        time.sleep(60)

if __name__ == "__main__":
    monitor()
