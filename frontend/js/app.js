import { api } from './api.js';
import { authView } from './auth.js';
import { chatView } from './chat.js';
import { createGroupModal } from './groups.js';
import { createChannelModal, toggleSubscribe } from './channels.js';
import { bindSearch } from './search.js';
import { profileModal } from './profile.js';
import { initTheme, openChatSettingsModal } from './theme.js';
import { renderStories } from './stories.js';
import { openAdminPanel } from './admin.js';
import { toast } from './utils.js';

initTheme();

const app = document.getElementById('app');
let socket;

function connectSocket() {
  const token = localStorage.getItem('token');
  if (!token) return;
  socket = io('/', { auth: { token } });
}

async function logoutAndReset() {
  try {
    await api.logout();
  } catch {
    // ignore API logout failures in client-only reset flow
  }
  localStorage.removeItem('token');
  bootstrap();
}

async function renderMessenger() {
  const me = await api.me();
  const chats = await api.chats();
  app.innerHTML = `<div class='layout'>
      <aside class='panel sidebar'>
        <input class='search-input' placeholder='Поиск людей и каналов' id='global-search'/>
        <button id='new-group'>+ Группа</button>
        <button id='new-channel'>+ Канал</button>
        <button id='chat-settings'>⚙️ Настройки чата</button>
        <button id='profile'>Профиль</button>
        <button id='admin-panel'>Админ-панель</button>
        <div id='stories'></div>
        <div class='chat-list' id='chat-list'></div>
      </aside>
      <main id='chat-main'></main>
      <aside class='panel sidebar right-panel' id='right-panel'></aside>
    </div>`;

  const chat = chatView({ currentUserId: me.id });
  document.getElementById('chat-main').appendChild(chat.el);

  const chatList = document.getElementById('chat-list');
  await renderStories(document.getElementById('stories'));
  chats.forEach((c) => {
    const item = document.createElement('div');
    item.className = 'chat-item';
    item.textContent = `${c.type === 'channel' ? '📣' : c.type === 'group' ? '👥' : '💬'} ${c.title || 'Личный чат'} `;
    item.onclick = () => chat.renderMessages(c.id);
    chatList.appendChild(item);
  });

  const searchInput = document.getElementById('global-search');
  bindSearch(searchInput, async (result) => {
    if (result.kind === 'user') {
      const created = await api.privateChat(result.id);
      await chat.renderMessages(created.chat_id);
    } else {
      document.getElementById('right-panel').innerHTML = `<h3>${result.title}</h3><p>${result.description || ''}</p><button id='sub'>Подписаться/Отписаться</button>`;
      document.getElementById('sub').onclick = () => toggleSubscribe(result.id);
    }
    searchInput.value = '';
  });

  document.getElementById('new-group').onclick = () => document.body.appendChild(createGroupModal(renderMessenger));
  document.getElementById('new-channel').onclick = () => document.body.appendChild(createChannelModal(renderMessenger));
  document.getElementById('chat-settings').onclick = () => openChatSettingsModal({ onLogout: logoutAndReset });
  document.getElementById('profile').onclick = () => document.body.appendChild(profileModal(me, renderMessenger));
  document.getElementById('admin-panel').onclick = () => openAdminPanel();

  if (socket) {
    socket.off('new_message');
    socket.on('new_message', () => toast('Новое сообщение'));
    socket.off('reaction_updated');
    socket.on('reaction_updated', () => {});
  }
}

function bootstrap() {
  if (!localStorage.getItem('token')) {
    app.innerHTML = '';
    app.appendChild(authView(() => { connectSocket(); renderMessenger(); }));
    return;
  }

  connectSocket();
  renderMessenger().catch((e) => {
    toast(e.message);
    localStorage.removeItem('token');
    bootstrap();
  });
}

bootstrap();
