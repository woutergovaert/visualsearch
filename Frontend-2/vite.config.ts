import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from "path"

export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@components": path.resolve(__dirname, "./src/components"),
      "@layouts": path.resolve(__dirname, "./src/components/layouts"),
    }
  }, 
  plugins: [react()],
  envDir: path.resolve(".."),
})

console.log(path.resolve(".."))