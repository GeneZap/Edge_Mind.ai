# EdgeMind AI — VS Code local-first coding assistant

An experimental VS Code extension integrating the React chat and LangGraph orchestrator.

## What works in this integration branch
- Real local Ollama inference using installed models.
- Optional OpenAI-compatible cloud inference **only when enabled in VS Code settings**.
- Automatically falls back to an installed Ollama model if the cloud request fails.
- SQLite workspace chunk storage with local Ollama embeddings (`nomic-embed-text` when installed); lexical retrieval works without an embedding model.
- VS Code sidebar, selected-code insertion, workspace indexing, and chat messages.
- Loopback-only authenticated Python service, never a publicly exposed backend.
- Original orchestrator mock CLI/tests remain available.

## Local setup
1. Install Python 3.11+ and Node.js, and start Ollama.
2. Run `ollama pull qwen2.5-coder:3b` and optionally `ollama pull nomic-embed-text`.
3. `python -m pip install -r requirements.txt`
4. `npm --prefix webview-ui ci` then `npm run build:webview`.
5. Open this repository in VS Code, press F5 with an Extension Development Host launch configuration, or run `npx vsce package` to produce an installable VSIX.
6. Configure `edgemind.pythonPath` when your Python environment isn't on PATH.

Cloud (optional): Set `EDGEMIND_CLOUD_API_KEY`, `EDGEMIND_CLOUD_MODEL`, and optionally `EDGEMIND_CLOUD_BASE_URL` in VS Code's environment before launch, then enable `edgemind.allowCloud`. **Enabling cloud permits sending retrieved code snippets to the provider.** Leave disabled for local-only privacy. Cloud URLs must use HTTPS.

## Testing
`python -m unittest discover -s tests -v`
`npm --prefix webview-ui run build`

## Limitations
This is an MVP, not production ready. Ollama must already be running and a model must be downloaded. Initial indexing is capped at 300 files, 256 KB per file. Existing on-disk indexes do not automatically remove deleted files. Semantic retrieval requires the optional Ollama embedding model; otherwise it uses lexical similarity. Cloud connectivity is inferred from actual cloud request failure, rather than Wi-Fi status. The extension does not edit code automatically. Python dependencies and Ollama are not bundled into the VSIX. No end-to-end VS Code launch or live model performance has been verified yet.
