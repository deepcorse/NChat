import { api } from './api.js';
import { toast } from './utils.js';

export function authView(onDone) {
  const div = document.createElement('div');
  div.className = 'auth-wrap';
  div.innerHTML = `
    <h2>nchat</h2>
    <div style='display:flex;gap:8px;margin-bottom:8px'>
      <button id='tab-login'>Вход</button>
      <button id='tab-register'>Регистрация</button>
    </div>

    <div id='login-form'>
      <input id='login-login' placeholder='Логин' />
      <input id='login-password' placeholder='Пароль' type='password' />
      <button id='btn-login' style='margin-top:8px'>Войти</button>
    </div>

    <div id='register-form' class='hidden'>
      <input id='reg-login' placeholder='Логин' />
      <input id='reg-nickname' placeholder='Ник' />
      <input id='reg-password' placeholder='Пароль' type='password' />
      <button id='btn-reg' style='margin-top:8px'>Зарегистрироваться</button>
    </div>`;

  const loginForm = div.querySelector('#login-form');
  const registerForm = div.querySelector('#register-form');

  div.querySelector('#tab-login').onclick = () => {
    loginForm.classList.remove('hidden');
    registerForm.classList.add('hidden');
  };
  div.querySelector('#tab-register').onclick = () => {
    registerForm.classList.remove('hidden');
    loginForm.classList.add('hidden');
  };

  div.querySelector('#btn-login').onclick = async () => {
    try {
      const data = await api.login({
        login: div.querySelector('#login-login').value,
        password: div.querySelector('#login-password').value,
      });
      localStorage.setItem('token', data.token);
      onDone();
    } catch (e) {
      toast(e.message);
    }
  };

  div.querySelector('#btn-reg').onclick = async () => {
    try {
      const data = await api.register({
        login: div.querySelector('#reg-login').value,
        nickname: div.querySelector('#reg-nickname').value,
        password: div.querySelector('#reg-password').value,
      });
      // Автовход после регистрации
      localStorage.setItem('token', data.token);
      onDone();
    } catch (e) {
      toast(e.message);
    }
  };

  return div;
}
