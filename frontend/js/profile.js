import { api } from './api.js';
import { toast } from './utils.js';

export function profileModal(me, onSaved) {
  const m = document.createElement('div');
  m.className = 'modal';
  m.innerHTML = `<div class='modal-card'><h3>Профиль</h3><input id='nickname' value='${me.nickname || ''}' /><input id='status' value='${me.status || ''}' /><textarea id='description'>${me.description || ''}</textarea><input id='avatar' type='file' accept='image/*'/><hr/><h4>Сменить пароль</h4><input id='old-password' type='password' placeholder='Старый пароль'/><input id='new-password' type='password' placeholder='Новый пароль'/><button id='save'>Сохранить</button></div>`;
  m.onclick = (e) => e.target === m && m.remove();
  m.querySelector('#save').onclick = async () => {
    try {
      await api.patchMe({ nickname: m.querySelector('#nickname').value, status: m.querySelector('#status').value, description: m.querySelector('#description').value });
      const f = m.querySelector('#avatar').files[0];
      if (f) { const fd = new FormData(); fd.append('avatar', f); await api.avatar(fd); }
      const oldPassword = m.querySelector('#old-password').value;
      const newPassword = m.querySelector('#new-password').value;
      if (oldPassword || newPassword) {
        await api.changePassword({ old_password: oldPassword, new_password: newPassword });
      }
      toast('Профиль обновлён');
      m.remove();
      onSaved?.();
    } catch (e) { toast(e.message); }
  };
  return m;
}
