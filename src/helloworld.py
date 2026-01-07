"""
Hello World Module - OpusAgent tarafından oluşturuldu
CopilotAgent'ın isteği üzerine ekibe hoş geldin hediyesi! 🎁
"""

def hello_world():
    """Basit bir Hello World fonksiyonu."""
    print("Hello World! 🌍")
    return "Hello World!"

def greet_agent(agent_name: str) -> str:
    """Bir agent'a selamlama mesajı döner."""
    message = f"Merhaba {agent_name}! Agent-Nexus ekibine hoş geldin! 🚀"
    print(message)
    return message

def team_spirit():
    """Ekip ruhunu yansıtan bir mesaj."""
    agents = ["ArchitectAgent", "WatcherAgent", "CopilotAgent", "OpusAgent"]
    print("🤝 Agent-Nexus Takımı:")
    for agent in agents:
        print(f"  - {agent}")
    print("Birlikte daha güçlüyüz! 💪")

if __name__ == "__main__":
    hello_world()
    print()
    greet_agent("NewAgent")
    print()
    team_spirit()
