import React from 'react';
import { FileText, Calendar, HardDrive, Folder, Image as ImageIcon } from 'lucide-react';

const ContextPane = ({ selectedItem }) => {
  // Placeholder data if nothing is selected
  const item = selectedItem || {
    name: "report_final.pdf",
    type: "PDF Document",
    size: "2.4 MB",
    created: "Oct 24, 2023",
    path: "~/Documents/Work/Reports",
    preview: null
  };

  return (
    <div className="h-full flex flex-col bg-zinc-900/30 border-l border-zinc-800/50">
      {/* Header */}
      <div className="p-4 border-b border-zinc-800/50 flex items-center gap-3">
        <div className="w-10 h-10 bg-zinc-800 rounded-lg flex items-center justify-center text-zinc-400">
          <FileText size={20} />
        </div>
        <div className="overflow-hidden">
          <h2 className="font-semibold text-zinc-200 truncate">{item.name}</h2>
          <p className="text-xs text-zinc-500 truncate">{item.type}</p>
        </div>
      </div>

      {/* Preview Area */}
      <div className="flex-1 p-6 flex items-center justify-center bg-zinc-950/20">
        <div className="w-full h-48 bg-zinc-900 rounded-lg border border-zinc-800 flex flex-col items-center justify-center text-zinc-600 gap-2 shadow-inner">
          <ImageIcon size={32} className="opacity-50" />
          <span className="text-sm">No Preview Available</span>
        </div>
      </div>

      {/* Metadata Grid */}
      <div className="p-4 border-t border-zinc-800/50 bg-zinc-900/20">
        <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">Metadata</h3>
        <div className="grid grid-cols-2 gap-y-4 gap-x-2">
          <MetaItem icon={<HardDrive size={14} />} label="Size" value={item.size} />
          <MetaItem icon={<Calendar size={14} />} label="Created" value={item.created} />
          <MetaItem icon={<Folder size={14} />} label="Path" value={item.path} fullWidth />
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
