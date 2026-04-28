import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    hmr: {
      clientPort: 443, // GitHub Codespaces uses HTTPS (port 443)
      protocol: 'wss', // Use secure websocket for HMR
    },
  },
})
