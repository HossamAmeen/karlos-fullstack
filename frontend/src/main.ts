import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { listenForInstallPrompt, registerServiceWorker } from './utils/pwa'
import { watchTables } from './utils/responsiveTables'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')

registerServiceWorker()
listenForInstallPrompt()
watchTables()
