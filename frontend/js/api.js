const API = '/api';

function token() { return localStorage.getItem('token'); }

async function req(path, options = {}) {
  const headers = options.headers || {};
  if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';
  if (token()) headers.Authorization = `Bearer ${token()}`;

  const r = await fetch(`${API}${path}`, { ...options, headers });
  const raw = await r.text();

  let data = {};
  try {
    data = raw ? JSON.parse(raw) : {};
  } catch {
    data = {};
  }

  if (!r.ok) {
    const fallback = raw && !raw.startsWith('<!doctype') ? raw : `HTTP ${r.status}`;
    throw new Error(data.error || fallback || 'Ошибка запроса');
  }

  return data;
}

async function adminReq(path, adminPassword) {
  return req(path, { headers: { 'X-Admin-Panel-Password': adminPassword } });
}

export const api = {
  register: (payload) => req('/register', { method: 'POST', body: JSON.stringify(payload) }),
  login: (payload) => req('/login', { method: 'POST', body: JSON.stringify(payload) }),
  me: () => req('/me'),
  search: (q) => req(`/users/search?q=${encodeURIComponent(q)}`),
  chats: () => req('/chats'),
  privateChat: (user_id) => req('/chats/private', { method: 'POST', body: JSON.stringify({ user_id }) }),
  messages: (chatId, beforeId) => req(`/chats/${chatId}/messages${beforeId ? `?before_id=${beforeId}` : ''}`),
  sendMessage: (chatId, form) => req(`/chats/${chatId}/messages`, { method: 'POST', body: form }),
  deleteMessage: (id) => req(`/messages/${id}`, { method: 'DELETE' }),
  reaction: (id, reaction_type) => req(`/messages/${id}/reactions`, { method: 'POST', body: JSON.stringify({ reaction_type }) }),
  createGroup: (form) => req('/groups', { method: 'POST', body: form }),
  addGroupMember: (id, user_id) => req(`/groups/${id}/members`, { method: 'POST', body: JSON.stringify({ user_id }) }),
  createChannel: (form) => req('/channels', { method: 'POST', body: form }),
  channel: (id) => req(`/channels/${id}`),
  subscribe: (id) => req(`/channels/${id}/subscribe`, { method: 'POST' }),
  patchMe: (payload) => req('/users/me', { method: 'PATCH', body: JSON.stringify(payload) }),
  avatar: (form) => req('/users/me/avatar', { method: 'POST', body: form }),
  changePassword: (payload) => req('/users/me/password', { method: 'PATCH', body: JSON.stringify(payload) }),
  adminSettings: (adminPassword) => adminReq('/admin/settings', adminPassword),
  adminUsers: (adminPassword) => adminReq('/admin/users', adminPassword),
  adminUserChats: (adminPassword, userId) => adminReq(`/admin/users/${userId}/chats`, adminPassword),
  storiesFeed: () => req('/stories/feed'),
  createStory: (form) => req('/stories', { method: 'POST', body: form }),
  story: (id) => req(`/stories/${id}`),
  deleteStory: (id) => req(`/stories/${id}`, { method: 'DELETE' }),
  stickerPacks: () => req('/stickers'),
};
