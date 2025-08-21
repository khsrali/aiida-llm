# verdi-llm

<br>
<div align="left">
  <img src="assets/logo.png" alt="Repository Logo" width="200" style="margin-top: 20px; margin-bottom: 20px;"/>
</div>
<br>

Uses LLM to achieve a prompt via aiida cli



## Installation

At the moment only developer installation is available. Just fetch the repo and run
```
pip install -e .
```

## Usage

For now, it only works with [Groq](https://groq.com/), because it provides free API.
More backends will be added later.

First, configure for once:
`verdi-llm configure --backend groq --api-key <API-KEY>` -- to generate a key [see here](https://console.groq.com/keys)

Now you can ask whatever you want, the limit is your imagination :crossed_fingers: 
`$ verdi-llm cli 'delete are groups that start with label qe*'`

It will then, respond with a generated command and asks for a confirmation (`e`) before executing it. 
```
$ verdi-llm cli 'delete are groups that start with label qe*'
Generated command: `verdi group delete --startswith qe`

Execute[e], Modify[m], or Cancel[c]:: e
$ verdi process list
Command output:

Report: all groups deleted.
```
Alternatively the user has the option (`m`) to edit the command and fix mistakes before executing. Or simply press `c` to cancel.
