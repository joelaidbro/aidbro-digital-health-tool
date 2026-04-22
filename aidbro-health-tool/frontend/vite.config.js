import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import { fileURLToPath } from 'url'

const rootDir = fileURLToPath(new URL('.', import.meta.url))
const routeRewrites = new Map([
  ['/auth', '/auth/'],
  ['/auth/callback', '/auth/callback/'],
  ['/login', '/login/'],
  ['/register', '/register/'],
  ['/upgrade', '/upgrade/'],
  ['/portal', '/portal/'],
])

function routeRewritePlugin() {
  const rewrite = (req, _res, next) => {
    if (!req.url) {
      next()
      return
    }

    const [pathname, query = ''] = req.url.split('?')
    const target = routeRewrites.get(pathname)
    if (target) {
      req.url = `${target}${query ? `?${query}` : ''}`
    }
    next()
  }

  return {
    name: 'aidbro-route-rewrites',
    configureServer(server) {
      server.middlewares.use(rewrite)
    },
    configurePreviewServer(server) {
      server.middlewares.use(rewrite)
    },
  }
}

export default defineConfig({
  appType: 'mpa',
  plugins: [react(), routeRewritePlugin()],
  build: {
    rollupOptions: {
      input: {
        main: resolve(rootDir, 'index.html'),
        auth: resolve(rootDir, 'auth/index.html'),
        authCallback: resolve(rootDir, 'auth/callback/index.html'),
        login: resolve(rootDir, 'login/index.html'),
        register: resolve(rootDir, 'register/index.html'),
        upgrade: resolve(rootDir, 'upgrade/index.html'),
        portal: resolve(rootDir, 'portal/index.html'),
        admin: resolve(rootDir, 'admin.html'),
      },
    },
  },
})
