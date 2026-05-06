import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import * as Sentry from '@sentry/react'
import './index.css'
import './stage4.css'
import "./additions.css"
import "./additions_v2.css"
import App from './App.jsx'

const sentryDsn = import.meta.env.VITE_SENTRY_DSN?.trim()

if (sentryDsn) {
  Sentry.init({
    dsn: sentryDsn,
  })
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
