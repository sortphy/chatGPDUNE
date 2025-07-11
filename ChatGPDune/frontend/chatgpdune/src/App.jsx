import { useState, useRef, useEffect } from "react";
import Header from './components/Header';
import MessageList from './components/MessageList';
import InputArea from './components/InputArea';
import './index.css';

export default function App() {
  const [messages, setMessages] = useState([
    { from: "bot", text: "Welcome to the desert planet! Ask me anything about the Dune universe - from spice mining to sandworms, politics to prophecies.", ragUsed: false },
  ]);
  const [useRag, setUseRag] = useState(true); // rag stuff
  const [selectedModel, setSelectedModel] = useState("deepseek-r1"); // model selection
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
        body: JSON.stringify({ 
          text: input, 
          use_rag: useRag,
          model: selectedModel // Send selected model to backend
        }),
      });
      const data = await res.json();
      
      setMessages((prev) => {
        const withoutTyping = prev.filter(m => !m.isTyping);
        return [...withoutTyping, { 
          from: "bot", 
          text: data.reply,
          ragUsed: data.rag_used || false,
          sources: data.sources || [], // Use the new detailed sources format
          sourcesLegacy: data.top_sources || [], // Keep old format for backwards compatibility
          model: data.model_used || selectedModel // Store which model was used
        }];
      });
    } catch (err) {
      setMessages((prev) => {
        const withoutTyping = prev.filter(m => !m.isTyping);
        return [...withoutTyping, { 
          from: "bot", 
          text: "The spice must flow... but connection failed. Please try again.",
          ragUsed: false,
          model: selectedModel
        }];
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
      <Header />
      
      <MessageList 
        messages={messages} 
        messagesEndRef={messagesEndRef}
      />
      <InputArea
        input={input}
        setInput={setInput}
        isLoading={isLoading}
        onSendMessage={sendMessage}
        onKeyPress={handleKeyPress}
        inputRef={inputRef}
        useRag={useRag}
        setUseRag={setUseRag}
        selectedModel={selectedModel}
        setSelectedModel={setSelectedModel}
      />
    </div>
  );
}