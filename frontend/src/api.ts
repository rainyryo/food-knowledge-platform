import axios from 'axios';

// 環境変数からバックエンドURLを取得（デフォルトは開発環境）
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const login = async (username: string, password: string) => {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await api.post('/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return response.data;
};

export const getMe = async () => {
  const response = await api.get('/auth/me');
  return response.data;
};

export const register = async (username: string, email: string, password: string, fullName?: string) => {
  const response = await api.post('/auth/register', {
    username,
    email,
    password,
    full_name: fullName,
  });
  return response.data;
};

export const updateProfile = async (email: string, fullName: string) => {
  const response = await api.put('/auth/profile', {
    email,
    full_name: fullName,
  });
  return response.data;
};

export const changePassword = async (currentPassword: string, newPassword: string) => {
  const response = await api.put('/auth/password', {
    current_password: currentPassword,
    new_password: newPassword,
  });
  return response.data;
};

// Search
export const search = async (query: string, topK?: number, filters?: Record<string, string>) => {
  const response = await api.post('/search', { query, top_k: topK, filters });
  return response.data;
};

export const getSearchHistory = async (limit?: number) => {
  const response = await api.get('/search/history', { params: { limit } });
  return response.data;
};

export const getFacets = async () => {
  const response = await api.get('/search/facets');
  return response.data;
};

// Documents
export const uploadDocument = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const getDocuments = async (page?: number, pageSize?: number, status?: string) => {
  const response = await api.get('/documents', {
    params: { page, page_size: pageSize, status },
  });
  return response.data;
};

export const deleteDocument = async (id: number) => {
  const response = await api.delete(`/documents/${id}`);
  return response.data;
};

export const getDocumentDownloadUrl = async (documentId: number) => {
  const response = await api.get(`/documents/${documentId}/download-url`);
  return response.data;
};


export const reprocessDocument = async (id: number) => {
  const response = await api.post(`/documents/${id}/reprocess`);
  return response.data;
};

// Admin
export const getSystemStats = async () => {
  const response = await api.get('/admin/stats');
  return response.data;
};

export const createSearchIndex = async () => {
  const response = await api.post('/admin/create-index');
  return response.data;
};

// User Management (Admin only)
export const getUsers = async (page?: number, pageSize?: number) => {
  const response = await api.get('/admin/users', {
    params: { page, page_size: pageSize },
  });
  return response.data;
};

export const updateUser = async (userId: number, data: { email?: string; full_name?: string; is_admin?: boolean; is_active?: boolean }) => {
  const response = await api.put(`/admin/users/${userId}`, data);
  return response.data;
};

export const deleteUser = async (userId: number) => {
  const response = await api.delete(`/admin/users/${userId}`);
  return response.data;
};

export default api;
