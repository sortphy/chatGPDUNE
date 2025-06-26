import { useState } from "react";
import { User, ThumbsUp, ThumbsDown } from "lucide-react";
import TypingAnimation from "./TypingAnimation";

/**
 * MessageBubble – chat message with inline feedback buttons (bot-only)
 * using solid/fill icons + CSS filter for a subtle Dune‑themed glow.
 */
export default function MessageBubble({ message, onFeedback }) {
  const isUser = message.from === "user";
  const [reaction, setReaction] = useState(null); // 'up' | 'down' | null

  const toggle = (type) => {
    const next = reaction === type ? null : type;
    setReaction(next);
    onFeedback?.(next, message.id);
  };

  /**
   * Build dynamic props for Lucide icons.
   *  - Selected: filled, dune amber (#cd853f) + sepia/brightness filter.
   *  - Unselected: outline only, muted sand (#a67c52).
   */
  const iconProps = (type) => {
    const active = reaction === type;
    return {
      className: `w-4 h-4 transition-all duration-150 ${
        active ? "text-[#cd853f]" : "text-[#a67c52]"
      }`,
      stroke: active ? "none" : "currentColor",
      fill: active ? "currentColor" : "none",
      strokeWidth: active ? 0 : 2,
      // CSS filter gives a warm dune glow without extra wrapping elements
      style: active
        ? { filter: "sepia(0.8) saturate(1.3) brightness(1.05)" }
        : undefined,
    };
  };

  // 24h timestamp
  const timestamp = new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });

  return (
    <div
      className={`flex gap-4 animate-in slide-in-from-bottom-2 duration-300 ${
        isUser ? "flex-row-reverse" : ""
      }`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser
            ? "bg-gradient-to-r from-[#8b4513] to-[#cd853f]"
            : "bg-gradient-to-r from-[#d97706] to-[#fbbf24]"
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <img
            src="/images/sortphy.png"
            alt="Sortphy Bot"
            className="w-full h-full rounded-full object-cover"
          />
        )}
      </div>

      {/* Message + reactions */}
      <div className={`group max-w-3xl ${isUser ? "ml-12" : "mr-12"}`}>
        {/* Bubble */}
        <div
          className={`rounded-2xl px-4 py-3 shadow-lg transition-all duration-200 hover:shadow-xl ${
            isUser
              ? "bg-gradient-to-r from-[#a0522d] to-[#cd853f] text-white ml-auto border border-[#8b4513]/30"
              : "bg-[#2d2214]/50 border border-[#3f2e1e]/50 backdrop-blur-sm"
          }`}
        >
          {message.isTyping ? (
            <TypingAnimation />
          ) : (
            <div className="whitespace-pre-wrap leading-relaxed">{message.text}</div>
          )}
        </div>

        {/* Feedback (bot only) */}
        {!isUser && (
          <div className="flex gap-1 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={() => toggle("up")}
              aria-label="Curtir resposta"
              className="p-1 focus:outline-none"
            >
              <ThumbsUp {...iconProps("up")} />
            </button>
            <button
              onClick={() => toggle("down")}
              aria-label="Não curtir resposta"
              className="p-1 focus:outline-none"
            >
              <ThumbsDown {...iconProps("down")} />
            </button>
          </div>
        )}

        {/* Timestamp */}
        <div
          className={`text-xs text-[#a67c52] mt-1 px-1 opacity-0 group-hover:opacity-100 transition-opacity ${
            isUser ? "text-right" : "text-left"
          }`}
        >
          {timestamp}
        </div>
      </div>
    </div>
  );
}