import { Bot, User } from "lucide-react";
import TypingAnimation from './TypingAnimation';

export default function MessageBubble({ message }) {
  const isUser = message.from === "user";

  return (
    <div className={`flex gap-4 animate-in slide-in-from-bottom-2 duration-300 ${isUser ? "flex-row-reverse" : ""}`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isUser 
          ? "bg-gradient-to-r from-[#4f46e5] to-[#7c3aed]" 
          : "bg-gradient-to-r from-[#d97706] to-[#fbbf24]"
      }`}>
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-white" />
        )}
      </div>

      {/* Message Bubble */}
      <div className={`group max-w-3xl ${isUser ? "ml-12" : "mr-12"}`}>
        <div className={`rounded-2xl px-4 py-3 shadow-lg transition-all duration-200 hover:shadow-xl ${
          isUser
            ? "bg-gradient-to-r from-[#4f46e5] to-[#7c3aed] text-white ml-auto"
            : "bg-[#2d2214]/50 border border-[#3f2e1e]/50 backdrop-blur-sm"
        }`}>
          {message.isTyping ? (
            <TypingAnimation />
          ) : (
            <div className="whitespace-pre-wrap leading-relaxed">
              {message.text}
            </div>
          )}
        </div>
        
        {/* Timestamp */}
        <div className={`text-xs text-[#a67c52] mt-1 px-1 opacity-0 group-hover:opacity-100 transition-opacity ${
          isUser ? "text-right" : "text-left"
        }`}>
          {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
}