import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Folder } from 'lucide-react';

const InputArea = ({ onSend }) => {
  const [input, setInput] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef(null);

  // Mock suggestions
  const suggestions = [
    { path: "~/Documents", type: "folder" },
    { path: "~/Downloads", type: "folder" },
    { path: "~/Desktop", type: "folder" },
    { path: "~/Pictures", type: "folder" },
  ];

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim()) {
        onSend(input);
        setInput("");
        setShowSuggestions(false);
      }
    }
  };

  const handleChange = (e) => {
    const val = e.target.value;
    setInput(val);
    // Simple trigger for demo: show if typing starts with ~ or /
    if (val.includes('~') || val.includes('/')) {
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  };

  return (
    <div className="p-4 pt-2 relative">
      {/* Autocomplete Popover */}
      {showSuggestions && (
        <div className="absolute bottom-full left-4 right-4 mb-2 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl overflow-hidden z-10">
          <div className="px-3 py-2 text-[10px] font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-900/50 border-b border-zinc-800">
            Suggested Paths
          </div>
          <ul>
            {suggestions.map((s, i) => (
              <li key={i} 
                  className="px-3 py-2 flex items-center gap-2 hover:bg-indigo-500/10 hover:text-indigo-300 cursor-pointer text-zinc-400 text-sm transition-colors"
                  onClick={() => {
                    setInput(s.path);
                    setShowSuggestions(false);
                    inputRef.current?.focus();
                  }}
              >
                <Folder size={14} />
                <span>{s.path}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Input Box */}
      <div className="relative bg-zinc-900 border border-zinc-800 rounded-xl shadow-sm focus-within:ring-1 focus-within:ring-indigo-500/50 focus-within:border-indigo-500/50 transition-all">
        <textarea
          ref={inputRef}
          value={input}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask OS Assistant..."
          className="w-full bg-transparent text-zinc-200 text-sm p-3 pr-12 resize-none outline-none h-[52px] max-h-32 placeholder:text-zinc-600"
          rows={1}
        />
        
        <div className="absolute right-2 bottom-2 flex items-center gap-1">
          <button className="p-1.5 text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800 rounded-lg transition-colors">
            <Paperclip size={16} />
          </button>
          <button 
            onClick={() => {
              if (input.trim()) {
                onSend(input);
                setInput("");
              }
            }}
            className={`p-1.5 rounded-lg transition-all ${input.trim() ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/20' : 'bg-zinc-800 text-zinc-600'}`}
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default InputArea;
