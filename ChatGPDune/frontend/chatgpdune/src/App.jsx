import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles } from "lucide-react";

import './index.css';

export default function App() {
  const [messages, setMessages] = useState([
    { from: "bot", text: "Welcome to the desert planet! Ask me anything about the Dune universe - from spice mining to sandworms, politics to prophecies." },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  async function sendMessage() {
    if (!input.trim() || isLoading) return;

    const userMessage = { from: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    const typingMessage = { from: "bot", text: "...", isTyping: true };
    setMessages((prev) => [...prev, typingMessage]);

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: input }),
      });
      const data = await res.json();
      
      setMessages((prev) => {
        const withoutTyping = prev.filter(m => !m.isTyping);
        return [...withoutTyping, { from: "bot", text: data.reply }];
      });
    } catch (err) {
      setMessages((prev) => {
        const withoutTyping = prev.filter(m => !m.isTyping);
        return [...withoutTyping, { from: "bot", text: "The spice must flow... but connection failed. Please try again." }];
      });
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#1a120b] via-[#2b1b11] to-[#0a0603] text-[#f5f0e6]">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-[#1a120b]/90 backdrop-blur-md border-b border-[#3f2e1e]/60">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-r from-[#d97706] to-[#fbbf24] rounded-full flex items-center justify-center shadow-lg">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-[#d97706] to-[#fbbf24] bg-clip-text text-transparent">
                Dune DeepSeek
              </h1>
              <p className="text-sm text-[#bfa77a]">Your guide to Arrakis</p>
            </div>
          </div>
        </div>
      </div>

      {/* Messages Container */}
      <div className="max-w-4xl mx-auto px-4 pb-32">
        <div className="space-y-6 py-6">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex gap-4 animate-in slide-in-from-bottom-2 duration-300 ${message.from === "user" ? "flex-row-reverse" : ""}`}
            >
              {/* Avatar */}
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                message.from === "user" 
                  ? "bg-gradient-to-r from-[#4f46e5] to-[#7c3aed]" 
                  : "bg-gradient-to-r from-[#d97706] to-[#fbbf24]"
              }`}>
                {message.from === "user" ? (
                  <User className="w-4 h-4 text-white" />
                ) : (
                  <Bot className="w-4 h-4 text-white" />
                )}
              </div>

              {/* Message Bubble */}
              <div className={`group max-w-3xl ${message.from === "user" ? "ml-12" : "mr-12"}`}>
                <div className={`rounded-2xl px-4 py-3 shadow-lg transition-all duration-200 hover:shadow-xl ${
                  message.from === "user"
                    ? "bg-gradient-to-r from-[#4f46e5] to-[#7c3aed] text-white ml-auto"
                    : "bg-[#2d2214]/50 border border-[#3f2e1e]/50 backdrop-blur-sm"
                }`}>
                  {message.isTyping ? (
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-[#d97706] rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                      <div className="w-2 h-2 bg-[#d97706] rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                      <div className="w-2 h-2 bg-[#d97706] rounded-full animate-bounce"></div>
                    </div>
                  ) : (
                    <div className="whitespace-pre-wrap leading-relaxed">
                      {message.text}
                    </div>
                  )}
                </div>
                <div className={`text-xs text-[#a67c52] mt-1 px-1 opacity-0 group-hover:opacity-100 transition-opacity ${
                  message.from === "user" ? "text-right" : "text-left"
                }`}>
                  {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-[#1a120b] via-[#1a120b]/95 to-transparent pt-6 pb-6">
        <div className="max-w-4xl mx-auto px-4">
          <div className="relative bg-[#2b1b11]/60 backdrop-blur-sm rounded-2xl border border-[#3f2e1e]/50 shadow-2xl transition-all duration-200 focus-within:border-[#d97706]/60 focus-within:shadow-[#d97706]/10">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about the spice, the desert, or the prophecy..."
              className="w-full bg-transparent text-white placeholder-[#a67c52] px-6 py-4 pr-16 resize-none focus:outline-none min-h-[60px] max-h-32"
              disabled={isLoading}
              rows={1}
              style={{ 
                resize: 'none',
                scrollbarWidth: 'thin',
                scrollbarColor: '#3f2e1e transparent'
              }}
            />

            {/* Send Button */}
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              className="absolute right-3 bottom-3 w-10 h-10 bg-gradient-to-r from-[#d97706] to-[#fbbf24] rounded-xl flex items-center justify-center text-white shadow-lg transition-all duration-200 hover:shadow-xl hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>

          {/* Footer */}
          <div className="text-center text-xs text-[#a67c52] mt-3">
            Powered by the Sortphy | Using Ollama & DeepSeek R1 • Às vezes demora, depende da máquina
          </div>
        </div>
      </div>
    </div>
  );
}
