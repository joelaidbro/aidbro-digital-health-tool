import { defineConfig, loadEnv } from 'vite'
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
  ['/app', '/app/'],
  ['/buy-credits', '/buy-credits/'],
  ['/about-us', '/about-us/'],
  ['/privacy-policy', '/privacy-policy/'],
  ['/terms-and-conditions', '/terms-and-conditions/'],
  ['/return-policy', '/return-policy/'],
  ['/contact-us', '/contact-us/'],
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

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, rootDir, '')
  const backendProxyTarget = env.VITE_BACKEND_DEV_PROXY_TARGET || 'http://localhost:8000'
  const proxy = {
    '/api': {
      target: backendProxyTarget,
      changeOrigin: true,
    },
    '/docs': {
      target: backendProxyTarget,
      changeOrigin: true,
    },
    '/openapi.json': {
      target: backendProxyTarget,
      changeOrigin: true,
    },
  }

  return {
    appType: 'mpa',
    plugins: [react(), routeRewritePlugin()],
    server: {
      proxy,
    },
    preview: {
      proxy,
    },
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
          app: resolve(rootDir, 'app/index.html'),
          buyCredits: resolve(rootDir, 'buy-credits/index.html'),
          aboutUs: resolve(rootDir, 'about-us/index.html'),
          privacyPolicy: resolve(rootDir, 'privacy-policy/index.html'),
          termsAndConditions: resolve(rootDir, 'terms-and-conditions/index.html'),
          returnPolicy: resolve(rootDir, 'return-policy/index.html'),
          contactUs: resolve(rootDir, 'contact-us/index.html'),
          admin: resolve(rootDir, 'admin.html'),
        },
      },
    },
  }
})
