# 🐝 AgencyHive AI Studio

A powerful macOS application for creating and managing AI agent crews - no coding required! Based on the excellent [CrewAI Studio](https://github.com/strnad/CrewAI-Studio) by strnad.

## ✨ Features

- 🤖 Build AI agent crews through an intuitive interface
- 🔧 Rich toolkit including API calls, file operations, and web scraping
- 🔌 Support for OpenAI, Groq, Anthropic and LM Studio
- 📱 Export crews as standalone apps
- ⚡️ Background processing with stop capability
- 🎯 Perfect for non-developers who want to harness AI agents

## 🖼️ Preview

![Crew Definition](https://raw.githubusercontent.com/strnad/CrewAI-Studio/main/img/crews.png)
![Crew Execution](https://raw.githubusercontent.com/strnad/CrewAI-Studio/main/img/kickoff.png)

## 🚀 Quick Start for macOS

1. **Download & Install**

```bash
# Clone the repository
git clone https://github.com/strnad/CrewAI-Studio.git
cd CrewAI-Studio

# Install dependencies
./install_venv.sh
```

2. **Launch**

```bash
./run_venv.sh
```

That's it! The app will open in your default browser.

## ⚙️ Configuration

Create a `.env` file with your API keys:

```env
OPENAI_API_KEY="your-key"    # Required for many features
GROQ_API_KEY="your-key"      # Optional
ANTHROPIC_API_KEY="your-key" # Optional
LMSTUDIO_API_BASE="http://localhost:1234/v1" # Optional, for LM Studio
OLLAMA_HOST="http://localhost:11434/api"    # Optional, for Ollama
OLLAMA_MODELS="llama2,mistral"             # Optional, comma-separated list of models
```

## 🆘 Need Help?

If you run into issues:
1. Remove the `venv` folder and reinstall
2. Back up and rename `crewai.db` if upgrading versions
3. Open an issue in our GitHub repository

## 🙏 Acknowledgments

AgencyHive AI Studio is powered by [CrewAI Studio](https://github.com/strnad/CrewAI-Studio). Special thanks to strnad for creating the original codebase that made this possible.