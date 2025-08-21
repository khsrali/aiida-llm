# verdi-llm

<br>
<div align="left">
  <img src="assets/logo.png" alt="Repository Logo" width="200" style="margin-top: 20px; margin-bottom: 20px;"/>
</div>
<br>

verdi-llm helps AiiDA users generate `verdi` commands using natural language queries. Instead of memorizing complex command syntax, simply describe what you want to do, and verdi-llm will suggest the appropriate command.


## Installation

```
pip install verdi-llm
```

## Quick Start

**Interactive Setup Process:**
1. Choose a backend (currently supports: `groq`)
2. Enter your API key for the selected backend
3. Wait for embeddings to be generated (one-time setup)

**Example:**
```bash
$ verdi-llm configure
This command will help you choose and configure an LLM backend for AiiDA.

Please follow the instructions below to set up your preferred LLM backend.
Step #1 Choose a backend:
      groq
Your choice: groq
Step #2 Enter your API key for groq:
Your API key: gsk_xxxxxxxxxxxxxxxxxxxx

Configuration saved to ~/.aiida/llm/config.json
You can now use the verdi smart command to interact with the LLM backend.
```

**Non-Interactive Setup Process:**
`verdi-llm configure --backend groq --api-key <API-KEY>` -- to generate a key [see here](https://console.groq.com/keys)

### 2. Generate Commands

Use the `cli` command to get AI-powered command suggestions:

```bash
verdi-llm cli "your question here"
```

**Example:**
```bash
verdi-llm cli "how do I list all my calculations"
```

**Output:**
```bash
💡 Suggested command (in 1.2 seconds): 
verdi process list

[E]xecute, [M]odify, [C]ancel? 
```



### 3. Interactive Shell Mode
Loading embeddings takes a few seconds, which can become annoying if you plan to ask multiple questions. It's better to load them once with the interactive shell:

```bash
verdi-llm shell
```



## User Workflows

### Workflow 1: Quick Command Generation

**Goal:** Get a single command suggestion and execute it

```bash
# Step 1: Ask your question
verdi-llm cli "show me the status of my computer setup"

# Step 2: Review the suggestion
💡 Suggested command (in 0.8 seconds): 
verdi computer list --all

# Step 3: Choose action
[E]xecute, [M]odify, [C]ancel? e

# Step 4: Command executes automatically
$ verdi computer list --all
[Command output appears here]
```

### Workflow 2: Interactive Shell Session

**Goal:** Work in an interactive environment with persistent AI assistance

```bash
# Launch shell
verdi-llm shell

# The shell loads AI models (one-time per session)
🚀 Initializing verdi-llm shell...
   Loading SentenceTransformer (this may take a few seconds)...
✅ SentenceTransformer loaded successfully!
🎯 verdi-llm shell ready!

# Use regular commands
verdi-llm:~/projects$ ls
project1/  project2/  data/

# Ask AI for help
verdi-llm:~/projects$ cli create a new calculation job
💡 Suggested command:
verdi process submit

[E]xecute, [M]odify, [C]ancel? m
Enter modified command: verdi process submit --help

# Regular shell features work
verdi-llm:~/projects$ cd project1
verdi-llm:~/projects/project1$ 

# Exit when done
verdi-llm:~/projects/project1$ exit
👋 Exiting verdi-llm shell
```


## Command Examples

### Basic Usage Examples

| Natural language query | Typical suggested command |
|------------------------|---------------------------|
| "is my computer configured correctly" | `verdi computer configure show` |
| "show details of process 123" | `verdi process show 123` |
| "get information about node 456" | `verdi node show 456` |

### Advanced Usage Examples

| Complex queries | Suggested command patterns |
|----------------|---------------------------|
| "Delete the working directories of all finished calculation jobs since the last month on cluster1 and cluster2 without asking for confirmation" | `verdi calcjob cleanworkdir --past-days 30 --computers cluster1,cluster2 --exit-status 0 --force` |
| "Export band structure data node 98765 as a matplotlib PDF with y-axis range from -5 to 10, LaTeX-formatted labels, and saves it to bands.pdf" | `verdi data core.bands export 98765 --format mpl_pdf --y-min-lim -5 --y-max-lim 10 --prettify-format latex --output bands.pdf` |




### RAG System Insights

The system uses Retrieval-Augmented Generation (RAG) to find relevant commands:

1. **Your query** → Converted to embeddings
2. **Similarity search** → Finds top 3 most relevant commands
3. **Context building** → Includes command usage, descriptions, and options
4. **AI generation** → Creates specific command based on context


## Troubleshooting

### Common Issues and Solutions

**Issue: "No configuration file found"**
```
Solution: Run `verdi-llm configure` first
```

**Issue: AI responses are slow**
```
Possible causes:
- First-time embedding generation
- Network latency to LLM backend
- Large command database

Solutions:
- Use the shell mode for faster subsequent queries
- Check your internet connection
- Wait for initial setup to complete
```

**Issue: Commands don't work as expected**
```
Solutions:
- Use the [M]odify option to adjust commands
- Check if you have the required AiiDA setup
- Verify command parameters match your environment
```

## API Backend Information

### Groq Integration

Currently supports Groq's API with the following models:
- **Default**: `llama3-8b-8192`
- **Features**: Fast inference, good command understanding
- **Rate limits**: Subject to Groq's API limitations

### Adding New Backends

The architecture supports additional backends. Future versions may include more backends.
If you prefer another backend, please open an issue with your suggestion!

## Support and Feedback


- Report issues with specific query examples
- Suggest improvements for command understanding
- Share successful query patterns
