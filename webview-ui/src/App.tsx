
import { useEffect, useState } from 'react'
import {
  Bot,
  Plus,
  Settings,
  Wifi,
  WifiOff,
  Send,
  User,
  Sparkles,
  FileCode
} from 'lucide-react'

type Message = {
  role: 'user' | 'assistant'
  content: string
}

declare function acquireVsCodeApi(): { postMessage: (msg: unknown) => void }

const vscode = typeof acquireVsCodeApi === 'function' ? acquireVsCodeApi() : null

function App() {
  const [online, setOnline] = useState(true)
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [inVscode, setInVscode] = useState(false)

  // Listen for messages coming back from the extension host
  useEffect(() => {
    const inVscode = typeof acquireVsCodeApi === 'function'
    setInVscode(inVscode)

    const handler = (event: MessageEvent) => {
      const message = event.data
      if (message?.command === 'selectedCode' && message.text) {
        setInput(`Here is my code (${message.fileName}):\n\n${message.text}\n\n`)
      }
    }
    window.addEventListener('message', handler)
    return () => window.removeEventListener('message', handler)
  }, [])

  const sendMessage = () => {
    if (!input.trim()) return

    const question = input.trim()

    setMessages(prev => [
      ...prev,
      { role: 'user', content: question },
      {
        role: 'assistant',
        content: online
          ? 'Demo response from Claude. Backend integration will come later.'
          : 'Demo response from your local LLM. Backend integration will come later.'
      }
    ])

    setInput('')
  }

  return (
    <div className="h-screen flex flex-col bg-[#1e1e1e] text-white">

      {/* Header */}
      <header className="p-3 border-b border-white/10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="text-blue-400" />
            <span className="font-semibold">Adaptive AI</span>
          </div>

          <div className="flex gap-3">
            <button title="New chat" onClick={() => setMessages([])}>
              <Plus size={18} />
            </button>
            {inVscode && (
              <button
                title="Insert selected code"
                onClick={() => vscode?.postMessage({ command: 'getSelectedCode' })}
              >
                <FileCode size={18} />
              </button>
            )}
            <button title="Settings">
              <Settings size={18} />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2 mt-3 text-xs">
          {online
            ? <Wifi size={15} className="text-green-400" />
            : <WifiOff size={15} className="text-orange-400" />
          }

          <span>{online ? 'Online' : 'Offline'}</span>
          <span className="text-white/50">•</span>
          <span>{online ? 'Claude' : 'Local LLM'}</span>

          <button
            className="ml-auto text-blue-400"
            onClick={() => setOnline(!online)}
          >
            Simulate switch
          </button>
        </div>
      </header>

      {/* Chat */}
      <main className="flex-1 overflow-y-auto p-3 space-y-4">

        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <Sparkles size={35} className="text-blue-400 mb-3" />
            <h2 className="text-lg font-semibold">
              How can I help you?
            </h2>
            <p className="text-xs text-white/50 mt-2">
              Your AI coding assistant, online or offline.
            </p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div key={index} className="flex gap-2">
              {message.role === 'user'
                ? <User size={18} className="shrink-0 text-blue-400" />
                : <Bot size={18} className="shrink-0 text-green-400" />
              }

              <div className="text-sm leading-6 break-words">
                {message.content}
              </div>
            </div>
          ))
        )}

      </main>

      {/* Input */}
      <footer className="p-3 border-t border-white/10">
        <div className="border border-white/20 rounded-lg p-2">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                sendMessage()
              }
            }}
            placeholder="Ask anything about your code..."
            className="w-full bg-transparent outline-none resize-none text-sm min-h-14"
          />

          <div className="flex justify-end">
            <button
              onClick={sendMessage}
              className="bg-blue-600 hover:bg-blue-500 rounded-md p-2"
              title="Send message"
            >
              <Send size={16} />
            </button>
          </div>
        </div>

        <p className="text-[10px] text-white/40 text-center mt-2">
          {inVscode ? 'Running inside VS Code' : 'Browser preview · No backend connected'}
        </p>
      </footer>

    </div>
  )
}

export default App
