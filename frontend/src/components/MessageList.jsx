import React, { useEffect, useRef } from 'react';
import { Bot, User } from 'lucide-react';

const MessageList = ({ messages }) => {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-6">
      {messages.map((msg, idx) => (
        <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
          {/* Avatar */}
          <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 
            ${msg.role === 'assistant' ? 'bg-indigo-500/10 text-indigo-400' : 'bg-zinc-800 text-zinc-400'}`}>
            {msg.role === 'assistant' ? <Bot size={16} /> : <User size={16} />}
          </div>

          {/* Bubble */}
          <div className={`max-w-[85%] text-sm leading-relaxed p-3 rounded-2xl
            ${msg.role === 'assistant' 
              ? 'bg-transparent text-zinc-300' 
              : 'bg-zinc-800 text-zinc-100'}`}>
            {msg.content}
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
};

export default MessageList;
