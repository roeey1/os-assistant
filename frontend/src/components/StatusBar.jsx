import React from 'react';
import { Command, CornerDownLeft, ArrowUp } from 'lucide-react';

const StatusBar = ({ status = "Ready" }) => {
  return (
    <div className="h-8 bg-zinc-900/80 border-t border-zinc-800 flex items-center justify-between px-4 text-xs select-none backdrop-blur-sm rounded-b-xl">
      {/* Left: Status Indicator */}
      <div className="flex items-center gap-2 text-zinc-400">
        <div className={`w-2 h-2 rounded-full ${status === "Processing" ? "bg-amber-500 animate-pulse" : "bg-emerald-500"}`}></div>
        <span className="font-medium">{status}</span>
      </div>

      {/* Right: Shortcuts */}
      <div className="flex items-center gap-4 text-zinc-500">
        <div className="flex items-center gap-1.5">
          <span className="bg-zinc-800 px-1.5 py-0.5 rounded text-[10px] text-zinc-300 font-mono flex items-center">
            <ArrowUp size={10} className="mr-0.5" /> K
          </span>
          <span>Move</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="bg-zinc-800 px-1.5 py-0.5 rounded text-[10px] text-zinc-300 font-mono">Tab</span>
          <span>Autocomplete</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="bg-zinc-800 px-1.5 py-0.5 rounded text-[10px] text-zinc-300 font-mono flex items-center">
            <CornerDownLeft size={10} />
          </span>
          <span>Execute</span>
        </div>
      </div>
    </div>
  );
};

export default StatusBar;
