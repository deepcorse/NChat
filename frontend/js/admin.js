import { api } from './api.js';
import { toast } from './utils.js';

export function openAdminPanel() {
  const pwd = prompt('Введите пароль админ-панели');
  if (!pwd) return;

  const modal = document.createElement('div');
  modal.className = 'modal';
  modal.innerHTML = `<div class='modal-card' style='width:900px;max-width:98vw'>
    <h3>Админ-панель</h3>
    <div id='admin-stats'>Загрузка...</div>
    <div style='display:grid;grid-template-columns:300px 1fr;gap:12px'>
      <div><h4>Пользователи</h4><div id='admin-users' style='max-height:360px;overflow:auto'></div></div>
      <div><h4>Чаты пользователя</h4><div id='admin-chats' style='max-height:360px;overflow:auto'></div></div>
    </div>
    <button id='admin-close'>Закрыть</button>
  </div>`;

  const usersEl = modal.querySelector('#admin-users');
  const chatsEl = modal.querySelector('#admin-chats');

  const load = async () => {
    try {
      const stats = await api.adminSettings(pwd);
      modal.querySelector('#admin-stats').innerHTML = `
        <b>Статистика:</b> пользователей ${stats.users_total}, чатов ${stats.chats_total},
        сообщений ${stats.messages_total}, групп ${stats.groups_total}, каналов ${stats.channels_total}`;

      const users = await api.adminUsers(pwd);
      usersEl.innerHTML = '';
      users.forEach((u) => {
        const row = document.createElement('div');
        row.className = 'chat-item';
        row.innerHTML = `<b>${u.nickname}</b> (@${u.login})<br/><span class='badge'>онлайн: ${u.is_online ? 'да' : 'нет'}, чаты: ${u.participated_chats}, каналы: ${u.subscribed_channels}</span>`;
        row.onclick = async () => {
          const chats = await api.adminUserChats(pwd, u.id);
          chatsEl.innerHTML = chats.map((c) => `<div class='chat-item'>#${c.id} [${c.type}] ${c.title || '(без названия)'}</div>`).join('') || '<p>Нет чатов</p>';
        };
        usersEl.appendChild(row);
      });
    } catch (e) {
      toast(e.message);
      modal.remove();
    }
  };

  modal.querySelector('#admin-close').onclick = () => modal.remove();
  modal.onclick = (e) => e.target === modal && modal.remove();
  document.body.appendChild(modal);
  load();
}
