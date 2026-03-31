import { api } from './api.js';
import { toast } from './utils.js';

export function authView(onDone) {
  const div = document.createElement('div');
  div.className = 'auth-wrap';
  div.innerHTML = `
    <h2>nchat</h2>
    <input id='login' placeholder='Логин' />
    <input id='nickname' placeholder='Ник (для регистрации)' />
    <input id='password' placeholder='Пароль' type='password' />
    <div style='display:flex;gap:8px;margin-top:8px'>
      <button id='btn-login'>Войти</button>
      <button id='btn-reg'>Регистрация</button>
    </div>`;

  div.querySelector('#btn-login').onclick = async () => {
    try {
      const data = await api.login({ login: div.querySelector('#login').value, password: div.querySelector('#password').value });
      localStorage.setItem('token', data.token);
      onDone();
    } catch (e) { toast(e.message); }
  };

  div.querySelector('#btn-reg').onclick = async () => {
    try {
      const data = await api.register({ login: div.querySelector('#login').value, nickname: div.querySelector('#nickname').value, password: div.querySelector('#password').value });
      localStorage.setItem('token', data.token);
      onDone();
    } catch (e) { toast(e.message); }
  };
  return div;
}
