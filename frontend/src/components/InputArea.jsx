import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Folder, File, Zap, Keyboard } from 'lucide-react';

const InputArea = ({ onSend, disabled, onSuggestionSelected }) => {
  const [triggerText, setTriggerText] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [autocompleteEnabled, setAutocompleteEnabled] = useState(true);
  
  const editorRef = useRef(null);
  const lastContextRef = useRef(null);

  useEffect(() => {
    const fetchSuggestions = async () => {
      if (autocompleteEnabled && triggerText.trim().length > 0 && window.eel) {
        try {
          const results = await window.eel.get_suggestions(triggerText)();
          setSuggestions(results);
          setShowSuggestions(results.length > 0);
          setSelectedIndex(0);
          
          if (results.length > 0) {
            lastContextRef.current = results[0];
            if (onSuggestionSelected) onSuggestionSelected(results[0]);
          } else {
             lastContextRef.current = null;
             if (onSuggestionSelected) onSuggestionSelected(null);
          }
        } catch (e) {
          console.error("Failed to fetch suggestions", e);
        }
      } else {
        setShowSuggestions(false);
        if (triggerText.trim().length === 0) {
            lastContextRef.current = null;
            if (onSuggestionSelected) onSuggestionSelected(null);
        }
      }
    };

    const debounce = setTimeout(fetchSuggestions, 200);
    return () => clearTimeout(debounce);
  }, [triggerText, onSuggestionSelected, autocompleteEnabled]);

  const handleInput = () => {
    const selection = window.getSelection();
    if (!selection.rangeCount) return;
    
    const node = selection.focusNode;
    if (node.nodeType === Node.TEXT_NODE) {
      const textUpToCursor = node.textContent.slice(0, selection.focusOffset);
      
      // Check for preceding chip to build context
      let effectiveText = textUpToCursor;
      
      // If we are at the start of the text node, or the text before cursor is just non-space chars
      // we might be continuing a path from a previous chip.
      if (!textUpToCursor.startsWith(' ') && !textUpToCursor.startsWith('\u00A0')) {
          let prev = node.previousSibling;
          if (prev && prev.nodeType === Node.ELEMENT_NODE && prev.hasAttribute('data-full-path')) {
              const path = prev.getAttribute('data-full-path');
              effectiveText = path + textUpToCursor;
          }
      }
      
      setTriggerText(effectiveText);
    } else {
      setTriggerText("");
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (showSuggestions && suggestions.length > 0) {
        applySuggestion(suggestions[selectedIndex]);
      } else if (!disabled) {
        handleSend();
      }
    } else if (e.key === 'ArrowDown') {
      if (showSuggestions) {
        e.preventDefault();
        const newIndex = (selectedIndex + 1) % suggestions.length;
        setSelectedIndex(newIndex);
        lastContextRef.current = suggestions[newIndex];
        if (onSuggestionSelected) onSuggestionSelected(suggestions[newIndex]);
      }
    } else if (e.key === 'ArrowUp') {
      if (showSuggestions) {
        e.preventDefault();
        const newIndex = (selectedIndex - 1 + suggestions.length) % suggestions.length;
        setSelectedIndex(newIndex);
        lastContextRef.current = suggestions[newIndex];
        if (onSuggestionSelected) onSuggestionSelected(suggestions[newIndex]);
      }
    } else if (e.key === 'Tab') {
      if (showSuggestions && suggestions.length > 0) {
        e.preventDefault();
        applySuggestion(suggestions[selectedIndex]);
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      setShowSuggestions(false);
    }
  };

  const applySuggestion = (suggestion) => {
    const selection = window.getSelection();
    if (!selection.rangeCount) return;
    
    const range = selection.getRangeAt(0);
    const node = range.startContainer;
    
    if (node.nodeType === Node.TEXT_NODE) {
      const textBefore = node.textContent.slice(0, range.startOffset);
      const textAfter = node.textContent.slice(range.startOffset);
      
      // Find word start
      const lastSpaceIndex = textBefore.lastIndexOf(' ');
      const lastNbspIndex = textBefore.lastIndexOf('\u00A0');
      const splitIndex = Math.max(lastSpaceIndex, lastNbspIndex);
      
      const startOfWord = splitIndex + 1;
      
      // Find word end
      const firstSpaceAfter = textAfter.search(/[\s\u00A0]/);
      const endOfWord = firstSpaceAfter === -1 ? node.textContent.length : range.startOffset + firstSpaceAfter;
      
      // Create Chip
      const chip = document.createElement('span');
      chip.contentEditable = "false";
      
      let colorClasses = "bg-blue-500/20 text-blue-300 border-blue-500/30 hover:bg-blue-500/30"; // Default file
      if (suggestion.type === 'action') colorClasses = "bg-amber-500/20 text-amber-300 border-amber-500/30 hover:bg-amber-500/30";
      if (suggestion.type === 'folder') colorClasses = "bg-emerald-500/20 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/30";

      chip.className = `inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-mono mx-0.5 align-middle select-none cursor-pointer transition-colors border ${colorClasses}`;
      
      chip.title = suggestion.path || suggestion.text;
      chip.setAttribute('data-full-path', suggestion.path || suggestion.text);
      chip.setAttribute('data-type', suggestion.type);
      chip.textContent = suggestion.text;
      
      // Add click handler for preview
      chip.onclick = (e) => {
          e.stopPropagation();
          // We need to reconstruct the suggestion object or pass the original one
          // Since we are in a closure, 'suggestion' is available here!
          if (onSuggestionSelected) onSuggestionSelected(suggestion);
      };
      
      // Create Space
      const space = document.createTextNode('\u00A0');
      
      // Replace text
      range.setStart(node, startOfWord);
      range.setEnd(node, endOfWord);
      range.deleteContents();
      
      range.insertNode(space);
      range.insertNode(chip);
      
      // Move cursor after space
      range.setStartAfter(space);
      range.setEndAfter(space);
      selection.removeAllRanges();
      selection.addRange(range);
      
      setTriggerText("");
      setShowSuggestions(false);
      
      lastContextRef.current = suggestion;
      if (onSuggestionSelected) onSuggestionSelected(suggestion);
      
      editorRef.current.focus();
    }
  };

  const handleSend = () => {
    if (!editorRef.current) return;
    
    let backendText = "";
    let displaySegments = [];
    
    editorRef.current.childNodes.forEach(node => {
      if (node.nodeType === Node.TEXT_NODE) {
        const text = node.textContent;
        backendText += text;
        displaySegments.push({ type: 'text', text: text });
      } else if (node.nodeType === Node.ELEMENT_NODE) {
        if (node.hasAttribute('data-full-path')) {
          const path = node.getAttribute('data-full-path');
          const text = node.textContent;
          const chipType = node.getAttribute('data-type') || 'file';
          
          backendText += path;
          displaySegments.push({ type: 'chip', text: text, path: path, chipType: chipType });
        } else {
          const text = node.innerText;
          backendText += text;
          displaySegments.push({ type: 'text', text: text });
        }
      }
    });
    
    if (backendText.trim()) {
      // Pass both the raw text for backend and the segments for UI
      onSend(backendText, displaySegments);
      editorRef.current.innerHTML = "";
      setTriggerText("");
    }
  };

  return (
    <div className="p-4 pt-2 relative">
      {showSuggestions && !disabled && autocompleteEnabled && (
        <div className="absolute bottom-full left-4 right-4 mb-2 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl overflow-hidden z-10 max-h-60 overflow-y-auto">
          <div className="px-3 py-2 text-[10px] font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-900/50 border-b border-zinc-800 flex justify-between items-center">
            <span>Suggestions</span>
            <span className="text-[9px] text-zinc-600">Tab to select</span>
          </div>
          <ul>
            {suggestions.map((s, i) => (
              <li key={i} 
                  className={`px-3 py-2.5 flex items-center gap-3 cursor-pointer text-sm transition-all border-l-2 ${
                    i === selectedIndex 
                      ? 'bg-zinc-800/80 border-indigo-500' 
                      : 'border-transparent hover:bg-zinc-800/50'
                  }`}
                  onClick={() => applySuggestion(s)}
              >
                <div className={`w-6 h-6 rounded flex items-center justify-center shrink-0 ${
                  s.type === 'action' ? 'bg-amber-500/10 text-amber-500' :
                  s.type === 'folder' ? 'bg-blue-500/10 text-blue-400' :
                  'bg-zinc-700/30 text-zinc-400'
                }`}>
                  {s.type === 'action' && <Zap size={14} />}
                  {s.type === 'folder' && <Folder size={14} />}
                  {s.type === 'file' && <File size={14} />}
                </div>

                <div className="flex flex-col min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className={`font-medium truncate ${i === selectedIndex ? 'text-zinc-200' : 'text-zinc-400'}`}>
                      {s.text}
                    </span>
                    {s.type === 'action' && (
                      <span className="text-[10px] font-bold uppercase tracking-wider text-amber-500/50 bg-amber-500/5 px-1.5 py-0.5 rounded">
                        CMD
                      </span>
                    )}
                  </div>
                  
                  {s.path && (
                    <span className="text-[10px] text-zinc-600 truncate font-mono">
                      {s.path}
                    </span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className={`relative bg-zinc-900 border border-zinc-800 rounded-xl shadow-sm transition-all flex flex-col ${disabled ? 'opacity-50 cursor-not-allowed' : 'focus-within:ring-1 focus-within:ring-indigo-500/50 focus-within:border-indigo-500/50'}`}>
        
        <div
          ref={editorRef}
          contentEditable={!disabled}
          onInput={handleInput}
          onKeyDown={handleKeyDown}
          onClick={() => setShowSuggestions(false)}
          className="w-full bg-transparent text-zinc-200 text-sm p-3 pr-28 leading-6 outline-none min-h-[52px] max-h-32 overflow-y-auto whitespace-pre-wrap break-words empty:before:content-[attr(placeholder)] empty:before:text-zinc-600"
          placeholder={disabled ? "Waiting for confirmation..." : "Ask OS Assistant..."}
          role="textbox"
        />
        
        <div className="absolute right-2 bottom-2 flex items-center gap-1 bg-zinc-900 pl-2">
          <button 
            onClick={() => setAutocompleteEnabled(!autocompleteEnabled)}
            className={`p-1.5 rounded-lg transition-colors ${autocompleteEnabled ? 'text-indigo-400 bg-indigo-500/10' : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800'}`}
            title={autocompleteEnabled ? "Disable Autocomplete" : "Enable Autocomplete"}
          >
            <Keyboard size={16} />
          </button>
          <button disabled={disabled} className="p-1.5 text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800 rounded-lg transition-colors disabled:opacity-50">
            <Paperclip size={16} />
          </button>
          <button 
            disabled={disabled}
            onClick={handleSend}
            className={`p-1.5 rounded-lg transition-all ${triggerText.trim() || (editorRef.current && editorRef.current.innerText.trim()) ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/20' : 'bg-zinc-800 text-zinc-600'} disabled:opacity-50`}
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default InputArea;
