import React, { useEffect, useRef, useState } from 'react';
import { Bot, User, AlertTriangle, Check, X, ChevronDown, ChevronUp, Info, Trash2 } from 'lucide-react';

const SecurityMessage = ({ msg, isPending, onConfirm, onCancel, onChipClick }) => {
  const { intent, risk, content } = msg;
  const isGeneric = content === "Action allowed.";
  // Always show details by default for security alerts so user sees what they are confirming
  const [showDetails, setShowDetails] = useState(true);
  
  // State for batch targets
  const [activeBatchTargets, setActiveBatchTargets] = useState(intent?.batch_targets || []);

  // Extract relevant details from intent
  const action = intent?.action || "Unknown";
  const target = intent?.resolved_path || intent?.path || intent?.resolved_src || intent?.source || intent?.destination || "Unknown";
  const isBatch = !!intent?.batch_targets;
  
  let batchDetails = null;
  if (isBatch && activeBatchTargets.length > 0) {
      const firstPath = activeBatchTargets[0];
      const sep = firstPath.includes('\\') ? '\\' : '/';
      const lastSep = firstPath.lastIndexOf(sep);
      const commonDir = firstPath.substring(0, lastSep);
      
      const files = activeBatchTargets.map(p => ({
          fullPath: p,
          fileName: p.split(sep).pop()
      }));
      batchDetails = { commonDir, files };
  }
  
  const handleRemoveFile = (pathToRemove) => {
      setActiveBatchTargets(prev => prev.filter(p => p !== pathToRemove));
  };

  const handleConfirmClick = () => {
      if (isBatch) {
          onConfirm(activeBatchTargets);
      } else {
          onConfirm();
      }
  };
  
  return (
    <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 w-full">
      <div className="flex items-center gap-2 text-amber-500 mb-2 font-semibold">
        <AlertTriangle size={16} />
        <span>Security Alert</span>
      </div>
      
      {!isGeneric && <p className="text-zinc-300 mb-3">{content}</p>}
      
      {/* Details Toggle */}
      <button 
        onClick={() => setShowDetails(!showDetails)}
        className="flex items-center gap-1 text-xs text-amber-500/80 hover:text-amber-400 mb-3 transition-colors"
      >
        {showDetails ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        {showDetails ? "Hide Details" : "Show Details"}
      </button>

      {/* Details Panel */}
      {showDetails && (
        <div className="bg-zinc-900/50 rounded p-2 mb-3 text-xs space-y-1.5 border border-amber-500/10">
           <div className="flex gap-2">
             <span className="text-zinc-500 w-16">Risk Level:</span>
             <span className="text-amber-500 font-bold">{risk}</span>
           </div>
           <div className="flex gap-2">
             <span className="text-zinc-500 w-16">Action:</span>
             <span className="text-zinc-300 font-mono">{action}</span>
           </div>
           
           {isBatch ? (
             <div className="flex flex-col gap-2 mt-1">
               <div className="flex gap-2">
                 <span className="text-zinc-500 w-16 shrink-0">Source:</span>
                 <span className="text-zinc-300 font-mono break-all">{batchDetails?.commonDir || "Multiple Sources"}</span>
               </div>
               <div className="flex gap-2">
                 <span className="text-zinc-500 w-16 shrink-0">Files:</span>
                 <div className="flex flex-col gap-1 w-full">
                   <span className="text-zinc-400 italic mb-1">{activeBatchTargets.length} files selected</span>
                   
                   {activeBatchTargets.length > 0 ? (
                   <div className="max-h-40 overflow-y-auto border border-zinc-700/50 rounded bg-zinc-800/30">
                     <table className="w-full text-left border-collapse">
                       <thead className="bg-zinc-800/80 sticky top-0">
                         <tr>
                           <th className="p-2 text-zinc-400 font-medium border-b border-zinc-700/50">File Name</th>
                           {isPending && <th className="p-2 text-zinc-400 font-medium border-b border-zinc-700/50 w-8"></th>}
                         </tr>
                       </thead>
                       <tbody>
                         {batchDetails.files.map((item, i) => {
                           const { fullPath, fileName } = item;
                           const isFolder = !fileName.includes('.'); // Simple heuristic
                           const colorClasses = isFolder 
                             ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/30"
                             : "bg-blue-500/20 text-blue-300 border-blue-500/30 hover:bg-blue-500/30";
                           
                           return (
                             <tr key={i} className="border-b border-zinc-800/50 last:border-0 hover:bg-zinc-800/50 group">
                               <td className="p-2">
                                 <span 
                                   onClick={() => onChipClick && onChipClick({ text: fileName, path: fullPath, type: isFolder ? 'folder' : 'file' })}
                                   className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-mono cursor-pointer transition-colors border ${colorClasses}`}
                                 >
                                   {fileName}
                                 </span>
                               </td>
                               {isPending && (
                                 <td className="p-2 text-right">
                                   <button 
                                     onClick={() => handleRemoveFile(fullPath)}
                                     className="text-zinc-600 hover:text-red-400 transition-colors p-1 rounded hover:bg-zinc-700/50 opacity-0 group-hover:opacity-100"
                                     title="Remove from batch"
                                   >
                                     <Trash2 size={12} />
                                   </button>
                                 </td>
                               )}
                             </tr>
                           );
                         })}
                       </tbody>
                     </table>
                   </div>
                   ) : (
                     <div className="text-zinc-500 italic p-2 border border-zinc-800 rounded bg-zinc-900/30">
                       No files selected. Action will be skipped for empty batch.
                     </div>
                   )}
                 </div>
               </div>
             </div>
           ) : (
             <div className="flex gap-2">
               <span className="text-zinc-500 w-16 shrink-0">Target:</span>
               <span className="text-zinc-300 font-mono break-all">{target}</span>
             </div>
           )}
        </div>
      )}
      
      {/* Action Buttons */}
      {isPending && (
        <div className="flex gap-2 mt-2">
          <button 
            onClick={handleConfirmClick}
            disabled={isBatch && activeBatchTargets.length === 0}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors
              ${isBatch && activeBatchTargets.length === 0 
                ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed' 
                : 'bg-amber-600 hover:bg-amber-500 text-white'}`}
          >
            <Check size={12} /> Confirm
          </button>
          <button 
            onClick={onCancel}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-md text-xs font-medium transition-colors"
          >
            <X size={12} /> Cancel
          </button>
        </div>
      )}
    </div>
  );
};

const MessageList = ({ messages, pendingConfirmation, onConfirm, onCancel, onChipClick, onChipContextMenu }) => {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const renderContent = (content) => {
    if (Array.isArray(content)) {
      return content.map((segment, i) => {
        if (segment.type === 'chip') {
          let colorClasses = "bg-blue-500/20 text-blue-300 border-blue-500/30 hover:bg-blue-500/30";
          if (segment.chipType === 'action') colorClasses = "bg-amber-500/20 text-amber-300 border-amber-500/30 hover:bg-amber-500/30";
          if (segment.chipType === 'folder') colorClasses = "bg-emerald-500/20 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/30";

          return (
            <span 
              key={i}
              onClick={() => onChipClick && onChipClick(segment)}
              onContextMenu={(e) => onChipContextMenu && onChipContextMenu(e, segment)}
              className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-mono mx-0.5 align-middle select-none cursor-pointer transition-colors border ${colorClasses}`}
              title={segment.path}
            >
              {segment.text}
            </span>
          );
        }
        return <span key={i}>{segment.text}</span>;
      });
    }
    return content;
  };

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
            
            {msg.isConfirmation ? (
              <SecurityMessage 
                msg={msg} 
                isPending={idx === messages.length - 1 && pendingConfirmation}
                onConfirm={onConfirm}
                onCancel={onCancel}
                onChipClick={onChipClick}
              />
            ) : (
              renderContent(msg.content)
            )}
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
};

export default MessageList;
