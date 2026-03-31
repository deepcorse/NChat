import { api } from './api.js';

export function bindSearch(input, onSelect) {
  const wrap = document.createElement('div');
  input.after(wrap);
  input.oninput = async () => {
    const q = input.value.trim();
    wrap.innerHTML = '';
    if (q.length < 2) return;
    const items = await api.search(q);
    items.forEach((i) => {
      const el = document.createElement('div');
      el.className = 'chat-item';
      el.textContent = i.kind === 'user' ? `👤 ${i.nickname} (@${i.login})` : `📣 ${i.title}`;
      el.onclick = () => onSelect(i);
      wrap.appendChild(el);
    });
  };
}
