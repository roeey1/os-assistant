import React, { useState, useEffect } from 'react';
import { PanelRightClose, PanelRightOpen } from 'lucide-react';
import MessageList from './components/MessageList';
import InputArea from './components/InputArea';
import ContextPane from './components/ContextPane';
import StatusBar from './components/StatusBar';
import ContextMenu from './components/ContextMenu';
import ActionModal from './components/ActionModal';

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your OS Assistant. How can I help you today?' }
  ]);
  const [status, setStatus] = useState("Ready");
  const [pendingConfirmation, setPendingConfirmation] = useState(null);
  const [selectedContext, setSelectedContext] = useState(null);
  const [showPreview, setShowPreview] = useState(true);
  
  // Context Menu State
  const [contextMenu, setContextMenu] = useState(null); // { x, y, item }
  const [actionModal, setActionModal] = useState({ isOpen: false, type: null, item: null });

  // Expose handleResponse to Python
  useEffect(() => {
    if (window.eel) {
      window.eel.expose(handleResponse, 'handle_response');
    }
  }, []);

  // Update cache when files are moved/renamed
  const updateFileCache = (oldPath, newPath) => {
      if (!oldPath || !newPath) return;
      
      // 1. Update LocalStorage History
      const history = JSON.parse(localStorage.getItem('os_assistant_history') || '[]');
      let updated = false;
      const newHistory = history.map(h => {
          if (h.path === oldPath) {
              updated = true;
              // Update path and text if text was the filename
              const oldName = oldPath.split(/[/\\]/).pop();
              const newName = newPath.split(/[/\\]/).pop();
              return { 
                  ...h, 
                  path: newPath,
                  text: h.text === oldName ? newName : h.text
              };
          }
          return h;
      });
      
      if (updated) {
          localStorage.setItem('os_assistant_history', JSON.stringify(newHistory));
      }
      
      // 2. Update Chat Messages (Chips)
      // This is tricky because messages contain HTML/Components. 
      // We need to update the 'content' array if it has chips.
      setMessages(prevMessages => prevMessages.map(msg => {
          if (Array.isArray(msg.content)) {
              const newContent = msg.content.map(segment => {
                  if (segment.type === 'chip' && segment.path === oldPath) {
                      const oldName = oldPath.split(/[/\\]/).pop();
                      const newName = newPath.split(/[/\\]/).pop();
                      return {
                          ...segment,
                          path: newPath,
                          text: segment.text === oldName ? newName : segment.text
                      };
                  }
                  return segment;
              });
              return { ...msg, content: newContent };
          }
          return msg;
      }));
  };

  const handleSend = async (text, displaySegments = null) => {
    // Add user message - use displaySegments if available, otherwise text
    setMessages(prev => [...prev, { role: 'user', content: displaySegments || text }]);
    setStatus("Processing");

    // Try to find a path in the user input to update context immediately
    // Matches paths starting with / or ~/ or ./
    const pathMatch = text.match(/(\/[\w\-. \/]+)|(~\/[\w\-. \/]+)|(\.\/[\w\-. \/]+)/);
    if (pathMatch) {
        const path = pathMatch[0].trim();
        const name = path.split(/[/\\]/).pop();
        setSelectedContext({
            text: name,
            type: path.includes('.') ? 'file' : 'folder',
            path: path
        });
    }

    try {
      if (window.eel) {
        // We don't await the result anymore, we wait for the callback
        window.eel.process_user_input(text);
      } else {
        // Fallback for UI testing
        console.warn("Eel not found. Mocking response.");
        setTimeout(() => {
            setMessages(prev => [...prev, { role: 'assistant', content: "Eel backend not connected. (Dev Mode)" }]);
            setStatus("Ready");
        }, 500);
      }
    } catch (error) {
      console.error("Eel Error:", error);
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${error.message}` }]);
      setStatus("Error");
    }
  };

  const handleChipClick = (chip) => {
      setSelectedContext({
          text: chip.text,
          type: chip.chipType || (chip.path.includes('.') ? 'file' : 'folder'),
          path: chip.path
      });
  };

  const handleChipContextMenu = (e, chip) => {
      e.preventDefault();
      setContextMenu({
          x: e.clientX,
          y: e.clientY,
          item: chip
      });
  };

  const handleContextMenuAction = (action, item) => {
      setContextMenu(null);
      
      if (action === 'copy_path') {
          navigator.clipboard.writeText(item.path);
          // Optional: Show toast
          return;
      }

      // Manual Actions that require Modal
      if (['move_file', 'copy_file', 'rename_item', 'create_symlink', 'delete_file', 'compress_item'].includes(action)) {
          setActionModal({
              isOpen: true,
              type: action,
              item: item
          });
          return;
      }

      // Direct Manual Actions (No Modal)
      if (['get_file_info', 'read_file', 'count_lines', 'get_file_hash'].includes(action)) {
          handleManualAction(action, { source: item.path });
          return;
      }

      let command = "";
      if (action === 'open_file') {
          // Use backend tool for opening file
          handleManualAction('open_file', { source: item.path });
          return;
      } else if (action === 'reveal') {
          command = `open folder containing "${item.path}"`;
      }

      if (command) {
          handleSend(command);
      }
  };

  const handleManualAction = async (actionType, params) => {
      // Close modal if open
      setActionModal({ isOpen: false, type: null, item: null });
      
      // Add a message to chat saying we are doing it
      const actionNames = {
          'move_file': 'Moving',
          'copy_file': 'Copying',
          'rename_item': 'Renaming',
          'create_symlink': 'Creating shortcut for',
          'delete_file': 'Deleting',
          'compress_item': 'Compressing',
          'get_file_info': 'Getting info for',
          'read_file': 'Reading',
          'count_lines': 'Counting lines in',
          'get_file_hash': 'Hashing',
          'open_file': 'Opening'
      };
      
      const displayMsg = `${actionNames[actionType] || actionType} ${params.source.split('/').pop()}...`;
      setMessages(prev => [...prev, { role: 'user', content: displayMsg }]);
      setStatus("Executing...");

      try {
          if (window.eel) {
              const result = await window.eel.perform_manual_action(actionType, params)();
              if (result.status === 'SUCCESS') {
                  setMessages(prev => [...prev, { role: 'assistant', content: result.message }]);
              } else {
                  setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${result.message}` }]);
              }
          } else {
              // Mock
              console.log("Mock Manual Action:", actionType, params);
              setTimeout(() => {
                  setMessages(prev => [...prev, { role: 'assistant', content: `[Mock] Successfully executed ${actionType}` }]);
              }, 1000);
          }
      } catch (e) {
          setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${e.message}` }]);
      }
      setStatus("Ready");
  };

  const handleModalConfirm = (inputValue) => {
      const { type, item } = actionModal;
      const params = { source: item.path };
      
      if (type === 'rename_item') {
          params.new_name = inputValue;
      } else if (['move_file', 'copy_file', 'create_symlink'].includes(type)) {
          params.destination = inputValue;
      } else if (type === 'compress_item') {
          params.format = inputValue || 'zip';
      }
      // For delete_file, inputValue is ignored/empty
      
      handleManualAction(type, params);
  };

  const handleFileOperationSuccess = (intent) => {
      if (!intent) return;
      const action = intent.action;
      
      if (action === 'move_file' || action === 'rename_item') {
          // Single file op
          const oldPath = intent.resolved_src || intent.resolved_path;
          let newPath = intent.resolved_dst;
          
          // If rename, newPath might be constructed from new_name
          if (action === 'rename_item' && intent.new_name && oldPath) {
              const sep = oldPath.includes('\\') ? '\\' : '/';
              const dir = oldPath.substring(0, oldPath.lastIndexOf(sep));
              newPath = `${dir}${sep}${intent.new_name}`;
          }
          // If move, check if dst is dir
          else if (action === 'move_file' && oldPath && newPath) {
              const sep = newPath.includes('\\') ? '\\' : '/';
              const oldName = oldPath.split(/[/\\]/).pop();
              
              // Heuristic: Check if newPath looks like a file (has extension)
              const hasExtension = newPath.split(/[/\\]/).pop().includes('.');
              const endsWithSep = newPath.endsWith('/') || newPath.endsWith('\\');
              
              // If it doesn't look like a file (no extension) and doesn't end with the filename
              // assume it's a directory and append the filename
              if (!endsWithSep && !hasExtension && !newPath.endsWith(oldName)) {
                   newPath += sep + oldName;
              }
          }

          if (oldPath && newPath) {
              console.log(`Updating cache: ${oldPath} -> ${newPath}`);
              updateFileCache(oldPath, newPath);
          }
      }
  };

  const handleResponse = (response) => {
    console.log("Received response from Python:", response);
    const { status: respStatus, message, action_id, risk, intent } = response;

    // Update Context Pane based on Intent
    if (intent) {
        const path = intent.resolved_path || intent.path || intent.resolved_src || intent.source || intent.resolved_dst || intent.destination;
        if (path && path !== "NOT FOUND") {
            const name = path.split(/[/\\]/).pop();
            let type = 'file';
            if (intent.action === 'open_app') type = 'app';
            else if (intent.action === 'list' || !name.includes('.')) type = 'folder';
            
            setSelectedContext({
                text: name,
                type: type,
                path: path
            });
        }
    }

    if (respStatus === 'NEEDS_CONFIRMATION') {
      setPendingConfirmation({ action_id, message, risk, intent });
      setStatus("Waiting for Confirmation");
      // Add a special message bubble for confirmation
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: message, 
        isConfirmation: true,
        risk: risk,
        intent: intent
      }]);
    } else {
      // SUCCESS, BLOCKED, or ERROR
      setMessages(prev => [...prev, { role: 'assistant', content: message }]);
      setStatus("Ready");
      
      // Check for file operations to update cache
      if (respStatus === 'SUCCESS' && intent) {
          handleFileOperationSuccess(intent);
      }
    }
  };

  const confirmAction = async (updatedBatchTargets = null) => {
    if (!pendingConfirmation) return;
    setStatus("Executing...");
    
    try {
      if (window.eel) {
        const result = await window.eel.execute_confirmed_action(pendingConfirmation.action_id, updatedBatchTargets)();
        setMessages(prev => [...prev, { role: 'assistant', content: result.message }]);
        
        // Trigger cache update if success
        if (result.status === 'SUCCESS' && result.intent) {
             handleFileOperationSuccess(result.intent);
        }
      }
    } catch (e) {
        setMessages(prev => [...prev, { role: 'assistant', content: "Execution failed." }]);
    }
    
    setPendingConfirmation(null);
    setStatus("Ready");
  };

  const cancelAction = async () => {
    if (!pendingConfirmation) return;
    
    if (window.eel) {
        await window.eel.cancel_action(pendingConfirmation.action_id)();
    }
    
    setMessages(prev => [...prev, { role: 'assistant', content: "Action cancelled." }]);
    setPendingConfirmation(null);
    setStatus("Ready");
  };

  return (
    <div className="w-[850px] h-[600px] bg-zinc-950 rounded-xl border border-zinc-800 shadow-2xl flex flex-col overflow-hidden font-sans text-zinc-100 relative">
      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden relative">
        
        {/* Left Pane: Chat */}
        <div className={`flex flex-col border-r border-zinc-800/50 bg-zinc-950/50 transition-all duration-300 ease-in-out ${showPreview ? 'w-[40%]' : 'w-full'}`}>
          <MessageList 
            messages={messages} 
            pendingConfirmation={pendingConfirmation}
            onConfirm={confirmAction}
            onCancel={cancelAction}
            onChipClick={handleChipClick}
            onChipContextMenu={handleChipContextMenu}
          />
          <InputArea 
            onSend={handleSend} 
            disabled={!!pendingConfirmation} 
            onSuggestionSelected={setSelectedContext}
            onChipContextMenu={handleChipContextMenu}
          />
        </div>

        {/* Right Pane: Context */}
        <div className={`bg-zinc-950 transition-all duration-300 ease-in-out overflow-hidden ${showPreview ? 'w-[60%]' : 'w-0 border-l-0'}`}>
          <ContextPane selectedItem={selectedContext} />
        </div>

        {/* Toggle Preview Button */}
        <button 
            onClick={() => setShowPreview(!showPreview)}
            className="absolute top-4 right-4 z-50 p-1.5 bg-zinc-800/80 hover:bg-zinc-700 text-zinc-400 rounded-md border border-zinc-700/50 shadow-lg backdrop-blur-sm transition-colors"
            title={showPreview ? "Hide Preview" : "Show Preview"}
        >
            {showPreview ? <PanelRightClose size={16} /> : <PanelRightOpen size={16} />}
        </button>

      </div>

      {/* Bottom Toolbar */}
      <StatusBar status={status} />

      {/* Context Menu Overlay */}
      {contextMenu && (
        <ContextMenu 
          x={contextMenu.x} 
          y={contextMenu.y} 
          item={contextMenu.item} 
          onClose={() => setContextMenu(null)}
          onAction={handleContextMenuAction}
        />
      )}

      {/* Action Modal */}
      {actionModal.isOpen && (
        <ActionModal 
          action={actionModal.type}
          item={actionModal.item}
          onClose={() => setActionModal({ ...actionModal, isOpen: false })}
          onConfirm={handleModalConfirm}
        />
      )}
    </div>
  );
}

export default App;
