export function initTheme() {
  const saved = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
  const accent = localStorage.getItem('accent');
  if (accent) document.documentElement.style.setProperty('--accent', accent);
  const chatBubble = localStorage.getItem('chat_bubble');
  if (chatBubble) document.documentElement.style.setProperty('--chat-bubble', chatBubble);
  const chatBubbleOwn = localStorage.getItem('chat_bubble_own');
  if (chatBubbleOwn) document.documentElement.style.setProperty('--chat-bubble-own', chatBubbleOwn);
  const chatBg = localStorage.getItem('chat_bg');
  if (chatBg) document.documentElement.style.setProperty('--chat-bg', chatBg);
  const chatBgImage = localStorage.getItem('chat_bg_image');
  if (chatBgImage) document.documentElement.style.setProperty('--chat-background-image', `url(${chatBgImage})`);
}

export function themeControls() {
  const wrap = document.createElement('div');
  wrap.innerHTML = `
    <button id='theme-toggle'>Светлая/Тёмная</button>
    <label>Акцент <input id='accent' type='color' value='#5b7cfa' /></label>
    <label>Пузырь сообщения <input id='chat-bubble' type='color' value='#ffffff' /></label>
    <label>Свои сообщения <input id='chat-bubble-own' type='color' value='#dfe8ff' /></label>
    <label>Фон чата <input id='chat-bg' type='color' value='#eef2fb' /></label>
    <input id='chat-bg-image' placeholder='URL фонового изображения' />
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
  };
  return wrap;
}
