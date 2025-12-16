import React, { useState, useEffect, useRef } from 'react';
import { X, Check, FolderInput, Type, AlertTriangle } from 'lucide-react';

const ActionModal = ({ action, item, onClose, onConfirm }) => {
  const [value, setValue] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [justSelected, setJustSelected] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
      if (action === 'rename_item') {
          setValue(item.text); // Pre-fill with current name
      }
    }
  }, [action, item]);

  // Autocomplete Logic
  useEffect(() => {
    if (justSelected) {
        setJustSelected(false);
        return;
    }

    const fetchSuggestions = async () => {
      // Only fetch suggestions for destination inputs (move, copy, shortcut)
      // Rename usually doesn't need file suggestions unless we want to overwrite, but typically no.
      if (['move_file', 'copy_file', 'create_symlink'].includes(action) && value.trim().length > 0 && window.eel) {
        try {
          const results = await window.eel.get_suggestions(value)();
          // Filter out actions, we only want folders/files for destination
          const fileResults = results.filter(r => r.type !== 'action');
          setSuggestions(fileResults);
          setShowSuggestions(fileResults.length > 0);
          setSelectedIndex(0);
        } catch (e) {
          console.error("Failed to fetch suggestions", e);
        }
      } else {
        setShowSuggestions(false);
      }
    };

    const debounce = setTimeout(fetchSuggestions, 200);
    return () => clearTimeout(debounce);
  }, [value, action]);

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      if (showSuggestions) {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % suggestions.length);
      }
    } else if (e.key === 'ArrowUp') {
      if (showSuggestions) {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + suggestions.length) % suggestions.length);
      }
    } else if (e.key === 'Tab' || (e.key === 'Enter' && showSuggestions)) {
      if (showSuggestions && suggestions.length > 0) {
        e.preventDefault();
        applySuggestion(suggestions[selectedIndex]);
      }
    } else if (e.key === 'Escape') {
      if (showSuggestions) {
        e.preventDefault();
        setShowSuggestions(false);
      } else {
        onClose();
      }
    }
  };

  const applySuggestion = (suggestion) => {
    setJustSelected(true);
    setValue(suggestion.path);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // If suggestions are open and user hits enter, handleKeyDown takes care of it.
    // But if they click the button or hit enter without suggestions, we submit.
    if (!showSuggestions) {
        onConfirm(value);
    }
  };

  const getTitle = () => {
    switch (action) {
      case 'move_file': return 'Move Item';
      case 'copy_file': return 'Copy Item';
      case 'rename_item': return 'Rename Item';
      case 'create_symlink': return 'Create Shortcut';
      case 'delete_file': return 'Delete Item';
      case 'compress_item': return 'Compress Item';
      default: return 'Action';
    }
  };

  const getDescription = () => {
    switch (action) {
      case 'move_file': return `Where would you like to move "${item.text}"?`;
      case 'copy_file': return `Where would you like to copy "${item.text}"?`;
      case 'rename_item': return `Enter a new name for "${item.text}":`;
      case 'create_symlink': return `Where should the shortcut be created?`;
      case 'delete_file': return `Are you sure you want to delete "${item.text}"? This cannot be undone.`;
      case 'compress_item': return `Enter format (zip, tar, gztar) for "${item.text}":`;
      default: return '';
    }
  };

  const isDestAction = ['move_file', 'copy_file', 'create_symlink'].includes(action);
  const isRename = action === 'rename_item';
  const isDelete = action === 'delete_file';
  const isCompress = action === 'compress_item';

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl w-[400px] overflow-hidden animate-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="px-4 py-3 border-b border-zinc-800 flex justify-between items-center bg-zinc-900/50">
          <h3 className="font-semibold text-zinc-200 flex items-center gap-2">
            {isDelete && <AlertTriangle size={16} className="text-red-500" />}
            {getTitle()}
          </h3>
          <button onClick={onClose} className="text-zinc-500 hover:text-zinc-300 transition-colors">
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-4">
          <p className="text-sm text-zinc-400 mb-4">{getDescription()}</p>

          {!isDelete && (
            <div className="relative">
              <div className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">
                {isRename ? <Type size={16} /> : <FolderInput size={16} />}
              </div>
              <input
                ref={inputRef}
                type="text"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                    isRename ? "New name" : 
                    isCompress ? "zip" :
                    "Destination path (e.g. /Users/name/Desktop)"
                }
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2 pl-10 pr-3 text-sm text-zinc-200 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 placeholder:text-zinc-600"
              />
              
              {/* Suggestions Dropdown */}
              {showSuggestions && (
                <div className="absolute left-0 right-0 top-full mt-1 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl max-h-48 overflow-y-auto z-50">
                  {suggestions.map((s, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => applySuggestion(s)}
                      className={`w-full text-left px-3 py-2 text-xs flex items-center gap-2 transition-colors ${
                        i === selectedIndex 
                          ? 'bg-indigo-500/20 text-indigo-200' 
                          : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                      }`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${s.type === 'folder' ? 'bg-emerald-500' : 'bg-blue-500'}`} />
                      <span className="truncate">{s.path}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Footer */}
          <div className="flex justify-end gap-2 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 text-xs font-medium text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className={`px-3 py-1.5 text-xs font-medium text-white rounded-md transition-colors flex items-center gap-1.5 ${
                isDelete 
                  ? 'bg-red-600 hover:bg-red-500' 
                  : 'bg-indigo-600 hover:bg-indigo-500'
              }`}
            >
              <Check size={12} />
              {isDelete ? 'Delete' : 'Confirm'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ActionModal;