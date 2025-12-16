import React, { useEffect, useRef, useState } from 'react';
import { FolderOpen, Copy, Trash2, Eye, Terminal, ChevronRight, Move, Link, MoreHorizontal, Edit2, FileText, Info, Archive, Hash } from 'lucide-react';

const ContextMenu = ({ x, y, item, onClose, onAction }) => {
  const menuRef = useRef(null);
  const [showOpsSubmenu, setShowOpsSubmenu] = useState(false);
  const [showInfoSubmenu, setShowInfoSubmenu] = useState(false);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        onClose();
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  if (!item) return null;

  const isFolder = item.chipType === 'folder';
  const isFile = item.chipType === 'file' || !item.chipType; 
  const isAction = item.chipType === 'action';

  if (isAction) return null; 

  // Calculate position to keep menu on screen
  const isNearBottom = y > window.innerHeight - 300;
  const menuStyle = {
      left: x,
      ...(isNearBottom 
          ? { bottom: window.innerHeight - y, transformOrigin: "bottom left" } 
          : { top: y, transformOrigin: "top left" }
      )
  };

  return (
    <div 
      ref={menuRef}
      className="fixed z-50 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl py-1 min-w-[200px] animate-in fade-in zoom-in-95 duration-100"
      style={menuStyle}
    >
      <div className="px-3 py-2 border-b border-zinc-800 mb-1">
        <p className="text-xs font-medium text-zinc-400 truncate max-w-[180px]">{item.text}</p>
      </div>

      <button 
        onClick={() => onAction('open_file', item)}
        className="w-full px-3 py-1.5 text-left text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white flex items-center gap-2 transition-colors"
      >
        <FolderOpen size={14} />
        <span>Open</span>
      </button>

      <button 
        onClick={() => onAction('reveal', item)}
        className="w-full px-3 py-1.5 text-left text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white flex items-center gap-2 transition-colors"
      >
        <Eye size={14} />
        <span>Reveal in Finder</span>
      </button>

      <div className="h-px bg-zinc-800 my-1" />

      <button 
        onClick={() => onAction('copy_path', item)}
        className="w-full px-3 py-1.5 text-left text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white flex items-center gap-2 transition-colors"
      >
        <Terminal size={14} />
        <span>Copy Path</span>
      </button>

      {/* File Operations Submenu */}
      <div 
        className="relative"
        onMouseEnter={() => setShowOpsSubmenu(true)}
        onMouseLeave={() => setShowOpsSubmenu(false)}
      >
        <button className="w-full px-3 py-1.5 text-left text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white flex items-center justify-between transition-colors">
            <div className="flex items-center gap-2">
                <MoreHorizontal size={14} />
                <span>File Operations</span>
            </div>
            <ChevronRight size={12} />
        </button>

        {showOpsSubmenu && (
            <div className={`absolute left-full ml-1 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl py-1 min-w-[180px] ${isNearBottom ? 'bottom-0' : 'top-0'}`}>
                <button 
                    onClick={() => onAction('move_file', item)}
                    className="w-full px-3 py-1.5 text-left text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white flex items-center gap-2 transition-colors"
                >
                    <Move size={14} />
                    <span>Move to...</span>
                </button>
                <button 
                    onClick={() => onAction('copy_file', item)}
                    className="w-full px-3 py-1.5 text-left text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white flex items-center gap-2 transition-colors"
                >
                    <Copy size={14} />
                    <span>Copy to...</span>
                </button>
                <button 
                    onClick={() => onAction('rename_item', item)}
                    className="w-full px-3 py-1.5 text-left text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white flex items-center gap-2 transition-colors"
                >
                    <Edit2 size={14} />
                    <span>Rename</span>
                </button>
                <button 
                    onClick={() => onAction('create_symlink', item)}
                    className="w-full px-3 py-1.5 text-left text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white flex items-center gap-2 transition-colors"
                >
                    <Link size={14} />
                    <span>Create Shortcut</span>
                </button>
                <button 
                    onClick={() => onAction('compress_item', item)}
                    className="w-full px-3 py-1.5 text-left text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white flex items-center gap-2 transition-colors"
                >
                    <Archive size={14} />
                    <span>Compress (Zip)</span>
                </button>
            </div>
        )}
      </div>

      {/* Info & Inspection Submenu */}
      <div 
        className="relative"
        onMouseEnter={() => setShowInfoSubmenu(true)}
        onMouseLeave={() => setShowInfoSubmenu(false)}
      >
        <button className="w-full px-3 py-1.5 text-left text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white flex items-center justify-between transition-colors">
            <div className="flex items-center gap-2">
                <Info size={14} />
                <span>Info & Inspect</span>
            </div>
            <ChevronRight size={12} />
        </button>

        {showInfoSubmenu && (
            <div className={`absolute left-full ml-1 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl py-1 min-w-[180px] ${isNearBottom ? 'bottom-0' : 'top-0'}`}>
                <button 
                    onClick={() => onAction('get_file_info', item)}
                    className="w-full px-3 py-1.5 text-left text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white flex items-center gap-2 transition-colors"
                >
                    <Info size={14} />
                    <span>Get Info</span>
                </button>
                <button 
                    onClick={() => onAction('read_file', item)}
                    className="w-full px-3 py-1.5 text-left text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white flex items-center gap-2 transition-colors"
                >
                    <FileText size={14} />
                    <span>Read Content</span>
                </button>
                <button 
                    onClick={() => onAction('count_lines', item)}
                    className="w-full px-3 py-1.5 text-left text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white flex items-center gap-2 transition-colors"
                >
                    <FileText size={14} />
                    <span>Count Lines</span>
                </button>
                <button 
                    onClick={() => onAction('get_file_hash', item)}
                    className="w-full px-3 py-1.5 text-left text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white flex items-center gap-2 transition-colors"
                >
                    <Hash size={14} />
                    <span>Calculate Hash</span>
                </button>
            </div>
        )}
      </div>

      <div className="h-px bg-zinc-800 my-1" />

      <button 
        onClick={() => onAction('delete_file', item)}
        className="w-full px-3 py-1.5 text-left text-sm text-red-400 hover:bg-red-500/10 flex items-center gap-2 transition-colors"
      >
        <Trash2 size={14} />
        <span>Delete</span>
      </button>
    </div>
  );
};

export default ContextMenu;