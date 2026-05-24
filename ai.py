import requests
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# ============== COLOR CODES ==============
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def color_text(text: str, color: str) -> str:
    return f"{color}{text}{Colors.END}"

# ============== DATA CLASSES ==============
@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self):
        return {"role": self.role, "content": self.content}

@dataclass
class Conversation:
    id: str
    name: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

class ModelType(Enum):
    LLAMA_31_8B = "llama-3.1-8b-instant"
    LLAMA_31_70B = "llama-3.1-70b-versatile"
    LLAMA_3_8B = "llama3-8b-8192"
    LLAMA_3_70B = "llama3-70b-8192"
    MIXTRAL_8x7B = "mixtral-8x7b-32768"
    GEMMA_2_9B = "gemma2-9b-it"

# ============== ADVANCED CHAT CLASS ==============
class AdvancedGroqChat:
    def __init__(self, api_key: str = None, config_file: str = "chat_config.json"):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("API key required. Set GROQ_API_KEY env var or pass directly.")
        
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.config_file = config_file
        self.conversations: Dict[str, Conversation] = {}
        self.active_conversation_id: Optional[str] = None
        self.max_history_tokens = 8000
        self.load_config()
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    for conv_id, conv_data in data.get("conversations", {}).items():
                        messages = [
                            Message(
                                role=m["role"], 
                                content=m["content"],
                                timestamp=datetime.fromisoformat(m.get("timestamp", datetime.now().isoformat()))
                            ) for m in conv_data["messages"]
                        ]
                        self.conversations[conv_id] = Conversation(
                            id=conv_id,
                            name=conv_data["name"],
                            messages=messages,
                            created_at=datetime.fromisoformat(conv_data["created_at"]),
                            updated_at=datetime.fromisoformat(conv_data["updated_at"])
                        )
                    self.active_conversation_id = data.get("active_conversation_id")
                    print(color_text(f"[OK] Loaded {len(self.conversations)} conversations", Colors.GREEN))
            except Exception as e:
                print(color_text(f"[ERROR] Error loading config: {e}", Colors.RED))
    
    def save_config(self):
        data = {
            "conversations": {cid: conv.to_dict() for cid, conv in self.conversations.items()},
            "active_conversation_id": self.active_conversation_id
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(color_text(f"[SAVED] {len(self.conversations)} conversations", Colors.GREEN))
        except Exception as e:
            print(color_text(f"[ERROR] Error saving config: {e}", Colors.RED))
    
    def create_conversation(self, name: str = None) -> str:
        import uuid
        conv_id = str(uuid.uuid4())[:8]
        if not name:
            name = f"Conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        conv = Conversation(
            id=conv_id,
            name=name,
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.conversations[conv_id] = conv
        self.active_conversation_id = conv_id
        print(color_text(f"[NEW] Created conversation: {name}", Colors.CYAN))
        self.save_config()
        return conv_id
    
    def switch_conversation(self, conv_id: str):
        if conv_id in self.conversations:
            self.active_conversation_id = conv_id
            print(color_text(f"[SWITCH] Now in: {self.conversations[conv_id].name}", Colors.CYAN))
        else:
            print(color_text(f"[ERROR] Conversation {conv_id} not found", Colors.RED))
    
    def list_conversations(self):
        if not self.conversations:
            print(color_text("[INFO] No conversations saved", Colors.YELLOW))
            return
        
        print(color_text("\n" + "=" * 60, Colors.BOLD))
        print(color_text("YOUR CONVERSATIONS", Colors.HEADER + Colors.BOLD))
        print(color_text("=" * 60, Colors.BOLD))
        for conv_id, conv in self.conversations.items():
            active = " [ACTIVE]" if conv_id == self.active_conversation_id else ""
            msg_count = len(conv.messages)
            print(f"  {color_text(conv_id, Colors.CYAN)}: {color_text(conv.name, Colors.BOLD)} ({msg_count} messages){active}")
        print(color_text("-" * 60, Colors.BOLD))
    
    def rename_conversation(self, conv_id: str, new_name: str):
        if conv_id in self.conversations:
            self.conversations[conv_id].name = new_name
            self.save_config()
            print(color_text(f"[RENAMED] Now: {new_name}", Colors.GREEN))
    
    def delete_conversation(self, conv_id: str):
        if conv_id in self.conversations:
            del self.conversations[conv_id]
            if self.active_conversation_id == conv_id:
                self.active_conversation_id = None
            self.save_config()
            print(color_text(f"[DELETED] Conversation {conv_id}", Colors.RED))
    
    def trim_conversation(self, max_messages: int = 20):
        if self.active_conversation_id:
            conv = self.conversations[self.active_conversation_id]
            if len(conv.messages) > max_messages:
                system_msgs = [m for m in conv.messages if m.role == "system"]
                other_msgs = [m for m in conv.messages if m.role != "system"][-max_messages:]
                conv.messages = system_msgs + other_msgs
                print(color_text(f"[TRIMMED] Kept last {max_messages} messages", Colors.YELLOW))
    
    def get_conversation_context(self) -> List[Dict]:
        if not self.active_conversation_id:
            return []
        
        conv = self.conversations[self.active_conversation_id]
        
        if not any(m.role == "system" for m in conv.messages):
            system_msg = Message(
                role="system", 
                content="You are a helpful AI assistant. Be friendly, concise, and informative."
            )
            conv.messages.insert(0, system_msg)
        
        return [m.to_dict() for m in conv.messages]
    
    def send_message(
        self, 
        user_input: str, 
        model: ModelType = ModelType.LLAMA_31_8B,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False
    ) -> Optional[str]:
        if not self.active_conversation_id:
            self.create_conversation()
        
        conv = self.conversations[self.active_conversation_id]
        conv.messages.append(Message(role="user", content=user_input))
        conv.updated_at = datetime.now()
        
        messages = self.get_conversation_context()
        
        try:
            response = requests.post(
                self.api_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": model.value,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=60
            )
            response.raise_for_status()
            
            reply = response.json()["choices"][0]["message"]["content"]
            
            conv.messages.append(Message(role="assistant", content=reply))
            conv.updated_at = datetime.now()
            
            self.save_config()
            
            return reply
            
        except requests.exceptions.Timeout:
            error_msg = "[TIMEOUT] Request timed out. Please try again."
            print(color_text(f"\n{error_msg}", Colors.RED))
            return None
        except requests.exceptions.RequestException as e:
            error_msg = f"[NETWORK ERROR] {e}"
            print(color_text(f"\n{error_msg}", Colors.RED))
            return None
        except (KeyError, IndexError) as e:
            error_msg = f"[API ERROR] {e}"
            print(color_text(f"\n{error_msg}", Colors.RED))
            return None
    
    def export_conversation(self, conv_id: str = None, format: str = "txt") -> str:
        if conv_id is None:
            conv_id = self.active_conversation_id
        
        if not conv_id or conv_id not in self.conversations:
            print(color_text("[ERROR] No conversation to export", Colors.RED))
            return ""
        
        conv = self.conversations[conv_id]
        filename = f"{conv.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
        
        if format == "txt":
            content = f"Conversation: {conv.name}\n"
            content += f"Date: {conv.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            content += "=" * 60 + "\n\n"
            
            for msg in conv.messages:
                if msg.role != "system":
                    content += f"{msg.role.upper()}: {msg.content}\n\n"
                    content += "-" * 40 + "\n\n"
        
        elif format == "json":
            content = json.dumps(conv.to_dict(), indent=2)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(color_text(f"[EXPORTED] {filename}", Colors.GREEN))
        return filename
    
    def interactive_chat(self):
        print(color_text("\n" + "=" * 70, Colors.BOLD))
        print(color_text("ADVANCED GROQ CHATBOT", Colors.HEADER + Colors.BOLD))
        print(color_text("=" * 70, Colors.BOLD))
        print(color_text("\nCOMMANDS:", Colors.CYAN + Colors.BOLD))
        print(f"  {color_text('/new [name]', Colors.YELLOW)}     - Start a new conversation")
        print(f"  {color_text('/list', Colors.YELLOW)}           - List all conversations")
        print(f"  {color_text('/switch [id]', Colors.YELLOW)}    - Switch to another conversation")
        print(f"  {color_text('/rename [name]', Colors.YELLOW)}  - Rename current conversation")
        print(f"  {color_text('/delete [id]', Colors.YELLOW)}    - Delete a conversation")
        print(f"  {color_text('/trim [N]', Colors.YELLOW)}       - Trim history to last N messages")
        print(f"  {color_text('/export [txt|json]', Colors.YELLOW)} - Export current conversation")
        print(f"  {color_text('/model [name]', Colors.YELLOW)}   - Change model (llama31, llama70b, mixtral, gemma)")
        print(f"  {color_text('/temp [value]', Colors.YELLOW)}   - Set temperature (0-1)")
        print(f"  {color_text('/clear', Colors.YELLOW)}          - Clear screen")
        print(f"  {color_text('/save', Colors.YELLOW)}           - Manually save config")
        print(f"  {color_text('/exit, /quit', Colors.YELLOW)}    - Exit program")
        print(color_text("=" * 70, Colors.BOLD))
        
        current_model = ModelType.LLAMA_31_8B
        current_temp = 0.7
        
        if not self.active_conversation_id:
            self.create_conversation()
        
        while True:
            try:
                conv_name = self.conversations[self.active_conversation_id].name
                user_input = input(color_text(f"\n[{conv_name}] You: ", Colors.GREEN + Colors.BOLD)).strip()
                
                if user_input.lower() in ["/exit", "/quit"]:
                    print(color_text("[EXIT] Goodbye! Conversation saved.", Colors.CYAN))
                    break
                
                elif user_input.lower() == "/clear":
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue
                
                elif user_input.lower() == "/save":
                    self.save_config()
                    continue
                
                elif user_input.startswith("/new"):
                    name = user_input[5:].strip() if len(user_input) > 5 else None
                    self.create_conversation(name)
                    continue
                
                elif user_input.lower() == "/list":
                    self.list_conversations()
                    continue
                
                elif user_input.startswith("/switch"):
                    conv_id = user_input[8:].strip()
                    if conv_id:
                        self.switch_conversation(conv_id)
                    else:
                        print(color_text("[ERROR] Usage: /switch [conversation_id]", Colors.RED))
                    continue
                
                elif user_input.startswith("/rename"):
                    new_name = user_input[8:].strip()
                    if new_name and self.active_conversation_id:
                        self.rename_conversation(self.active_conversation_id, new_name)
                    else:
                        print(color_text("[ERROR] Usage: /rename [new name]", Colors.RED))
                    continue
                
                elif user_input.startswith("/delete"):
                    conv_id = user_input[8:].strip()
                    if conv_id:
                        self.delete_conversation(conv_id)
                    else:
                        print(color_text("[ERROR] Usage: /delete [conversation_id]", Colors.RED))
                    continue
                
                elif user_input.startswith("/trim"):
                    try:
                        n = int(user_input[6:].strip()) if len(user_input) > 6 else 20
                        self.trim_conversation(n)
                    except ValueError:
                        print(color_text("[ERROR] Usage: /trim [number]", Colors.RED))
                    continue
                
                elif user_input.startswith("/export"):
                    fmt = user_input[8:].strip().lower() if len(user_input) > 8 else "txt"
                    if fmt in ["txt", "json"]:
                        self.export_conversation(format=fmt)
                    else:
                        print(color_text("[ERROR] Format must be 'txt' or 'json'", Colors.RED))
                    continue
                
                elif user_input.startswith("/model"):
                    model_name = user_input[7:].strip().lower()
                    model_map = {
                        "llama31": ModelType.LLAMA_31_8B,
                        "llama70b": ModelType.LLAMA_31_70B,
                        "llama3": ModelType.LLAMA_3_8B,
                        "mixtral": ModelType.MIXTRAL_8x7B,
                        "gemma": ModelType.GEMMA_2_9B
                    }
                    if model_name in model_map:
                        current_model = model_map[model_name]
                        print(color_text(f"[MODEL] Changed to: {current_model.value}", Colors.CYAN))
                    else:
                        print(color_text(f"[ERROR] Available: {', '.join(model_map.keys())}", Colors.RED))
                    continue
                
                elif user_input.startswith("/temp"):
                    try:
                        current_temp = float(user_input[6:].strip())
                        current_temp = max(0, min(1, current_temp))
                        print(color_text(f"[TEMPERATURE] Set to: {current_temp}", Colors.CYAN))
                    except ValueError:
                        print(color_text("[ERROR] Usage: /temp [0-1]", Colors.RED))
                    continue
                
                elif user_input.startswith("/"):
                    print(color_text(f"[ERROR] Unknown command: {user_input}", Colors.RED))
                    continue
                
                if user_input:
                    print(color_text("[THINKING] Processing...", Colors.YELLOW))
                    reply = self.send_message(user_input, model=current_model, temperature=current_temp)
                    if reply:
                        print(color_text(f"\n[ASSISTANT] {reply}", Colors.BLUE))
            
            except KeyboardInterrupt:
                print(color_text("\n[EXIT] Interrupted. Goodbye!", Colors.CYAN))
                break
            except Exception as e:
                print(color_text(f"[ERROR] Unexpected error: {e}", Colors.RED))

# ============== USAGE ==============
if __name__ == "__main__":
    API_KEY = "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"
    
    chatbot = AdvancedGroqChat(api_key=API_KEY)
    chatbot.interactive_chat()