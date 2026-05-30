import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // Must match your GitHub repository name exactly.
  // Change this if your repo is named differently.
  base: '/mlops-playbook/',
})
