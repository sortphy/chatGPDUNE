export default function TypingAnimation() {
  return (
    <div className="flex gap-1">
      <div className="w-2 h-2 bg-[#8b4513] rounded-full animate-bounce [animation-delay:-0.3s]"></div>
      <div className="w-2 h-2 bg-[#8b4513] rounded-full animate-bounce [animation-delay:-0.15s]"></div>
      <div className="w-2 h-2 bg-[#8b4513] rounded-full animate-bounce"></div>
    </div>
  );
}