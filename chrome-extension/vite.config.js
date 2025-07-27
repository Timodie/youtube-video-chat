import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import { copyFileSync, existsSync, mkdirSync } from 'fs'

// Plugin to copy Chrome extension files
function copyExtensionFiles() {
  return {
    name: 'copy-extension-files',
    writeBundle() {
      const files = [
        { src: 'manifest.json', dest: 'dist/manifest.json' },
        { src: 'popup.html', dest: 'dist/popup.html' },
        { src: 'popup.js', dest: 'dist/popup.js' }
      ];

      // Copy icons directory
      if (existsSync('icons')) {
        if (!existsSync('dist/icons')) {
          mkdirSync('dist/icons', { recursive: true });
        }
        try {
          copyFileSync('icons/icon16.png', 'dist/icons/icon16.png');
          copyFileSync('icons/icon48.png', 'dist/icons/icon48.png');
          copyFileSync('icons/icon128.png', 'dist/icons/icon128.png');
        } catch (e) {
          console.log('Some icon files may not exist, skipping...');
        }
      }

      // Copy other extension files
      files.forEach(({ src, dest }) => {
        if (existsSync(src)) {
          copyFileSync(src, dest);
          console.log(`Copied ${src} to ${dest}`);
        }
      });
    }
  };
}

export default defineConfig({
  plugins: [react(), copyExtensionFiles()],
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: {
        content: resolve(__dirname, 'src/content.tsx')
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: '[name].js',
        assetFileNames: '[name].[ext]'
      }
    },
    minify: false, // Keep readable for Chrome extension debugging
    sourcemap: true
  },
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development')
  }
})