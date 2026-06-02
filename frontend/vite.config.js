import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      { find: /^es-toolkit\/compat\/get$/, replacement: path.resolve(__dirname, 'node_modules/es-toolkit/compat/get.js') },
      { find: /^es-toolkit\/compat\/omit$/, replacement: path.resolve(__dirname, 'node_modules/es-toolkit/compat/omit.js') },
      { find: /^es-toolkit\/compat\/isPlainObject$/, replacement: path.resolve(__dirname, 'node_modules/es-toolkit/compat/isPlainObject.js') },
      { find: /^es-toolkit\/compat\/sortBy$/, replacement: path.resolve(__dirname, 'node_modules/es-toolkit/compat/sortBy.js') },
      { find: /^es-toolkit\/compat\/range$/, replacement: path.resolve(__dirname, 'node_modules/es-toolkit/compat/range.js') },
      { find: /^es-toolkit\/compat\/last$/, replacement: path.resolve(__dirname, 'node_modules/es-toolkit/compat/last.js') },
      { find: /^es-toolkit\/compat\/maxBy$/, replacement: path.resolve(__dirname, 'node_modules/es-toolkit/compat/maxBy.js') },
      { find: /^es-toolkit\/compat\/minBy$/, replacement: path.resolve(__dirname, 'node_modules/es-toolkit/compat/minBy.js') },
      { find: /^es-toolkit\/compat\/uniqBy$/, replacement: path.resolve(__dirname, 'node_modules/es-toolkit/compat/uniqBy.js') },
      { find: /^es-toolkit\/compat\/throttle$/, replacement: path.resolve(__dirname, 'node_modules/es-toolkit/compat/throttle.js') },
      { find: /^es-toolkit\/compat\/sumBy$/, replacement: path.resolve(__dirname, 'node_modules/es-toolkit/compat/sumBy.js') },
      { find: 'use-sync-external-store/shim/with-selector', replacement: path.resolve(__dirname, 'src/wrappers/use-sync-external-store-shim-with-selector.mjs') },
      { find: /^use-sync-external-store\/with-selector$/, replacement: path.resolve(__dirname, 'src/wrappers/use-sync-external-store-shim-with-selector.mjs') },
      { find: 'use-sync-external-store/with-selector.js', replacement: path.resolve(__dirname, 'src/wrappers/use-sync-external-store-shim-with-selector.mjs') },
    ],
  },
  optimizeDeps: {
    exclude: ['recharts', 'react-router-dom'],
    include: [
      'react',
      'react-dom',
    ],
  },
  ssr: {
    noExternal: ['recharts'],
  },
})

