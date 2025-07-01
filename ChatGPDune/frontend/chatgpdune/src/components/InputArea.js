import { Send, ChevronDown } from "lucide-react";
import { useState, useEffect } from "react";

export default function InputArea({ 
  input, 
  setInput, 
  isLoading, 
  onSendMessage, 
  onKeyPress, 
  inputRef,
  useRag,
  setUseRag
}) {
  const [selectedModel, setSelectedModel] = useState("deepseek-r1");
  const [showModelDropdown, setShowModelDropdown] = useState(false);
  
  // Auto-resize textarea based on content
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      const scrollHeight = inputRef.current.scrollHeight;
      const maxHeight = 200; // Max height in pixels (about 8-10 lines)
      inputRef.current.style.height = Math.min(scrollHeight, maxHeight) + 'px';
    }
  }, [input]);

  const models = [
    { id: "deepseek-r1", name: "DeepSeek R1" }
  ];

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
            className="w-full bg-transparent text-white placeholder-[#a67c52] px-6 py-4 pb-14 resize-none focus:outline-none min-h-[60px] max-h-[200px] overflow-y-auto"
            disabled={isLoading}
            rows={1}
            style={{ 
              resize: 'none',
              scrollbarWidth: 'thin',
              scrollbarColor: '#3f2e1e transparent'
            }}
          />

          {/* Bottom bar with controls */}
          <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between px-4 py-3 border-t border-[#3f2e1e]/30">
            {/* RAG Toggle Switch - Bottom Left */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-[#a67c52]">RAG</span>
              <button
                onClick={() => setUseRag(prev => !prev)}
                disabled={isLoading}
                className={`relative w-10 h-5 rounded-full transition-all duration-200 ${
                  useRag 
                    ? 'bg-gradient-to-r from-[#8b4513] to-[#cd853f]' 
                    : 'bg-[#3f2e1e]/60'
                } disabled:opacity-50`}
              >
                <div 
                  className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow-sm transition-transform duration-200 ${
                    useRag ? 'translate-x-5' : 'translate-x-0.5'
                  }`}
                />
              </button>
            </div>

            {/* Right side controls */}
            <div className="flex items-center gap-2">
              {/* Model Selector */}
              <div className="relative">
                <button
                  onClick={() => setShowModelDropdown(!showModelDropdown)}
                  disabled={isLoading}
                  className="flex items-center gap-1 px-3 py-1.5 text-xs text-[#a67c52] hover:text-white bg-[#3f2e1e]/40 hover:bg-[#3f2e1e]/60 rounded-lg transition-all duration-200 disabled:opacity-50"
                >
                  <span>{models.find(m => m.id === selectedModel)?.name}</span>
                  <ChevronDown className="w-3 h-3" />
                </button>
                
                {showModelDropdown && (
                  <div className="absolute bottom-full mb-2 right-0 bg-[#2b1b11] border border-[#3f2e1e]/50 rounded-lg shadow-xl min-w-32">
                    {models.map((model) => (
                      <button
                        key={model.id}
                        onClick={() => {
                          setSelectedModel(model.id);
                          setShowModelDropdown(false);
                        }}
                        className={`w-full text-left px-3 py-2 text-xs hover:bg-[#3f2e1e]/40 first:rounded-t-lg last:rounded-b-lg ${
                          selectedModel === model.id ? 'text-[#cd853f]' : 'text-[#a67c52]'
                        }`}
                      >
                        {model.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Send Button */}
              <button
                onClick={onSendMessage}
                disabled={!input.trim() || isLoading}
                className="w-8 h-8 bg-gradient-to-r from-[#8b4513] to-[#cd853f] rounded-lg flex items-center justify-center text-white shadow-lg transition-all duration-200 hover:shadow-xl hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-[#a67c52] mt-3">
          Using Ollama & DeepSeek R1 • Às vezes demora, depende da máquina, pois roda local.
        </div>
      </div>
    </div>
  );
}