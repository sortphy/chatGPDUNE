// components/SourcesPopover.js
import { X } from "lucide-react";

export default function SourcesPopover({ sources, onClose }) {
  return (
    <div
      className="absolute z-20 left-0 top-full mt-2 w-max max-w-xs
                 rounded-xl border border-[#3f2e1e]/70 bg-[#2d2214]/80
                 p-4 text-xs text-[#f5f0e6] backdrop-blur-sm shadow-lg"
    >
      <button
        onClick={onClose}
        aria-label="Fechar"
        className="absolute right-2 top-2 text-[#a67c52] hover:text-[#cd853f]"
      >
        <X className="w-3 h-3" />
      </button>

      <p className="mb-2 font-semibold text-[#cd853f]">Fontes utilizadas</p>
      <ul className="list-disc list-inside space-y-1">
        {sources.map((src, i) => (
          <li key={i}>{src}</li>
        ))}
      </ul>
    </div>
  );
}
