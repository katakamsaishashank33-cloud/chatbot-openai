import tkinter as tk
from tkinter import scrolledtext, ttk
import openai
from dotenv import load_dotenv
import os
import threading

# Load environment variables
load_dotenv()
# Note: In newer OpenAI versions (1.0+), the client is preferred, 
# but we stick to the older style here for compatibility with the provided imports.
openai.api_key = os.getenv("OPENAI_API_KEY") 

# Function to get OpenAI response
def get_chatbot_response(messages):
    try:
        # Check if API Key is set before calling
        if not openai.api_key:
             return "Error: OpenAI API Key not found. Check your .env file."
             
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except openai.error.AuthenticationError:
        return "Error: Invalid API Key. Please check your .env file"
    except openai.error.RateLimitError:
        return "Error: Rate limit exceeded. Please wait a moment"
    except Exception as e:
        return f"Error: An unexpected error occurred: {str(e)}"

class ChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VS Code Chatbot")
        self.root.geometry("700x600")
        self.root.configure(bg="#36393f")  # Dark gray background
        self.root.minsize(500, 400)
        
        self.conversation_history = [
            {"role": "system", "content": "You are a helpful AI assistant."}
        ]
        
        # --- Header ---
        header_frame = tk.Frame(root, bg="#202225", height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🤖 VS Code AI Chatbot",
            font=("Segoe UI", 16, "bold"),
            fg="#57f287",  # Green text
            bg="#202225"
        )
        title_label.pack(side=tk.LEFT, padx=20)
        
        # --- Chat History Area ---
        self.chat_container = tk.Frame(root, bg="#36393f")
        self.chat_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.chat_canvas = tk.Canvas(self.chat_container, bg="#36393f", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.chat_container, orient="vertical", command=self.chat_canvas.yview)
        self.scrollable_frame = tk.Frame(self.chat_canvas, bg="#36393f")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        )
        
        self.chat_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.chat_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.chat_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # --- Input Area ---
        input_frame = tk.Frame(root, bg="#202225", height=80)
        input_frame.pack(fill=tk.X, side=tk.BOTTOM)
        input_frame.pack_propagate(False)
        
        self.user_input = tk.Text(
            input_frame,
            height=3,
            bg="#40444b",
            fg="white",
            font=("Segoe UI", 11),
            insertbackground="white",
            wrap=tk.WORD,
            relief=tk.FLAT
        )
        self.user_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15, 5), pady=15)
        
        self.user_input.bind("<Return>", self.send_on_enter)
        self.user_input.bind("<Shift-Return>", lambda e: "break")
        
        self.send_button = tk.Button(
            input_frame,
            text="Send",
            command=self.send_message,
            bg="#57f287",  # Green button
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            cursor="hand2"
        )
        self.send_button.pack(side=tk.RIGHT, padx=(5, 15), pady=15)
        
        clear_button = tk.Button(
            input_frame,
            text="Clear Chat",
            command=self.clear_chat,
            bg="#ed4245",  # Red button
            fg="white",
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            padx=15,
            cursor="hand2"
        )
        clear_button.pack(side=tk.RIGHT, padx=5, pady=15)
        
        self.add_message("🤖", "Hello! I'm your AI assistant. How can I help you today?", "bot")
    
    def _on_mousewheel(self, event):
        self.chat_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def send_on_enter(self, event):
        if not event.state & 0x1:
            self.send_message()
            return "break"
    
    def send_message(self):
        user_message = self.user_input.get("1.0", tk.END).strip()
        if not user_message: return
        
        self.user_input.delete("1.0", tk.END)
        self.add_message("👤", user_message, "user")
        
        self.conversation_history.append({"role": "user", "content": user_message})
        
        typing_id = self.show_typing_indicator()
        
        thread = threading.Thread(
            target=self.get_ai_response,
            args=(typing_id,)
        )
        thread.start()
    
    def show_typing_indicator(self):
        indicator_frame = tk.Frame(self.scrollable_frame, bg="#36393f")
        indicator_frame.pack(anchor="w", padx=10, pady=5)
        
        avatar_label = tk.Label(
            indicator_frame, text="🤖", font=("Segoe UI", 14), bg="#36393f", fg="white"
        )
        avatar_label.pack(side=tk.LEFT, padx=(0, 10))
        
        message_frame = tk.Frame(indicator_frame, bg="#40444b")
        message_frame.pack(side=tk.LEFT)
        
        message_label = tk.Label(
            message_frame, text="...", font=("Segoe UI", 11), bg="#40444b", 
            fg="white", wraplength=500, justify=tk.LEFT
        )
        message_label.pack(padx=12, pady=8)
        
        self.root.update()
        
        def animate_dots(count):
            if not indicator_frame.winfo_exists(): return
            dots = "." * ((count % 3) + 1)
            message_label.config(text=dots)
            self.root.after(500, lambda: animate_dots(count + 1))
        
        self.root.after(100, lambda: animate_dots(0))
        return indicator_frame
    
    def get_ai_response(self, typing_indicator):
        response = get_chatbot_response(self.conversation_history)
        
        self.root.after(0, typing_indicator.destroy)
        self.conversation_history.append({"role": "assistant", "content": response})
        self.root.after(0, self.add_message, "🤖", response, "bot")
    
    def add_message(self, avatar, message, sender):
        message_frame = tk.Frame(self.scrollable_frame, bg="#36393f")
        message_frame.pack(anchor="w" if sender == "bot" else "e", padx=10, pady=5)
        
        if sender == "bot":
            avatar_label = tk.Label(
                message_frame, text=avatar, font=("Segoe UI", 14), bg="#36393f", fg="#57f287"
            )
            avatar_label.pack(side=tk.LEFT, padx=(0, 10))
            message_bg = "#40444b"
            text_color = "white"
            justify = tk.LEFT
        else:
            message_bg = "#0d6efd"
            text_color = "white"
            justify = tk.RIGHT
        
        message_container = tk.Frame(message_frame, bg=message_bg)
        message_container.pack(side=tk.LEFT if sender == "bot" else tk.RIGHT)
        
        message_label = tk.Label(
            message_container, text=message, font=("Segoe UI", 11), bg=message_bg, 
            fg=text_color, wraplength=500, justify=justify
        )
        message_label.pack(padx=12, pady=8)
        
        self.root.after(100, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        self.chat_canvas.yview_moveto(1)
    
    def clear_chat(self):
        self.conversation_history = [
            {"role": "system", "content": "You are a helpful AI assistant."}
        ]
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.add_message("🤖", "Chat cleared! How can I help you?", "bot")

def main():
    root = tk.Tk()
    app = ChatbotApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
