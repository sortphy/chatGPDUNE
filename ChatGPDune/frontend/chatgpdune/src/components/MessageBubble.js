import { useState } from "react";
import { User, ThumbsUp, ThumbsDown, Database, ExternalLink } from "lucide-react";
import SourcesPopover from "./SourcesPopover";
import TypingAnimation from "./TypingAnimation";
import ReactMarkdown from 'react-markdown';

/**
 * MessageBubble – chat message with inline feedback buttons (bot-only)
 * using solid/fill icons + CSS filter for a subtle Dune‑themed glow.
 * Now includes RAG indicator for bot messages and full markdown support via react-markdown.
 */
export default function MessageBubble({ message, onFeedback }) {
  const isUser = message.from === "user";
  const [reaction, setReaction] = useState(null); // 'up' | 'down' | null
  const [showSources, setShowSources] = useState(false);

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

  // Custom components for ReactMarkdown to match your Dune theme
  const markdownComponents = {
    // Headers
    h1: ({ children }) => (
      <h1 className="text-2xl font-bold text-[#cd853f] mb-3 mt-2">{children}</h1>
    ),
    h2: ({ children }) => (
      <h2 className="text-xl font-bold text-[#cd853f] mb-2 mt-2">{children}</h2>
    ),
    h3: ({ children }) => (
      <h3 className="text-lg font-semibold text-[#cd853f] mb-2 mt-1">{children}</h3>
    ),
    h4: ({ children }) => (
      <h4 className="text-base font-semibold text-[#cd853f] mb-1 mt-1">{children}</h4>
    ),
    h5: ({ children }) => (
      <h5 className="text-sm font-semibold text-[#cd853f] mb-1 mt-1">{children}</h5>
    ),
    h6: ({ children }) => (
      <h6 className="text-xs font-semibold text-[#cd853f] mb-1 mt-1">{children}</h6>
    ),
    
    // Paragraphs
    p: ({ children }) => (
      <p className="mb-2 last:mb-0">{children}</p>
    ),
    
    // Lists
    ul: ({ children }) => (
      <ul className="list-disc list-inside mb-2 space-y-1 text-[#e5ddd5]">{children}</ul>
    ),
    ol: ({ children }) => (
      <ol className="list-decimal list-inside mb-2 space-y-1 text-[#e5ddd5]">{children}</ol>
    ),
    li: ({ children }) => (
      <li className="text-[#e5ddd5]">{children}</li>
    ),
    
    // Inline code
    code: ({ inline, children }) => {
      if (inline) {
        return (
          <code className="bg-[#3f2e1e]/50 text-[#cd853f] px-1 py-0.5 rounded text-sm font-mono">
            {children}
          </code>
        );
      }
      // Block code (fallback, though react-markdown usually uses pre > code)
      return (
        <code className="block bg-[#3f2e1e]/70 text-[#cd853f] p-3 rounded-lg text-sm font-mono overflow-x-auto">
          {children}
        </code>
      );
    },
    
    // Code blocks
    pre: ({ children }) => (
      <pre className="bg-[#3f2e1e]/70 text-[#cd853f] p-3 rounded-lg text-sm font-mono overflow-x-auto mb-2 border border-[#8b4513]/30">
        {children}
      </pre>
    ),
    
    // Links
    a: ({ href, children }) => (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-[#cd853f] hover:text-[#daa520] underline decoration-1 underline-offset-2 inline-flex items-center gap-1 transition-colors"
      >
        {children}
        <ExternalLink className="w-3 h-3" />
      </a>
    ),
    
    // Blockquotes
    blockquote: ({ children }) => (
      <blockquote className="border-l-4 border-[#cd853f]/50 pl-4 italic text-[#a67c52] mb-2 bg-[#3f2e1e]/20 py-2 rounded-r">
        {children}
      </blockquote>
    ),
    
    // Strong/Bold
    strong: ({ children }) => (
      <strong className="font-bold text-[#cd853f]">{children}</strong>
    ),
    
    // Emphasis/Italic
    em: ({ children }) => (
      <em className="italic text-[#daa520]">{children}</em>
    ),
    
    // Horizontal rule
    hr: () => (
      <hr className="border-[#8b4513]/30 my-4" />
    ),
    
    // Tables
    table: ({ children }) => (
      <div className="overflow-x-auto mb-2">
        <table className="min-w-full border border-[#8b4513]/30 rounded-lg">
          {children}
        </table>
      </div>
    ),
    thead: ({ children }) => (
      <thead className="bg-[#3f2e1e]/50">{children}</thead>
    ),
    tbody: ({ children }) => (
      <tbody>{children}</tbody>
    ),
    tr: ({ children }) => (
      <tr className="border-b border-[#8b4513]/20">{children}</tr>
    ),
    th: ({ children }) => (
      <th className="px-3 py-2 text-left text-[#cd853f] font-semibold">{children}</th>
    ),
    td: ({ children }) => (
      <td className="px-3 py-2 text-[#e5ddd5]">{children}</td>
    ),
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
      <div className={`relative group max-w-3xl ${isUser ? "ml-12" : "mr-12"}`}>
        {/* Bubble */}
        <div
          className={`rounded-2xl px-4 py-3 shadow-lg transition-all duration-200 hover:shadow-xl ${
            isUser
              ? "bg-gradient-to-r from-[#a0522d] to-[#cd853f] text-white ml-auto border border-[#8b4513]/30"
              : "bg-[#2d2214]/50 border border-[#3f2e1e]/50 backdrop-blur-sm text-[#e5ddd5]"
          }`}
        >
          {message.isTyping ? (
            <TypingAnimation />
          ) : isUser ? (
            <div className="leading-relaxed">{message.text}</div>
          ) : (
            <div className="leading-relaxed">
              <ReactMarkdown components={markdownComponents}>
                {message.text}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* All controls in one row - only for bot messages */}
        {!isUser && (
          <div className={`flex items-center gap-2 mt-1 opacity-0 group-hover:opacity-100 transition-opacity ${
            isUser ? "justify-end" : "justify-start"
          }`}>
            {/* RAG indicator (clickable to show sources) */}
            {message.ragUsed && message.sources && message.sources.length > 0 && (
              <button
                onClick={() => setShowSources(true)}
                aria-label="View RAG sources"
                className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-[#cd853f]/20 border border-[#cd853f]/30 text-[#cd853f] text-xs font-medium hover:bg-[#cd853f]/30 transition-colors"
              >
                <Database className="w-3 h-3" />
                <span>RAG ({message.sources.length})</span>
              </button>
            )}

            {/* Feedback buttons */}
            <button
              onClick={() => toggle("up")}
              aria-label="Like response"
              className="p-1 focus:outline-none"
            >
              <ThumbsUp {...iconProps("up")} />
            </button>
            <button
              onClick={() => toggle("down")}
              aria-label="Dislike response"
              className="p-1 focus:outline-none"
            >
              <ThumbsDown {...iconProps("down")} />
            </button>

            {/* Timestamp */}
            <span className="text-xs text-[#a67c52] px-1">
              {timestamp}
            </span>
          </div>
        )}

        {/* User timestamp (separate for alignment) */}
        {isUser && (
          <div className="text-xs text-[#a67c52] mt-1 px-1 opacity-0 group-hover:opacity-100 transition-opacity text-right">
            {timestamp}
          </div>
        )}

        {/* Sources Popover - now shows as modal */}
        {showSources && message.sources && (
          <SourcesPopover
            sources={message.sources}
            onClose={() => setShowSources(false)}
          />
        )}
      </div>
    </div>
  );
}