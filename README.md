# 🤖 Self-Improving Coding Agent

A sophisticated AI coding agent that autonomously writes, tests, debugs, and learns from its experiences. Built with LangGraph, ChromaDB, and Streamlit.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Built following the phase-by-phase implementation plan for autonomous AI agents**

## 🌟 Features

- **Autonomous Code Generation**: Writes production-ready Python code with unit tests
- **Self-Debugging**: Automatically detects and fixes errors through reflection
- **Learning Memory**: Learns from past successes and failures using vector embeddings
- **Safety-First**: Static code analysis prevents dangerous operations
- **Human-in-the-Loop**: Requests approval for potentially risky code
- **Isolated Execution**: Runs code safely in Docker containers with resource limits
- **Real-Time UI**: Beautiful Streamlit interface with live execution streaming

## 🏗️ Architecture

The agent follows a sophisticated cognitive loop:

```
User Goal → Memory Retrieval → Planning → Coding → Safety Check → Execution
                                              ↑                        ↓
                                              ←── Reflection ←── Failed?
                                                                      ↓
                                                                  Success → Save to Memory
```

### Components

1. **Agent Module** (`agent/`)
   - `state.py`: State management for the agent loop
   - `graph.py`: LangGraph orchestration and routing logic
   - `nodes.py`: Cognitive functions (Planner, Coder, Reflector)
   - `prompts.py`: System prompts for each cognitive module

2. **Sandbox Module** (`sandbox/`)
   - `safety.py`: AST-based static code analysis
   - `executor.py`: Docker-based isolated code execution

3. **Memory Module** (`memory/`)
   - `vector_store.py`: ChromaDB vector database management
   - `memory_manager.py`: High-level memory operations

4. **Frontend** (`main.py`)
   - Streamlit UI with real-time streaming
   - Human approval workflow
   - Memory statistics and management

## 📋 Prerequisites

- Python 3.11+
- Docker Desktop (running)
- Google API key (recommended - free tier available) OR OpenAI API key OR Anthropic API key

## 🚀 Installation

1. **Clone the repository**
   ```bash
   cd self-improving-coding-agent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Edit the `.env` file and add your API key:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here  # Recommended - Free tier available!
   # OR
   OPENAI_API_KEY=your_openai_api_key_here
   # OR
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```
   
   **Get a free Google API key**: Visit [Google AI Studio](https://aistudio.google.com/apikey)

5. **Ensure Docker is running**
   ```bash
   docker ps
   ```
   If this fails, start Docker Desktop.

## 🎮 Usage

### Running the Streamlit UI

```bash
streamlit run main.py
```

The UI will open in your browser at `http://localhost:8501`.

### Using the Agent

1. Enter your coding goal in the text area (e.g., "Write a function to sort a list using quicksort with unit tests")
2. Click "🚀 Start Agent"
3. Watch as the agent:
   - Retrieves similar past successes from memory
   - Creates an implementation plan
   - Writes code with tests
   - Executes in a safe Docker container
   - Debugs and fixes errors automatically
   - Saves successful solutions to memory

### Safety Approvals

If the agent attempts to use restricted operations (like file I/O or network access), it will pause and request your approval. You can:
- **Approve**: Allow the operation to proceed
- **Deny**: Force the agent to find an alternative approach

## 🧠 How It Learns

### Success Memory
When the agent successfully completes a task, it saves:
- The user's goal
- The working code

Future similar tasks will retrieve these examples to inform planning.

### Failure Memory
When the agent fixes a bug, it saves:
- The error logs
- The reflection/solution

Future similar errors will retrieve these solutions to speed up debugging.

## 🔧 Configuration

Edit `.env` to customize:

```env
# Maximum retry attempts before giving up
MAX_ITERATIONS=10

# Docker execution timeout (seconds)
DOCKER_TIMEOUT=10

# Docker memory limit
DOCKER_MEMORY_LIMIT=256m

# Database paths
CHROMA_DB_PATH=./chroma_db
SQLITE_DB_PATH=./agent_state.db
```

## 📊 Memory Management

The UI sidebar provides controls to:
- View memory statistics (success/failure counts)
- Clear success memory
- Clear failure memory
- Clear all memory

## 🛡️ Safety Features

### Static Analysis
The safety analyzer checks for:
- Forbidden imports (`os`, `subprocess`, `sys`, etc.)
- Dangerous builtins (`eval`, `exec`, `open`, etc.)
- Risky attribute access (`__dict__`, `__class__`, etc.)

### Docker Isolation
All code executes in containers with:
- 10-second timeout
- 256MB memory limit
- No network access
- Only workspace directory mounted

## 🧪 Example Goals

Try these example goals:

1. **Simple Algorithm**
   ```
   Write a function to calculate the nth Fibonacci number using memoization with unit tests
   ```

2. **Data Structure**
   ```
   Implement a binary search tree with insert, search, and delete methods with comprehensive tests
   ```

3. **String Processing**
   ```
   Create a function that validates email addresses using regex with edge case tests
   ```

4. **Math Problem**
   ```
   Write a function to find all prime numbers up to n using the Sieve of Eratosthenes with tests
   ```

## 🔍 Troubleshooting

### Docker Issues
- **Error: "Cannot connect to Docker daemon"**
  - Solution: Ensure Docker Desktop is running
  - Run: `docker ps` to verify

### API Key Issues
- **Error: "Invalid API key"**
  - Solution: Check your `.env` file has the correct key
  - Ensure no extra spaces or quotes around the key

### Memory Issues
- **Agent seems slow or unresponsive**
  - Solution: Clear the memory databases
  - Click "Clear All Memory" in the sidebar

### Execution Timeout
- **Code times out during execution**
  - Solution: Increase `DOCKER_TIMEOUT` in `.env`
  - Consider optimizing the generated code

## 📁 Project Structure

```
self-improving-coding-agent/
├── agent/
│   ├── __init__.py
│   ├── state.py          # State management
│   ├── graph.py          # LangGraph orchestration
│   ├── nodes.py          # Cognitive functions
│   └── prompts.py        # System prompts
├── sandbox/
│   ├── __init__.py
│   ├── safety.py         # Static code analysis
│   └── executor.py       # Docker execution
├── memory/
│   ├── __init__.py
│   ├── vector_store.py   # ChromaDB management
│   └── memory_manager.py # Memory operations
├── workspace/            # Ephemeral execution folder
├── .env                  # Configuration
├── .gitignore
├── requirements.txt
├── main.py              # Streamlit UI
└── README.md
```

## 🤝 Contributing

This is a tutorial project, but feel free to:
- Report bugs
- Suggest improvements
- Fork and extend

## 📝 License

MIT License - Feel free to use this project for learning and development.

## 🙏 Acknowledgments

Built with:
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent orchestration
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Streamlit](https://streamlit.io/) - Web UI
- [Docker](https://www.docker.com/) - Code isolation
- [OpenAI GPT-4](https://openai.com/) - Language model

## 📚 Learn More

This project demonstrates:
- LangGraph state machines
- Vector embeddings for memory
- Docker containerization
- Static code analysis with AST
- Streamlit real-time streaming
- Human-in-the-loop AI systems

Perfect for learning about autonomous AI agents!
