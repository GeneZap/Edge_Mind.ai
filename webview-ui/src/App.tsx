import { useEffect, useState } from 'react'
import { Bot, Plus, Settings, Wifi, WifiOff, Send, User, Sparkles, FileCode, Database } from 'lucide-react'

type Message = { role: 'user' | 'assistant'; content: string; provider?: string; sources?: string[] }
type HostMessage = { command?: string; text?: string; fileName?: string; id?: number;
  status?: string; content?: string; error?: string; provider?: string; model?: string;
  sources?: string[]; local_models?: string[]; cloud_configured?: boolean; count?: number }
declare function acquireVsCodeApi(): { postMessage: (msg: unknown) => void }
const vscode = typeof acquireVsCodeApi === 'function' ? acquireVsCodeApi() : null

function App() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [pending, setPending] = useState(false)
  const [status, setStatus] = useState('Checking local service…')
  const [models, setModels] = useState<string[]>([])
  const [indexState, setIndexState] = useState('')
  const [nextId, setNextId] = useState(1)

  useEffect(() => {
    const handler = (event: MessageEvent<HostMessage>) => {
      const data = event.data
      if (data?.command === 'ready') vscode?.postMessage({ command: 'status' })
      if (data?.command === 'selectedCode' && data.text)
        setInput(prev => prev + (prev ? '\n\n' : '') + 'Code from ' + data.fileName + ':\n\n' + data.text)
      if (data?.command === 'statusResult') {
        setModels(data.local_models || [])
        setStatus((data.local_models?.length || 0) > 0
          ? 'Local model ready' : 'No Ollama models found')
      }
      if (data?.command === 'indexComplete')
        setIndexState('Indexed ' + data.count + ' workspace chunks')
      if (data?.command === 'chatResult') {
        setPending(false)
        setMessages(prev => [...prev, { role: 'assistant',
          content: data.content || data.error || 'No response available.',
          provider: data.provider || 'unavailable', sources: data.sources }])
      }
      if (data?.command === 'error') {
        setPending(false)
        setMessages(prev => [...prev, { role: 'assistant', content: 'Error: ' + (data.error || 'Unknown error') }])
        setStatus(data.error || 'Service unavailable')
      }
    }
    window.addEventListener('message', handler)
    return () => window.removeEventListener('message', handler)
  }, [])

  const sendMessage = () => {
    if (!input.trim() || pending) return
    const question = input.trim()
    setMessages(prev => [...prev, { role: 'user', content: question }])
    setInput('')
    setPending(true)
    if (!vscode) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Browser preview only. Run EdgeMind inside VS Code to use live inference.' }])
      setPending(false)
      return
    }
    vscode.postMessage({ command: 'chat', id: nextId, query: question })
    setNextId(id => id + 1)
  }

  return (
    <div className="h-screen flex flex-col bg-[#1e1e1e] text-white">
      <header className="p-3 border-b border-white/10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2"><Bot className="text-blue-400" /><span className="font-semibold">EdgeMind AI</span></div>
          <div className="flex gap-3">
            <button title="New chat" onClick={() => setMessages([])}><Plus size={18}/></button>
            {vscode && <button title="Insert selected code" onClick={() => vscode.postMessage({ command: 'getSelectedCode' })}><FileCode size={18}/></button>}
            <button title="Index workspace" onClick={() => { setIndexState('Indexing…'); vscode?.postMessage({ command: 'index' }) }}><Database size={18}/></button>
            <button title="Settings" onClick={() => vscode?.postMessage({ command: 'settings' })}><Settings size={18}/></button>
          </div>
        </div>
        <div className="flex items-center gap-2 mt-3 text-xs">
          {models.length ? <Wifi size={15} className="text-green-400"/> : <WifiOff size={15} className="text-orange-400"/>}
          <span>{status}</span>
          <button className="ml-auto text-blue-400" title="Refresh status" onClick={() => vscode?.postMessage({ command: 'status' })}>Refresh</button>
        </div>
        {indexState && <p className="text-xs text-white/50 mt-1">{indexState}</p>}
      </header>
      <main className="flex-1 overflow-y-auto p-3 space-y-4">
        {messages.length === 0 ? <div className="h-full flex flex-col items-center justify-center text-center">
          <Sparkles size={35} className="text-blue-400 mb-3"/>
          <h2 className="text-lg font-semibold">How can I help you?</h2>
          <p className="text-xs text-white/50 mt-2">Repository-aware coding help, online or offline.</p>
        </div> : messages.map((message, index) => <div key={index} className="flex gap-2">
          {message.role === 'user' ? <User size={18} className="shrink-0 text-blue-400"/> : <Bot size={18} className="shrink-0 text-green-400"/>}
          <div className="min-w-0">
            <div className="text-sm leading-6 whitespace-pre-wrap break-words">{message.content}</div>
            {message.provider && <p className="text-xs text-blue-300 mt-1">Via {message.provider}</p>}
            {!!message.sources?.length && <p className="text-xs text-white/50">Sources: {message.sources.join(', ')}</p>}
          </div>
        </div>)}
        {pending && <div className="text-xs text-white/60">Generating response…</div>}
      </main>
      <footer className="p-3 border-t border-white/10">
        <div className="border border-white/20 rounded-lg p-2">
          <textarea value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }}
            placeholder="Ask about your code…" className="w-full bg-transparent outline-none resize-none text-sm min-h-14"/>
          <div className="flex justify-end"><button disabled={pending || !input.trim()} onClick={sendMessage}
            className="bg-blue-600 hover:bg-blue-500 rounded-md p-2 disabled:opacity-40" title="Send message"><Send size={16}/></button></div>
        </div>
        <p className="text-[10px] text-white/40 text-center mt-2">{vscode ? 'VS Code · Local-first' : 'Browser preview · Extension host required'}</p>
      </footer>
    </div>
  )
}
export default App
