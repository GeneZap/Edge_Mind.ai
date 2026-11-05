'use strict';
const vscode = require('vscode');
const crypto = require('crypto');
const http = require('http');
const net = require('net');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const IGNORES = '**/{node_modules,.git,dist,build,.venv,venv,.next,coverage}/**';
let serverProcess;
let apiPort;
let token;
let output;

function request(endpoint, data, timeoutMs = 110000) {
  return new Promise((resolve, reject) => {
    const payload = data === undefined ? null : Buffer.from(JSON.stringify(data));
    const req = http.request({
      hostname: '127.0.0.1', port: apiPort, path: endpoint, method: payload ? 'POST' : 'GET',
      headers: { 'X-EdgeMind-Token': token, ...(payload ? { 'Content-Type': 'application/json', 'Content-Length': payload.length } : {}) },
      timeout: timeoutMs
    }, res => {
      const pieces = [];
      res.on('data', chunk => pieces.push(chunk));
      res.on('end', () => {
        try {
          const result = JSON.parse(Buffer.concat(pieces).toString('utf8'));
          if (res.statusCode >= 400) reject(new Error(result.error || 'Service request failed'));
          else resolve(result);
        } catch (err) { reject(err); }
      });
    });
    req.on('timeout', () => req.destroy(new Error('EdgeMind service timed out')));
    req.on('error', reject);
    if (payload) req.write(payload);
    req.end();
  });
}

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
  });
}

async function startBackend(context) {
  if (serverProcess && !serverProcess.killed) return;
  apiPort = await freePort();
  token = crypto.randomBytes(32).toString('hex');
  const python = vscode.workspace.getConfiguration('edgemind').get('pythonPath') || 'python';
  const env = { ...process.env, EDGEMIND_API_TOKEN: token, EDGEMIND_API_PORT: String(apiPort),
                PYTHONPATH: context.extensionPath + (process.env.PYTHONPATH ? path.delimiter + process.env.PYTHONPATH : '') };
  serverProcess = spawn(python, ['-m', 'edgemind.api'], {
    cwd: context.extensionPath, env, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe']
  });
  serverProcess.stdout.on('data', chunk => output.append(chunk.toString()));
  serverProcess.stderr.on('data', chunk => output.append(chunk.toString()));
  serverProcess.on('error', err => output.appendLine('Backend failed: ' + err.message));
  serverProcess.on('exit', code => { output.appendLine('Backend exited: ' + code); serverProcess = undefined; });
  for (let i = 0; i < 30; i++) {
    await new Promise(resolve => setTimeout(resolve, 200));
    try { await request('/health'); return; } catch (_) {
      if (!serverProcess) break;
    }
  }
  throw new Error('Cannot start local service. Check EdgeMind output and install Python requirements.');
}

function workspace() {
  return vscode.workspace.workspaceFolders?.[0]?.uri.toString() || 'no-workspace';
}

async function indexWorkspace(post) {
  const files = await vscode.workspace.findFiles('**/*', IGNORES, 300);
  let indexed = 0;
  for (const uri of files) {
    const relative = vscode.workspace.asRelativePath(uri, false).replace(/\\/g, '/');
    if (!/\.(py|js|jsx|ts|tsx|json|md|html|css|scss|java|go|rs|c|cpp|h|hpp|yml|yaml|toml|sql|sh|ps1)$/i.test(relative)) continue;
    try {
      const stat = await vscode.workspace.fs.stat(uri);
      if (stat.size > 256000 || !(stat.type & vscode.FileType.File)) continue;
      const text = Buffer.from(await vscode.workspace.fs.readFile(uri)).toString('utf8');
      if (text.includes('\u0000')) continue;
      const result = await request('/index', { workspace: workspace(), path: relative, content: text }, 25000);
      indexed += result.indexed || 0;
    } catch (err) {
      output.appendLine('Index skipped ' + relative + ': ' + err.message);
    }
  }
  post({ command: 'indexComplete', count: indexed });
}

class ChatProvider {
  constructor(context) { this.context = context; }
  async resolveWebviewView(view) {
    this.view = view;
    const webview = view.webview;
    webview.options = { enableScripts: true, localResourceRoots: [vscode.Uri.joinPath(this.context.extensionUri, 'dist')] };
    const file = path.join(this.context.extensionPath, 'dist', 'webview-ui', 'index.html');
    if (!fs.existsSync(file)) {
      webview.html = '<p>Build the webview first: npm --prefix webview-ui install && npm run build:webview</p>';
      return;
    }
    const nonce = crypto.randomBytes(16).toString('base64');
    let html = fs.readFileSync(file, 'utf8');
    html = html.replace(/(src|href)="\.\/([^"]+)"/g, (_, attr, asset) => {
      return attr + '="' + webview.asWebviewUri(vscode.Uri.file(path.join(path.dirname(file), asset))) + '"';
    });
    html = html.replace('</head>', '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src ' + webview.cspSource + ' data:; style-src ' + webview.cspSource + ' \'unsafe-inline\'; script-src ' + webview.cspSource + ';">' + '</head>');
    webview.html = html;
    const post = data => webview.postMessage(data);
    webview.onDidReceiveMessage(async message => {
      try {
        if (message.command === 'getSelectedCode') {
          const editor = vscode.window.activeTextEditor;
          if (editor) post({ command: 'selectedCode', fileName: editor.document.fileName,
                             text: editor.document.getText(editor.selection) });
        } else if (message.command === 'chat') {
          await startBackend(this.context);
          const result = await request('/chat', { query: message.query, workspace: workspace(),
            allow_cloud: vscode.workspace.getConfiguration('edgemind').get('allowCloud') === true });
          post({ command: 'chatResult', id: message.id, ...result });
        } else if (message.command === 'status') {
          await startBackend(this.context);
          post({ command: 'statusResult', ...await request('/health') });
        } else if (message.command === 'index') {
          await startBackend(this.context);
          await indexWorkspace(post);
        } else if (message.command === 'settings') {
          await vscode.commands.executeCommand('workbench.action.openSettings', 'edgemind');
        }
      } catch (err) {
        post({ command: 'error', id: message.id, error: err.message });
      }
    });
    post({ command: 'ready' });
    if (vscode.workspace.getConfiguration('edgemind').get('autoIndex')) {
      try { await startBackend(this.context); await indexWorkspace(post); } catch (err) {
        post({ command: 'error', error: err.message });
      }
    }
    try { await startBackend(this.context); post({ command: 'statusResult', ...await request('/health') }); }
    catch (err) { post({ command: 'error', error: err.message }); }
  }
}

function activate(context) {
  output = vscode.window.createOutputChannel('EdgeMind');
  context.subscriptions.push(output);
  const provider = new ChatProvider(context);
  context.subscriptions.push(vscode.window.registerWebviewViewProvider('edgemind.chat', provider));
  context.subscriptions.push(vscode.commands.registerCommand('edgemind.openChat', () => vscode.commands.executeCommand('edgemind.chat.focus')));
  context.subscriptions.push(vscode.commands.registerCommand('edgemind.indexWorkspace', async () => {
    try { await startBackend(context); await indexWorkspace(data => provider.view?.webview.postMessage(data)); }
    catch (err) { vscode.window.showErrorMessage(err.message); }
  }));
}
function deactivate() { if (serverProcess) serverProcess.kill(); }
module.exports = { activate, deactivate };
