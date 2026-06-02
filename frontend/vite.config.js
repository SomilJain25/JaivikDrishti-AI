import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['recharts', 'es-toolkit'],
  },
  ssr: {
    noExternal: ['recharts', 'es-toolkit'],
  },
})
