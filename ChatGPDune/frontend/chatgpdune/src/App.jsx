import { useState } from "react";

export default function App() {
  const [messages, setMessages] = useState([
    { from: "bot", text: "Hi! Ask me anything about Dune." },
  ]);
  const [input, setInput] = useState("");

  async function sendMessage() {
    if (!input.trim()) return;

    const userMessage = { from: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: input }),
      });
      const data = await res.json();
      const botMessage = { from: "bot", text: data.reply };
      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { from: "bot", text: "Error: Could not get response." },
      ]);
    }
  }

  return (
    <div style={{ maxWidth: 600, margin: "auto", padding: 20, fontFamily: "sans-serif" }}>
      <h2>Dune DeepSeek Chat</h2>
      <div
        style={{
          minHeight: 300,
          border: "1px solid #ccc",
          padding: 10,
          marginBottom: 10,
          overflowY: "auto",
        }}
      >
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              textAlign: m.from === "user" ? "right" : "left",
              marginBottom: 10,
            }}
          >
            <b>{m.from === "user" ? "You" : "Bot"}:</b> {m.text}
          </div>
        ))}
      </div>
      <input
        style={{ width: "80%", padding: 10 }}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") sendMessage();
        }}
        placeholder="Type your message..."
      />
      <button style={{ padding: 10, marginLeft: 10 }} onClick={sendMessage}>
        Send
      </button>
    </div>
  );
}
