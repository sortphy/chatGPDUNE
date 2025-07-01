import { useState } from "react";
import { X, ChevronDown, ChevronUp, Copy, Check } from "lucide-react";

export default function SourcesPopover({ sources, onClose }) {
  const [expandedSources, setExpandedSources] = useState(new Set());
  const [copiedStates, setCopiedStates] = useState(new Set());

  const toggleExpanded = (sourceId) => {
    const newExpanded = new Set(expandedSources);
    if (newExpanded.has(sourceId)) {
      newExpanded.delete(sourceId);
    } else {
      newExpanded.add(sourceId);
    }
    setExpandedSources(newExpanded);
  };

  const copyToClipboard = async (text, sourceId) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedStates(prev => new Set([...prev, sourceId]));
      setTimeout(() => {
        setCopiedStates(prev => {
          const newSet = new Set(prev);
          newSet.delete(sourceId);
          return newSet;
        });
      }, 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="relative w-full max-w-4xl max-h-[80vh] m-4 rounded-xl border border-[#3f2e1e]/70 bg-[#2d2214]/95 backdrop-blur-sm shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#3f2e1e]/50">
          <h3 className="text-lg font-semibold text-[#cd853f]">
            RAG Sources ({sources.length})
          </h3>
          <button
            onClick={onClose}
            aria-label="Close sources"
            className="text-[#a67c52] hover:text-[#cd853f] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(80vh-80px)] p-4 space-y-4">
          {sources.map((source) => {
            const isExpanded = expandedSources.has(source.id);
            const isCopied = copiedStates.has(source.id);
            
            return (
              <div
                key={source.id}
                className="border border-[#3f2e1e]/50 rounded-lg bg-[#1a120b]/30 overflow-hidden"
              >
                {/* Source Header */}
                <div className="p-3 border-b border-[#3f2e1e]/30">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-[#cd853f]">
                        Source #{source.id}
                      </span>
                      {source.file && (
                        <span className="text-xs text-[#a67c52] bg-[#3f2e1e]/30 px-2 py-1 rounded">
                          {source.file}
                        </span>
                      )}
                      {source.score && (
                        <span className="text-xs text-[#a67c52] bg-[#2d2214]/50 px-2 py-1 rounded">
                          Score: {source.score}
                        </span>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => copyToClipboard(source.content, source.id)}
                        className="p-1.5 text-[#a67c52] hover:text-[#cd853f] transition-colors"
                        aria-label="Copy content"
                      >
                        {isCopied ? (
                          <Check className="w-4 h-4 text-green-500" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </button>
                      
                      <button
                        onClick={() => toggleExpanded(source.id)}
                        className="p-1.5 text-[#a67c52] hover:text-[#cd853f] transition-colors"
                        aria-label={isExpanded ? "Collapse" : "Expand"}
                      >
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4" />
                        ) : (
                          <ChevronDown className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Content */}
                <div className="p-3">
                  <div className="text-sm text-[#f5f0e6] leading-relaxed">
                    {isExpanded ? (
                      <div className="whitespace-pre-wrap">{source.content}</div>
                    ) : (
                      <div>
                        {source.preview}
                        {source.content.length > 150 && (
                          <button
                            onClick={() => toggleExpanded(source.id)}
                            className="text-[#cd853f] hover:text-[#cd853f]/80 ml-2 underline"
                          >
                            Show more
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#3f2e1e]/50 text-center">
          <p className="text-xs text-[#a67c52]">
            These are the knowledge chunks used to generate the response
          </p>
        </div>
      </div>
    </div>
  );
}