import { api } from './api.js';

export const REACTIONS = ['👍','❤️','😂','😮','😢','😡','🎉','🤔','👎','🔥','🚀','👀','💯','✅','🆒'];

export function bindReactionContext(messageEl, messageId) {
  const menu = document.createElement('div');
  menu.className = 'reaction-context hidden';

  REACTIONS.forEach((r) => {
    const b = document.createElement('button');
    b.className = 'reaction';
    b.textContent = r;
    b.onclick = async (e) => {
      e.stopPropagation();
      await api.reaction(messageId, r);
      menu.classList.add('hidden');
    };
    menu.appendChild(b);
  });

  messageEl.appendChild(menu);

  messageEl.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    menu.classList.remove('hidden');
    menu.style.left = `${e.offsetX}px`;
    menu.style.top = `${e.offsetY}px`;
  });

  document.addEventListener('click', () => menu.classList.add('hidden'));
}
