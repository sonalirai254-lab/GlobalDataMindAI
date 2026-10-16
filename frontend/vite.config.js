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
  const backendTarget = env.BACKEND_URL || env.VITE_API_URL || 'http://127.0.0.1:8000'

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
                  message: 'The Graphwise Nexus backend is offline or starting up. Ensure uvicorn is running on port 8000.',
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
