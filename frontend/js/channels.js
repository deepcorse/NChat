import { api } from './api.js';
import { toast } from './utils.js';

export function createChannelModal(onCreated) {
  const m = document.createElement('div');
  m.className = 'modal';
  m.innerHTML = `<div class='modal-card'><h3>Новый канал</h3><input id='c-title' placeholder='Название'/><textarea id='c-desc' placeholder='Описание'></textarea><button id='c-save'>Создать</button></div>`;
  m.onclick = (e) => e.target === m && m.remove();
  m.querySelector('#c-save').onclick = async () => {
    const fd = new FormData();
    fd.append('title', m.querySelector('#c-title').value);
    fd.append('description', m.querySelector('#c-desc').value);
    try { await api.createChannel(fd); toast('Канал создан'); m.remove(); onCreated?.(); } catch (e) { toast(e.message); }
  };
  return m;
}

export async function toggleSubscribe(channelId) {
  const res = await api.subscribe(channelId);
  toast(res.subscribed ? 'Вы подписаны' : 'Вы отписаны');
}
