function applyCssVar(storageKey, cssVar) {
  const value = localStorage.getItem(storageKey);
  if (!value) return;
  if (cssVar === '--chat-background-image') {
    document.documentElement.style.setProperty(cssVar, `url(${value})`);
    return;
  }
  document.documentElement.style.setProperty(cssVar, value);
}

export function initTheme() {
  const saved = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
  applyCssVar('accent', '--accent');
  applyCssVar('chat_bubble', '--chat-bubble');
  applyCssVar('chat_bubble_own', '--chat-bubble-own');
  applyCssVar('chat_bg', '--chat-bg');
  applyCssVar('chat_bg_image', '--chat-background-image');
}

function makeAppearanceControls() {
  const wrap = document.createElement('div');
  wrap.innerHTML = `
    <h4>Оформление чата</h4>
    <button id='theme-toggle'>Светлая/Тёмная</button>
    <label>Акцент <input id='accent' type='color' value='${localStorage.getItem('accent') || '#5b7cfa'}' /></label>
    <label>Пузырь сообщения <input id='chat-bubble' type='color' value='${localStorage.getItem('chat_bubble') || '#ffffff'}' /></label>
    <label>Свои сообщения <input id='chat-bubble-own' type='color' value='${localStorage.getItem('chat_bubble_own') || '#dfe8ff'}' /></label>
    <label>Фон чата <input id='chat-bg' type='color' value='${localStorage.getItem('chat_bg') || '#eef2fb'}' /></label>
    <input id='chat-bg-image' placeholder='URL фонового изображения' value='${localStorage.getItem('chat_bg_image') || ''}' />
    <button id='chat-bg-image-clear'>Очистить фон</button>
  `;

  wrap.querySelector('#theme-toggle').onclick = () => {
    const cur = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', cur);
    localStorage.setItem('theme', cur);
  };
  wrap.querySelector('#accent').onchange = (e) => {
    document.documentElement.style.setProperty('--accent', e.target.value);
    localStorage.setItem('accent', e.target.value);
  };
  wrap.querySelector('#chat-bubble').onchange = (e) => {
    document.documentElement.style.setProperty('--chat-bubble', e.target.value);
    localStorage.setItem('chat_bubble', e.target.value);
  };
  wrap.querySelector('#chat-bubble-own').onchange = (e) => {
    document.documentElement.style.setProperty('--chat-bubble-own', e.target.value);
    localStorage.setItem('chat_bubble_own', e.target.value);
  };
  wrap.querySelector('#chat-bg').onchange = (e) => {
    document.documentElement.style.setProperty('--chat-bg', e.target.value);
    localStorage.setItem('chat_bg', e.target.value);
  };
  wrap.querySelector('#chat-bg-image').onchange = (e) => {
    const url = e.target.value.trim();
    if (!url) return;
    document.documentElement.style.setProperty('--chat-background-image', `url(${url})`);
    localStorage.setItem('chat_bg_image', url);
  };
  wrap.querySelector('#chat-bg-image-clear').onclick = () => {
    document.documentElement.style.setProperty('--chat-background-image', 'none');
    localStorage.removeItem('chat_bg_image');
    wrap.querySelector('#chat-bg-image').value = '';
  };

  return wrap;
}

export function openChatSettingsModal({ onLogout } = {}) {
  const modal = document.createElement('div');
  modal.className = 'modal';
  modal.innerHTML = `<div class='modal-card'>
    <h3>Настройки чата</h3>
    <div id='chat-settings-appearance'></div>
    <hr />
    <h4>Полезные функции</h4>
    <button id='clear-customization'>Сбросить кастомизацию</button>
    <button id='logout'>Выйти из аккаунта</button>
    <button id='close-chat-settings'>Закрыть</button>
  </div>`;

  modal.onclick = (e) => {
    if (e.target === modal) modal.remove();
  };

  modal.querySelector('#chat-settings-appearance').appendChild(makeAppearanceControls());

  modal.querySelector('#clear-customization').onclick = () => {
    ['accent', 'chat_bubble', 'chat_bubble_own', 'chat_bg', 'chat_bg_image'].forEach((k) => localStorage.removeItem(k));
    document.documentElement.style.removeProperty('--accent');
    document.documentElement.style.removeProperty('--chat-bubble');
    document.documentElement.style.removeProperty('--chat-bubble-own');
    document.documentElement.style.removeProperty('--chat-bg');
    document.documentElement.style.setProperty('--chat-background-image', 'none');
  };

  modal.querySelector('#logout').onclick = async () => {
    await onLogout?.();
    modal.remove();
  };

  modal.querySelector('#close-chat-settings').onclick = () => modal.remove();

  document.body.appendChild(modal);
}
