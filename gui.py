import sys
import os
import eel
import threading
import subprocess
import base64
import mimetypes
import pypdf

# Add the current directory to Python path
sys.path.append(".")

try:
    from src.backend.core.assistant import OSAssistant
    from src.backend.utils.logger import AuditLogger
except ImportError:
    # Fallback
    sys.path.append(os.getcwd())
    from src.backend.core.assistant import OSAssistant
    from src.backend.utils.logger import AuditLogger

# Initialize Components
print("--- Initializing OS Assistant GUI ---")
try:
    assistant = OSAssistant()
    logger = AuditLogger()
    print("--- System Ready ---")
except Exception as e:
    print(f"Initialization Failed: {e}")
    sys.exit(1)

# Initialize Eel
# Point to the frontend build directory
# Note: You must run 'npm run build' in the frontend folder first!
eel.init('frontend/dist')

@eel.expose
def process_user_input(user_input):
    """
    Bridge function: Frontend calls this with user text.
    Starts a background thread to process the request to avoid blocking the UI.
    """
    print(f"Received input: {user_input}")
    
    if not user_input:
        eel.handle_response({"status": "ERROR", "message": "Empty input"})
        return

    def run_backend():
        try:
            # Call the backend core
            response = assistant.process_request(user_input)
            
            # Log the intent if available
            intent = response.get('intent', {})
            status = response.get('status')
            message = response.get('message')
            
            # Handle Confirmation
            if status == 'NEEDS_CONFIRMATION':
                # Pass the full response (including action_id, risk, etc.) to the frontend
                eel.handle_response(response)
                return
            
            if status == 'SUCCESS':
                logger.log_action(user_input, intent, message)
            elif status == 'BLOCKED':
                logger.log_action(user_input, intent, f"BLOCKED: {message}")
            elif status == 'ERROR':
                logger.log_action(user_input, intent, f"Error: {message}")
                
            eel.handle_response(response)

        except Exception as e:
            eel.handle_response({"status": "ERROR", "message": str(e)})

    # Start the thread
    threading.Thread(target=run_backend, daemon=True).start()
    return "Processing started..."

@eel.expose
def execute_confirmed_action(action_id, updated_batch_targets=None):
    """
    Called when user clicks 'Confirm' in the UI.
    """
    print(f"Executing confirmed action: {action_id}")
    try:
        result = assistant.execute_confirmed_action(action_id, updated_batch_targets)
        
        # Log the success
        # Note: We'd ideally want the original intent here for logging, 
        # but the assistant handles the execution. 
        # We can log a generic confirmation message.
        logger.log_action("User Confirmed Action", {"action_id": action_id}, result.get('message'))
        
        return result
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

@eel.expose
def cancel_action(action_id):
    """
    Called when user clicks 'Cancel'.
    """
    print(f"Cancelled action: {action_id}")
    # We can just log this
    logger.log_action("User Cancelled Action", {"action_id": action_id}, "Cancelled by user")
    return {"status": "CANCELLED", "message": "Action cancelled."}

@eel.expose
def get_system_stats():
    """
    Returns system stats for the UI sidebar/status bar.
    """
    return assistant.sys_info.get_system_specs()

@eel.expose
def get_file_preview(path):
    """
    Returns the content of a file for preview.
    Supports images (base64) and text files.
    """
    if not path or not os.path.exists(path):
        return {"type": "error", "content": "File not found"}
    
    if os.path.isdir(path):
        try:
            items = os.listdir(path)[:20]
            return {"type": "list", "content": items}
        except Exception as e:
            return {"type": "error", "content": str(e)}

    mime_type, _ = mimetypes.guess_type(path)
    
    try:
        # PDF - Extract Text Content
        if mime_type == 'application/pdf' or path.lower().endswith('.pdf'):
             if os.path.getsize(path) > 10 * 1024 * 1024: # 10MB limit
                return {"type": "error", "content": "PDF too large to preview"}
             
             try:
                 reader = pypdf.PdfReader(path)
                 text_content = ""
                 # Extract text from first 5 pages to avoid huge payloads
                 for i, page in enumerate(reader.pages[:5]):
                     text_content += f"--- Page {i+1} ---\n"
                     text_content += page.extract_text() + "\n\n"
                 
                 if len(reader.pages) > 5:
                     text_content += f"\n... ({len(reader.pages) - 5} more pages truncated)"
                     
                 if not text_content.strip():
                     # Fallback to binary message if no text found (e.g. scanned image)
                     return {"type": "text", "content": "[PDF contains no extractable text (Scanned/Image)]"}
                     
                 return {"type": "text", "content": text_content}
             except Exception as e:
                 return {"type": "error", "content": f"Failed to extract PDF text: {str(e)}"}

        # Image
        if mime_type and mime_type.startswith('image'):
            # Limit image size check could be good here, but for now just read
            if os.path.getsize(path) > 5 * 1024 * 1024: # 5MB limit
                return {"type": "error", "content": "Image too large to preview"}
                
            with open(path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
                return {"type": "image", "content": f"data:{mime_type};base64,{encoded}"}
        
        # Text (default fallback)
        try:
            if os.path.getsize(path) > 1024 * 1024: # 1MB limit for text
                 return {"type": "text", "content": "File too large to preview."}

            with open(path, "r", encoding="utf-8") as f:
                content = f.read(2000) # Read first 2000 chars
                if len(content) == 2000:
                    content += "\n... (truncated)"
                return {"type": "text", "content": content}
        except UnicodeDecodeError:
            return {"type": "binary", "content": "Binary file - No preview available"}
            
    except Exception as e:
        return {"type": "error", "content": str(e)}

@eel.expose
def get_suggestions(query):
    """
    Returns a list of suggestions based on the user's query.
    """
    suggestions = []
    
    # 1. Action Suggestions
    actions = ["open", "close", "move", "copy", "delete", "rename", "create", "list", "read"]
    
    parts = query.split()
    if not parts:
        return []

    # Check if we are currently typing a word or have just finished one
    ends_with_space = query.endswith(" ")
    
    # Only suggest actions if we are on the first word and NOT ending with space
    if len(parts) == 1 and not ends_with_space:
        first_word = parts[0].lower()
        for action in actions:
            if action.startswith(first_word):
                suggestions.append({"text": action, "type": "action"})
            
    # 2. File/Folder Suggestions
    # Determine the target string to complete
    if ends_with_space:
        # User typed a space, waiting for next token. 
        # We could suggest CWD content here, but user requested box to close.
        return suggestions
    else:
        target = parts[-1]
    
    if not target:
        return suggestions[:10]

    # Strategy A: Path Navigation (if it looks like a path)
    if "/" in target or "~" in target:
        # Resolve ~ to home
        path_query = os.path.expanduser(target) if target.startswith("~") else target
        
        search_dirs = []
        partial = ""

        if os.path.isabs(path_query):
            # Absolute path
            if os.path.isdir(path_query):
                search_dirs = [path_query]
                partial = ""
            else:
                search_dirs = [os.path.dirname(path_query)]
                partial = os.path.basename(path_query)
        else:
            # Relative path - search in CWD, Home, and Root
            # Handle trailing slash for directories
            if path_query.endswith(os.sep):
                dirname = path_query.rstrip(os.sep)
                partial = ""
            else:
                dirname = os.path.dirname(path_query)
                partial = os.path.basename(path_query)
            
            roots = [os.getcwd(), os.path.expanduser("~"), "/"]
            for root in roots:
                if dirname:
                    candidate = os.path.join(root, dirname)
                else:
                    candidate = root
                
                if os.path.exists(candidate) and os.path.isdir(candidate):
                    search_dirs.append(candidate)

        # Collect suggestions
        seen_paths = set()
        for directory in search_dirs:
            if not directory: continue
            try:
                for item in os.listdir(directory):
                    if item.lower().startswith(partial.lower()) and not item.startswith("."):
                        full_path = os.path.join(directory, item)
                        if full_path in seen_paths:
                            continue
                        seen_paths.add(full_path)
                        
                        is_dir = os.path.isdir(full_path)
                        suggestions.append({
                            "text": item, 
                            "type": "folder" if is_dir else "file",
                            "path": full_path
                        })
            except (PermissionError, OSError):
                pass

    # Strategy B: Global Search (Spotlight/mdfind)
    # Only if it doesn't look like a path and has enough chars
    elif len(target) >= 3:
        try:
            # mdfind -name "target"
            # We use -name to match the filename, not content
            cmd = ['mdfind', '-name', target]
            
            # Run with timeout to prevent hanging
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=0.5)
            
            paths = result.stdout.splitlines()
            
            # Filter and limit results
            count = 0
            for p in paths:
                if count >= 15: break
                
                name = os.path.basename(p)
                # Strict check: target must be in name
                if target.lower() in name.lower():
                    # Skip hidden files or system files if desired, but for now keep them
                    if name.startswith('.'): continue
                    
                    is_dir = os.path.isdir(p)
                    suggestions.append({
                        "text": name,
                        "type": "folder" if is_dir else "file",
                        "path": p
                    })
                    count += 1
                    
        except Exception as e:
            print(f"Search error: {e}")

    # Sort suggestions
    # Priority:
    # 1. Actions (already at top if matched)
    # 2. Exact match (case insensitive)
    # 3. Starts with
    # 4. Others
    
    def sort_key(s):
        text = s['text'].lower()
        q = target.lower() if target else ""
        
        score = 0
        if s['type'] == 'action':
            score += 100
        
        if text == q:
            score += 50
        elif text.startswith(q):
            score += 25
            
        # Prefer folders?
        if s['type'] == 'folder':
            score += 5
            
        return -score # Descending

    suggestions.sort(key=sort_key)

    return suggestions[:20] # Limit total suggestions

@eel.expose
def perform_manual_action(action, params):
    """
    Directly executes a file operation without LLM parsing.
    Used for context menu actions like Move, Copy, Rename, etc.
    """
    print(f"Manual Action: {action} with {params}")
    
    # Construct intent dictionary expected by _run_single_tool
    intent = {
        'action': action,
        'resolved_src': params.get('source'),
        'resolved_path': params.get('source'), # Some tools use path, some src
        'resolved_dst': params.get('destination'),
        'new_name': params.get('new_name'),
        'format': params.get('format'),
        # For specific tools that might look for other keys
        'src': params.get('source'),
        'dst': params.get('destination')
    }
    
    try:
        # Execute directly using the assistant's internal method
        # We use _run_execution to ensure it gets logged to short_term_memory
        result = assistant._run_execution(intent)
        
        # Log to audit logger as well
        logger.log_action(f"Manual: {action}", intent, result)
        
        return {"status": "SUCCESS", "message": result}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def start_app():
    # Start the app
    # If you are developing, you might want to use:
    # eel.start({'port': 5173}, host='localhost', port=8080, mode='chrome')
    # But for production (serving 'dist'):
    try:
        eel.start('index.html', size=(900, 650), port=0)
    except (SystemExit, MemoryError, KeyboardInterrupt):
        # Handle clean exit
        print("Exiting...")
        sys.exit(0)

if __name__ == "__main__":
    start_app()
