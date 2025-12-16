import React, { useState, useEffect } from 'react';
import { FileText, Calendar, HardDrive, Folder, Image as ImageIcon, Zap, Terminal, AppWindow, AlertCircle } from 'lucide-react';

const ContextPane = ({ selectedItem }) => {
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchPreview = async () => {
      if (selectedItem && (selectedItem.type === 'file' || selectedItem.type === 'folder') && selectedItem.path) {
        setLoading(true);
        setPreview(null);
        try {
          if (window.eel) {
            const result = await window.eel.get_file_preview(selectedItem.path)();
            setPreview(result);
          }
        } catch (e) {
          console.error("Preview error:", e);
          setPreview({ type: 'error', content: "Failed to load preview" });
        } finally {
          setLoading(false);
        }
      } else {
        setPreview(null);
      }
    };

    fetchPreview();
  }, [selectedItem]);

  if (!selectedItem) {
    return (
      <div className="h-full flex flex-col items-center justify-center bg-zinc-900/30 border-l border-zinc-800/50 text-zinc-600">
        <Terminal size={48} className="mb-4 opacity-20" />
        <p className="text-sm">Start typing to see context...</p>
      </div>
    );
  }

  const { text, type, path } = selectedItem;
  
  // Map type to display string and icon
  let displayType = "Unknown";
  let Icon = FileText;
  
  if (type === 'action') {
    displayType = "Action";
    Icon = Zap;
  } else if (type === 'folder') {
    displayType = "Folder";
    Icon = Folder;
  } else if (type === 'file') {
    displayType = "File";
    Icon = FileText;
  } else if (type === 'app') {
    displayType = "Application";
    Icon = AppWindow;
  }

  return (
    <div className="h-full flex flex-col bg-zinc-900/30 border-l border-zinc-800/50">
      {/* Header */}
      <div className="p-4 border-b border-zinc-800/50 flex items-center gap-3">
        <div className="w-10 h-10 bg-zinc-800 rounded-lg flex items-center justify-center text-zinc-400">
          <Icon size={20} />
        </div>
        <div className="overflow-hidden">
          <h2 className="font-semibold text-zinc-200 truncate">{text}</h2>
          <p className="text-xs text-zinc-500 truncate">{displayType}</p>
        </div>
      </div>

      {/* Preview Area */}
      <div className="flex-1 p-6 flex items-center justify-center bg-zinc-950/20 overflow-hidden relative">
        <div className="w-full h-full bg-zinc-900 rounded-lg border border-zinc-800 flex flex-col items-center justify-center text-zinc-600 gap-2 shadow-inner overflow-hidden relative">
           
           {loading && (
             <div className="absolute inset-0 flex items-center justify-center bg-zinc-900/80 z-10">
               <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
             </div>
           )}

           {type === 'action' ? (
             <>
                <Zap size={32} className="opacity-50 text-amber-500" />
                <span className="text-sm">Command</span>
             </>
           ) : type === 'app' ? (
             <>
                <AppWindow size={32} className="opacity-50 text-purple-500" />
                <span className="text-sm">Application</span>
             </>
           ) : preview?.type === 'image' ? (
             <img src={preview.content} alt="Preview" className="w-full h-full object-contain" />
           ) : preview?.type === 'pdf' ? (
             <iframe src={preview.content} className="w-full h-full border-0" title="PDF Preview" />
           ) : preview?.type === 'text' ? (
             <div className="w-full h-full p-4 overflow-auto text-xs font-mono text-zinc-400 whitespace-pre-wrap text-left">
               {preview.content}
             </div>
           ) : preview?.type === 'list' ? (
             <div className="w-full h-full p-4 overflow-auto text-left">
               <h4 className="text-xs font-semibold text-zinc-500 mb-2 uppercase">Folder Contents</h4>
               <ul className="space-y-1">
                 {preview.content.map((item, i) => (
                   <li key={i} className="text-xs text-zinc-400 flex items-center gap-2">
                     <span className="w-1 h-1 rounded-full bg-zinc-600"></span>
                     {item}
                   </li>
                 ))}
               </ul>
             </div>
           ) : (
             <>
                <ImageIcon size={32} className="opacity-50" />
                <span className="text-sm">{preview?.content || "No Preview Available"}</span>
             </>
           )}
        </div>
      </div>

      {/* Metadata Grid */}
      <div className="p-4 border-t border-zinc-800/50 bg-zinc-900/20">
        <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">Metadata</h3>
        <div className="grid grid-cols-2 gap-y-4 gap-x-2">
          {path && <MetaItem icon={<Folder size={14} />} label="Path" value={path} fullWidth />}
        </div>
      </div>
    </div>
  );
};

const MetaItem = ({ icon, label, value, fullWidth = false }) => (
  <div className={`${fullWidth ? 'col-span-2' : 'col-span-1'} flex flex-col gap-1`}>
    <span className="text-[10px] text-zinc-500 flex items-center gap-1.5">
      {icon} {label}
    </span>
    <span className="text-sm text-zinc-300 font-medium truncate" title={value}>
      {value}
    </span>
  </div>
);

export default ContextPane;
