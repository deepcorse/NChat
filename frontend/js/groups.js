import { api } from './api.js';
import { toast } from './utils.js';

export function createGroupModal(onCreated) {
  const m = document.createElement('div');
  m.className = 'modal';
  m.innerHTML = `<div class='modal-card'><h3>Новая группа</h3><input id='g-title' placeholder='Название'/><textarea id='g-desc' placeholder='Описание'></textarea><button id='g-save'>Создать</button></div>`;
  m.onclick = (e) => e.target === m && m.remove();
  m.querySelector('#g-save').onclick = async () => {
    const fd = new FormData();
    fd.append('title', m.querySelector('#g-title').value);
    fd.append('description', m.querySelector('#g-desc').value);
    try { await api.createGroup(fd); toast('Группа создана'); m.remove(); onCreated?.(); } catch (e) { toast(e.message); }
  };
  return m;
}
