import api from './client';

export const surplus = {
    list: (params) => api.get('/surplus', { params }),
    get: (id) => api.get(`/surplus/${id}`),
    create: (data) => api.post('/surplus', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
    update: (id, data) => api.patch(`/surplus/${id}`, data),
    remove: (id) => api.delete(`/surplus/${id}`),
};

export const claims = {
    list: () => api.get('/claims'),
    incoming: () => api.get('/claims/incoming'),
    create: (surplusId, data) => api.post(`/claims/${surplusId}`, data),
    confirm: (id) => api.patch(`/claims/${id}/confirm`),
    complete: (id) => api.patch(`/claims/${id}/complete`),
    cancel: (id) => api.patch(`/claims/${id}/cancel`),
};

export const auth = {
    register: (data) => api.post('/auth/register', data),
    login: (data) => api.post('/auth/login', data),
    logout: () => api.post('/auth/logout'),
    me: () => api.get('/auth/me'),
    refresh: (token) => api.post('/auth/refresh', { refreshToken: token }),
};

export const notifications = {
    list: () => api.get('/notifications'),
    readAll: () => api.patch('/notifications/read-all'),
    read: (id) => api.patch(`/notifications/${id}/read`),
    subscribe: (sub) => api.post('/notifications/subscribe', sub),
    vapidKey: () => api.get('/notifications/vapid-key'),
};

export const users = {
    profile: (id) => api.get(`/users/${id}/profile`),
    updateMe: (data) => api.patch('/users/me', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
    changePassword: (data) => api.post('/users/me/change-password', data),
    registerOrg: (data) => api.post('/users/organizations', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
};

export const metrics = {
    platform: () => api.get('/metrics/platform'),
    user: () => api.get('/metrics/user'),
    timeseries: () => api.get('/metrics/timeseries'),
    categories: () => api.get('/metrics/categories'),
    leaderboard: () => api.get('/metrics/leaderboard'),
};

export const admin = {
    users: (params) => api.get('/admin/users', { params }),
    banUser: (id, data) => api.patch(`/admin/users/${id}/ban`, data),
    setRole: (id, data) => api.patch(`/admin/users/${id}/role`, data),
    organizations: (params) => api.get('/admin/organizations', { params }),
    verifyOrg: (id, data) => api.patch(`/admin/organizations/${id}/verify`, data),
    surplusAll: (params) => api.get('/admin/surplus', { params }),
    removeSurplus: (id, data) => api.delete(`/admin/surplus/${id}`, { data }),
    logs: () => api.get('/admin/logs'),
};
