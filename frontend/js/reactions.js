import { api } from './api.js';

export const REACTIONS = ['👍','❤️','😂','😮','😢','😡','🎉','🤔','👎','🔥','🚀','👀','💯','✅','🆒'];

export function reactionPicker(messageId) {
  const box = document.createElement('div');
  box.className = 'reactions';
  REACTIONS.forEach((r) => {
    const b = document.createElement('button');
    b.className = 'reaction';
    b.textContent = r;
    b.onclick = () => api.reaction(messageId, r);
    box.appendChild(b);
  });
  return box;
}
