import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
import { dirname } from 'node:path'

const __dirname = dirname(fileURLToPath(import.meta.url))

export default defineConfig(({ mode }) => {
  const env = {
    ...loadEnv(mode, __dirname, ''),
    ...loadEnv(mode, process.cwd(), ''),
    ...process.env,
  }
  // Use 127.0.0.1 to avoid Windows Node.js IPv6 localhost (::1) ECONNREFUSED issues
  const defaultPort = env.PORT || env.BACKEND_PORT || '8000'
  const backendTarget = env.BACKEND_URL || env.VITE_API_URL || `http://127.0.0.1:${defaultPort}`

  let configuredPort = '8000'
  try {
    const url = new URL(backendTarget)
    configuredPort = url.port || (url.protocol === 'https:' ? '443' : '80')
  } catch (_) {
    configuredPort = defaultPort
  }

  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy: {
        '/api': {
          target: backendTarget,
          changeOrigin: true,
          secure: false,
          ws: true,
          configure: (proxy, _options) => {
            proxy.on('error', (err, _req, res) => {
              if (res && typeof res.writeHead === 'function' && !res.headersSent) {
                res.writeHead(503, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({
                  error: 'Backend API unavailable',
                  message: `The GlobalDataMind AI backend is offline or starting up. Ensure uvicorn is running on port ${configuredPort}.`,
                  detail: err.message,
                  status: 'backend_offline'
                }));
              }
            });
          },
        },
      },
    },
  }
})
