import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    // Enable caching for faster reloads
    fs: {
      strict: false,
    },
  },
  build: {
    // Optimize chunk sizes
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          // Split vendor chunks for better caching
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'mui-vendor': ['@mui/material', '@mui/icons-material'],
          'charts-vendor': ['recharts'],
        },
      },
    },
  },
  optimizeDeps: {
    // Pre-bundle dependencies for faster dev server startup
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@mui/material',
      '@mui/icons-material',
      'recharts',
    ],
  },
})
