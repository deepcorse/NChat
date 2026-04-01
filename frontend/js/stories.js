import { api } from './api.js';
import { toast } from './utils.js';

export async function renderStories(container) {
  container.innerHTML = `<div style='display:flex;gap:8px;overflow:auto' id='stories-row'></div>`;
  const row = container.querySelector('#stories-row');

  const add = document.createElement('button');
  add.textContent = '+ Story';
  add.onclick = () => openStoryCreateModal(() => renderStories(container));
  row.appendChild(add);

  const feed = await api.storiesFeed();
  feed.forEach((bucket) => {
    const latest = bucket.stories[0];
    const btn = document.createElement('button');
    btn.style.minWidth = '120px';
    btn.textContent = `${latest.seen ? '⚪' : '🟣'} ${bucket.nickname}`;
    btn.onclick = () => openStoryViewer(bucket.stories.map((s) => s.id));
    row.appendChild(btn);
  });
}

export function openStoryCreateModal(onDone) {
  const m = document.createElement('div');
  m.className = 'modal';
  m.innerHTML = `<div class='modal-card'><h3>Новая story (24ч)</h3><input id='s-file' type='file' accept='image/*,video/*'/><textarea id='s-caption' placeholder='Подпись'></textarea><button id='s-save'>Опубликовать</button></div>`;
  m.onclick = (e) => e.target === m && m.remove();
  m.querySelector('#s-save').onclick = async () => {
    const f = m.querySelector('#s-file').files[0];
    if (!f) return toast('Выберите файл');
    const fd = new FormData();
    fd.append('media', f);
    fd.append('caption', m.querySelector('#s-caption').value);
    try {
      await api.createStory(fd);
      toast('Story опубликована');
      m.remove();
      onDone?.();
    } catch (e) {
      toast(e.message);
    }
  };
  document.body.appendChild(m);
}

async function openStoryViewer(storyIds) {
  const m = document.createElement('div');
  m.className = 'modal';
  m.innerHTML = `<div class='modal-card'><div id='story-content'></div><button id='next'>Следующая</button><button id='close'>Закрыть</button></div>`;
  document.body.appendChild(m);

  let idx = 0;
  const content = m.querySelector('#story-content');
  async function render() {
    const data = await api.story(storyIds[idx]);
    content.innerHTML = data.media_type === 'video'
      ? `<video controls autoplay src='${data.media_url}' style='width:100%'></video><p>${data.caption || ''}</p>`
      : `<img src='${data.media_url}' style='width:100%;border-radius:8px'/><p>${data.caption || ''}</p>`;
  }

  m.querySelector('#next').onclick = async () => {
    idx += 1;
    if (idx >= storyIds.length) return m.remove();
    await render();
  };
  m.querySelector('#close').onclick = () => m.remove();
  m.onclick = (e) => e.target === m && m.remove();

  await render();
}
