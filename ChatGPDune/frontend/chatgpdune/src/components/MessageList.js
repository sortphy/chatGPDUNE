import MessageBubble from './MessageBubble';

export default function MessageList({ messages, messagesEndRef }) {
  return (
    <div className="max-w-4xl mx-auto px-4 pb-32">
      <div className="space-y-6 py-6">
        {messages.map((message, index) => (
          <MessageBubble 
            key={index} 
            message={message} 
          />
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}