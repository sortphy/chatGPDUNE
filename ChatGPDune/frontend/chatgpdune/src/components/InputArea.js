import { Send } from "lucide-react";

export default function InputArea({ 
  input, 
  setInput, 
  isLoading, 
  onSendMessage, 
  onKeyPress, 
  inputRef 
}) {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-[#1a120b] via-[#1a120b]/95 to-transparent pt-6 pb-6">
      <div className="max-w-4xl mx-auto px-4">
        <div className="relative bg-[#2b1b11]/60 backdrop-blur-sm rounded-2xl border border-[#3f2e1e]/50 shadow-2xl transition-all duration-200 focus-within:border-[#8b4513]/60 focus-within:shadow-[#8b4513]/10">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={onKeyPress}
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
            onClick={onSendMessage}
            disabled={!input.trim() || isLoading}
            className="absolute right-3 bottom-3 w-10 h-10 bg-gradient-to-r from-[#8b4513] to-[#cd853f] rounded-xl flex items-center justify-center text-white shadow-lg transition-all duration-200 hover:shadow-xl hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-[#a67c52] mt-3">
          Using Ollama & DeepSeek R1 • Às vezes demora, depende da máquina, pois roda local.
        </div>
      </div>
    </div>
  );
}