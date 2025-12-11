# 🤖 OS Assistant (Backend Core)

**OS Assistant** is a secure, intelligent, natural-language interface for your operating system. It translates human intent into precise system operations, allowing you to manage files, monitor system health, and control applications using plain English.

Unlike standard scripts, it features a robust **Security Layer** (Guard) that prevents accidental data loss and handles race conditions, making it safe for daily use.

---

## ✨ Key Features

### 🧠 Intelligent Core
* **Natural Language Processing:** Powered by local LLMs (Llama 3 via Ollama) to understand complex instructions.
* **Context Awareness:** Remembers previous actions and answers questions about system history.
* **Smart Parsing:** Converts fuzzy terms like "last week" or "huge files" into precise dates and byte sizes.

### 🛡️ Active Security Layer (The Guard)
* **Risk Assessment:** Every tool has a risk level (Safe, Moderate, High).
* **Confirmation Loop:** High-risk actions (e.g., `delete_file`, `move_file`) trigger an interactive confirmation prompt.
* **Path Protection:** Blocks operations on critical system directories (`/System`, `C:\Windows`, `/bin`).
* **Race Condition Handling (TOCTOU):** Verifies file existence *milliseconds* before execution to prevent errors if the state changes during confirmation.
* **Safe Deletion:** Uses the Recycle Bin/Trash instead of permanent deletion.

### 🔍 Advanced Filtering Engine
* **Batch Operations:** Operate on hundreds of files at once.
* **Metadata Filtering:** Select files by:
    * **Type:** Extensions (`jpg`, `png`) or categories.
    * **Size:** Constraints (`> 50MB`, `< 10kb`).
    * **Time:** Creation or Modification dates (`before 2024`, `last week`).

### ⚡ System Operations
* **App Control:** Open and close applications.
* **System Settings:** Access control panels and settings directly.
* **Hardware Monitor:** Check RAM usage, CPU load, and Disk space in real-time.

---

## 🏗️ Architecture

The system follows a strict "Brain-Guard-Hands" architecture:

1.  **The Brain (`Client.py`)**: Translates user input into a JSON Intent.
2.  **The Orchestrator (`assistant.py`)**: Resolves paths and routes the intent.
3.  **The Guard (`safety.py`)**: Validates the action against safety rules.
4.  **The Hands (`tools/`)**: Executes the actual Python logic on the OS.

---

## 🖥️ User Interface

A modern web-based UI is available, powered by Streamlit.

### Prerequisites
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the UI
Run the following command in your terminal:
```bash
streamlit run app.py
```

The interface provides:
- **Chat Interface:** Interact with the assistant naturally.
- **System Sidebar:** View real-time system specs and disk usage.
- **Interactive Confirmations:** Safe, button-based confirmation for high-risk actions.