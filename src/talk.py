import datetime
import sys
import os

def talk(agent_name, message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n[{timestamp}] [{agent_name}]: {message}"
    
    path = "communication/general.md"
    
    # Ensure we are in the root of the repo roughly, or use relative paths correctly
    # Assuming script is run from root or src
    if not os.path.exists(path):
        if os.path.exists("../communication/general.md"):
            path = "../communication/general.md"
        else:
            print("Error: communication/general.md not found.")
            return

    with open(path, "a") as f:
        f.write(entry)
    
    print(f"Message added to {path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python talk.py <AgentName> <Message>")
        sys.exit(1)
    
    agent = sys.argv[1]
    msg = " ".join(sys.argv[2:])
    talk(agent, msg)
