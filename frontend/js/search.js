import { api } from './api.js';
import { toast } from './utils.js';

export function bindSearch(input, onSelect) {
  const wrap = document.createElement('div');
  wrap.className = 'search-results hidden';
  input.after(wrap);

  let seq = 0;

  function clearResults() {
    wrap.innerHTML = '';
    wrap.classList.add('hidden');
  }

  function renderItem(item) {
    const row = document.createElement('div');
    row.className = 'search-item';

    const left = document.createElement('div');
    left.className = 'search-item-title';
    left.textContent = item.kind === 'user'
      ? `👤 ${item.nickname} (@${item.login})`
      : `📣 ${item.title || 'Канал'}`;

    const rightBtn = document.createElement('button');
    rightBtn.className = 'search-action-btn';
    rightBtn.textContent = item.kind === 'user' ? 'Написать' : 'Перейти';

    const open = () => onSelect(item);
    row.onclick = open;
    rightBtn.onclick = (e) => {
      e.stopPropagation();
      open();
    };

    row.append(left, rightBtn);
    return row;
  }

  input.oninput = async () => {
    const q = input.value.trim();
    const requestId = ++seq;

    if (q.length < 2) {
      clearResults();
      return;
    }

    wrap.classList.remove('hidden');
    wrap.innerHTML = `<div class='search-empty'>Поиск...</div>`;

    try {
      const items = await api.search(q);
      if (requestId !== seq) return;

      wrap.innerHTML = '';
      if (!items.length) {
        wrap.innerHTML = `<div class='search-empty'>Ничего не найдено</div>`;
        return;
      }

      items.forEach((item) => wrap.appendChild(renderItem(item)));
    } catch (e) {
      if (requestId !== seq) return;
      wrap.innerHTML = `<div class='search-empty'>Ошибка поиска</div>`;
      toast(e.message);
    }
  };

  input.onblur = () => setTimeout(clearResults, 180);
  input.onfocus = () => {
    if (wrap.innerHTML.trim()) {
      wrap.classList.remove('hidden');
    }
  };
}
