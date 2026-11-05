import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// The VS Code webview runtime exposes `acquireVsCodeApi` globally.
// App.tsx calls it (it may only be called once), so we do nothing here.

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
