import { createApp } from 'vue';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import App from './App.vue';
import axios from 'axios';

axios.defaults.baseURL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:4000';

createApp(App).use(ElementPlus).mount('#app'); 