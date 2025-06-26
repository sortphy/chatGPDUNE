export default function Header() {
  return (
    <div className="sticky top-0 z-10 bg-[#1a120b]/90 backdrop-blur-md border-b border-[#3f2e1e]/60">
      <div className="max-w-4xl mx-auto px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-r from-[#8b4513] to-[#cd853f] rounded-full flex items-center justify-center shadow-lg">
            <img 
              src="/images/sortphy.png" 
              alt="Sortphy Logo" 
              className="w-full h-full rounded-full object-cover"
            />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-[#8b4513] to-[#cd853f] bg-clip-text text-transparent">
              ChatGPDune
            </h1>
            <p className="text-sm text-[#bfa77a]">Powered by Sortphy</p>
          </div>
        </div>
      </div>
    </div>
  );
}