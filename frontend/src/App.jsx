import React, { useState } from 'react';
import MessageList from './components/MessageList';
import InputArea from './components/InputArea';
import ContextPane from './components/ContextPane';
import StatusBar from './components/StatusBar';

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your OS Assistant. How can I help you today?' }
  ]);
  const [status, setStatus] = useState("Ready");

  const handleSend = (text) => {
    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    
    // Simulate processing
    setStatus("Processing");
    setTimeout(() => {
      setMessages(prev => [...prev, { role: 'assistant', content: "I've received your command. This is a demo response." }]);
      setStatus("Ready");
    }, 1000);
  };

  return (
    <div className="w-[850px] h-[600px] bg-zinc-950 rounded-xl border border-zinc-800 shadow-2xl flex flex-col overflow-hidden font-sans text-zinc-100 relative">
      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Left Pane: Chat (40%) */}
        <div className="w-[40%] flex flex-col border-r border-zinc-800/50 bg-zinc-950/50">
          <MessageList messages={messages} />
          <InputArea onSend={handleSend} />
        </div>

        {/* Right Pane: Context (60%) */}
        <div className="w-[60%] bg-zinc-950">
          <ContextPane />
        </div>
      </div>

      {/* Bottom Toolbar */}
      <StatusBar status={status} />
    </div>
  );
}

export default App;
