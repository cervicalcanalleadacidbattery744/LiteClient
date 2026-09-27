import { defineConfig, type Plugin } from 'vite';
import path from 'node:path';

// Without HMR, Vite doesn't re-transform timeline.ts when a scene file is added, so its
// import.meta.glob keeps the old scene list: invalidate it on add/unlink.
const sceneGlob = (): Plugin => ({
  name: 'scene-glob-refresh',
  configureServer(server) {
    const refresh = (f: string) => {
      if (!/[\\/]src[\\/]scenes[\\/][^\\/]+\.ts$/.test(f)) return;
      const m = server.moduleGraph.getModuleById(path.resolve(import.meta.dirname, 'src/timeline.ts'));
      if (m) server.moduleGraph.invalidateModule(m);
    };
    server.watcher.on('add', refresh);
    server.watcher.on('unlink', refresh);
  },
});

// The repo root holds audio/ and data/; serve them next to the app.
export default defineConfig({
  root: '.',
  publicDir: 'public',
  plugins: [sceneGlob()],
  // VIZ_NO_HMR=1: no live reload (export renders must not reload mid-run when a file changes)
  server: { port: 5190, strictPort: true, hmr: process.env.VIZ_NO_HMR ? false : undefined, fs: { allow: [path.resolve(import.meta.dirname, '..')] } },
  resolve: { alias: { '@root': path.resolve(import.meta.dirname, '..') } },
  build: { target: 'esnext', assetsInlineLimit: 0 },
});
