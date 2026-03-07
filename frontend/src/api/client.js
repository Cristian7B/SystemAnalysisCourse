import axios from 'axios';

const api = axios.create({ baseURL: '/api', withCredentials: true });

// Auto-attach access token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('accessToken');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
    (res) => res,
    async (err) => {
        const orig = err.config;
        if (err.response?.status === 401 && !orig._retry) {
            orig._retry = true;
            try {
                const refresh = localStorage.getItem('refreshToken');
                const { data } = await axios.post('/api/auth/refresh', { refreshToken: refresh });
                localStorage.setItem('accessToken', data.accessToken);
                localStorage.setItem('refreshToken', data.refreshToken);
                orig.headers.Authorization = `Bearer ${data.accessToken}`;
                return api(orig);
            } catch {
                localStorage.removeItem('accessToken');
                localStorage.removeItem('refreshToken');
                window.location.href = '/login';
            }
        }
        return Promise.reject(err);
    }
);

export default api;
