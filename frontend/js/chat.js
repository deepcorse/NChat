import { api } from './api.js';
import { reactionPicker } from './reactions.js';
import { toast } from './utils.js';

export function chatView({ onDelete }) {
  const box = document.createElement('div');
  box.className = 'panel';
  box.innerHTML = `
    <div class='chat-header'>Выберите чат</div>
    <div class='messages' id='messages'></div>
    <div class='composer'>
      <input id='msg-text' placeholder='Сообщение...' />
      <input id='msg-file' type='file' />
      <button id='msg-send'>Отправить</button>
    </div>`;

  let activeChatId = null;

  async function renderMessages(chatId) {
    activeChatId = chatId;
    const messages = await api.messages(chatId);
    const list = box.querySelector('#messages');
    list.innerHTML = '';
    messages.forEach((m) => list.appendChild(messageNode(m, chatId)));
    list.scrollTop = list.scrollHeight;
  }

  function messageNode(m, chatId) {
    const el = document.createElement('div');
    el.className = 'message';
    el.innerHTML = `<div>${m.text || ''}</div><div class='meta'>#${m.id} · ${new Date(m.created_at).toLocaleString()}</div>`;
    if (m.file_url) {
      if (m.file_type === 'image') el.innerHTML += `<img src='${m.file_url}' style='max-width:220px;border-radius:8px' />`;
      else if (m.file_type === 'video') el.innerHTML += `<video controls src='${m.file_url}' style='max-width:260px'></video>`;
      else el.innerHTML += `<a href='${m.file_url}' target='_blank'>${m.file_name} (${(m.file_size/1024).toFixed(1)} KB)</a>`;
    }
    const del = document.createElement('button');
    del.textContent = 'Удалить';
    del.onclick = async () => {
      if (!confirm('Удалить сообщение?')) return;
      await api.deleteMessage(m.id);
      onDelete?.(m.id, chatId);
      el.remove();
    };
    el.appendChild(del);
    el.appendChild(reactionPicker(m.id));
    return el;
  }

  box.querySelector('#msg-send').onclick = async () => {
    if (!activeChatId) return toast('Сначала выберите чат');
    const fd = new FormData();
    fd.append('text', box.querySelector('#msg-text').value);
    const f = box.querySelector('#msg-file').files[0];
    if (f) fd.append('file', f);
    await api.sendMessage(activeChatId, fd);
    box.querySelector('#msg-text').value = '';
    box.querySelector('#msg-file').value = '';
    await renderMessages(activeChatId);
  };

  return { el: box, renderMessages };
}
