import { api } from './api.js';
import { reactionPicker } from './reactions.js';
import { toast } from './utils.js';

export function chatView({ onDelete, currentUserId }) {
  const box = document.createElement('div');
  box.className = 'panel';
  box.innerHTML = `
    <div class='chat-header'>Выберите чат</div>
    <div class='messages' id='messages'></div>
    <div class='reply-preview hidden' id='reply-preview'></div>
    <div class='composer'>
      <input id='msg-text' placeholder='Сообщение...' />
      <input id='msg-file' type='file' />
      <button id='create-poll' title='Создать опрос'>📊</button>
      <button id='stickers-open' title='Стикеры'>😀</button>
      <button id='msg-send'>Отправить</button>
    </div>
    <div class='sticker-panel hidden' id='sticker-panel'></div>`;

  let activeChatId = null;
  let selectedReply = null;
  let cachedStickerPacks = null;

  function renderReplyPreview() {
    const el = box.querySelector('#reply-preview');
    if (!selectedReply) {
      el.classList.add('hidden');
      el.innerHTML = '';
      return;
    }

    el.classList.remove('hidden');
    el.innerHTML = `<div><strong>Ответ на #${selectedReply.id}</strong>: ${selectedReply.text || '[медиа]'}</div>
      <button id='cancel-reply'>×</button>`;
    el.querySelector('#cancel-reply').onclick = () => {
      selectedReply = null;
      renderReplyPreview();
    };
  }

  async function renderMessages(chatId) {
    activeChatId = chatId;
    selectedReply = null;
    renderReplyPreview();
    const messages = await api.messages(chatId);
    const list = box.querySelector('#messages');
    list.innerHTML = '';
    messages.forEach((m) => list.appendChild(messageNode(m, chatId)));
    list.scrollTop = list.scrollHeight;
  }

  function replySnippet(replyTo) {
    if (!replyTo) return '';
    return `<div class='reply-snippet'>↪ ${replyTo.text || `[${replyTo.file_type || 'медиа'}]`}</div>`;
  }

  function forwardSnippet(forwarded) {
    if (!forwarded) return '';
    return `<div class='reply-snippet'>Переслано из: ${forwarded.title || 'чата'}</div>`;
  }

  function pollNode(m) {
    if (!m.poll) return '';
    const optionsHtml = m.poll.options.map((o) => {
      const checked = m.poll.my_votes?.includes(o.id) ? 'checked' : '';
      const type = m.poll.multiple_choice ? 'checkbox' : 'radio';
      return `<label class='poll-option'><input ${checked} type='${type}' name='poll-${m.poll.id}' value='${o.id}' ${m.poll.is_closed ? 'disabled' : ''}/> ${o.text} <span class='badge'>(${o.votes})</span></label>`;
    }).join('');

    return `<div class='poll-box' data-poll-id='${m.poll.id}'>
      <div><strong>📊 ${m.poll.question}</strong></div>
      ${optionsHtml}
      <div class='poll-actions'>
        <button class='poll-vote' ${m.poll.is_closed ? 'disabled' : ''}>Голосовать</button>
        <button class='poll-close' ${m.poll.is_closed ? 'disabled' : ''}>Закрыть</button>
      </div>
    </div>`;
  }

  function messageMedia(m) {
    if (!m.file_url) return '';
    if (m.file_type === 'image') return `<img src='${m.file_url}' style='max-width:220px;border-radius:8px' />`;
    if (m.file_type === 'video') return `<video controls src='${m.file_url}' style='max-width:260px'></video>`;
    if (m.file_type === 'sticker') return `<img src='${m.file_url}' class='sticker-msg' alt='sticker' />`;
    return `<a href='${m.file_url}' target='_blank'>${m.file_name} (${(m.file_size / 1024).toFixed(1)} KB)</a>`;
  }

  function bindPollActions(el, m) {
    if (!m.poll) return;
    const voteBtn = el.querySelector('.poll-vote');
    const closeBtn = el.querySelector('.poll-close');

    voteBtn?.addEventListener('click', async () => {
      const checked = [...el.querySelectorAll(`input[name='poll-${m.poll.id}']:checked`)].map((x) => Number(x.value));
      if (!checked.length) return toast('Выберите вариант');
      await api.votePoll(m.poll.id, checked);
      await renderMessages(activeChatId);
    });

    closeBtn?.addEventListener('click', async () => {
      await api.closePoll(m.poll.id);
      await renderMessages(activeChatId);
    });
  }

  function messageNode(m, chatId) {
    const el = document.createElement('div');
    el.className = `message ${m.sender_id === currentUserId ? 'own' : ''}`;
    el.innerHTML = `${forwardSnippet(m.forwarded_from)}${replySnippet(m.reply_to)}<div>${m.text || ''}</div><div class='meta'>#${m.id} · ${new Date(m.created_at).toLocaleString()}</div>${pollNode(m)}${messageMedia(m)}`;

    const actions = document.createElement('div');
    actions.className = 'message-actions';

    const reply = document.createElement('button');
    reply.textContent = 'Ответить';
    reply.onclick = () => {
      selectedReply = m;
      renderReplyPreview();
      box.querySelector('#msg-text').focus();
    };

    const forward = document.createElement('button');
    forward.textContent = 'Переслать';
    forward.onclick = async () => {
      const target = prompt('ID чата/канала для пересылки:');
      if (!target) return;
      await api.forwardMessage(m.id, Number(target));
      toast('Сообщение переслано');
    };

    const del = document.createElement('button');
    del.textContent = 'Удалить';
    del.onclick = async () => {
      if (!confirm('Удалить сообщение?')) return;
      await api.deleteMessage(m.id);
      onDelete?.(m.id, chatId);
      el.remove();
    };

    actions.append(reply, forward, del);
    el.append(actions, reactionPicker(m.id));
    bindPollActions(el, m);
    return el;
  }

  async function loadStickerPanel() {
    if (!cachedStickerPacks) cachedStickerPacks = await api.stickerPacks();
    const panel = box.querySelector('#sticker-panel');
    panel.innerHTML = '';
    if (!cachedStickerPacks.length) {
      panel.textContent = 'Стикеры не найдены в backend/stickers';
      return;
    }

    cachedStickerPacks.forEach((pack) => {
      const wrap = document.createElement('div');
      wrap.className = 'sticker-pack';
      wrap.innerHTML = `<div class='sticker-pack-title'>${pack.cover_url ? `<img src='${pack.cover_url}' class='sticker-cover'/>` : ''}<span>${pack.name}</span></div>`;
      const grid = document.createElement('div');
      grid.className = 'sticker-grid';
      pack.stickers.forEach((sticker) => {
        const btn = document.createElement('button');
        btn.className = 'sticker-btn';
        btn.innerHTML = `<img src='${sticker.url}' alt='${sticker.name}'/>`;
        btn.onclick = async () => {
          if (!activeChatId) return toast('Сначала выберите чат');
          const fd = new FormData();
          fd.append('sticker_path', sticker.path);
          if (selectedReply?.id) fd.append('reply_to_id', String(selectedReply.id));
          await api.sendMessage(activeChatId, fd);
          selectedReply = null;
          renderReplyPreview();
          panel.classList.add('hidden');
          await renderMessages(activeChatId);
        };
        grid.appendChild(btn);
      });
      wrap.appendChild(grid);
      panel.appendChild(wrap);
    });
  }

  box.querySelector('#create-poll').onclick = async () => {
    if (!activeChatId) return toast('Сначала выберите чат');
    const question = prompt('Вопрос опроса:');
    if (!question) return;
    const optionsRaw = prompt('Варианты (через запятую):');
    if (!optionsRaw) return;
    const options = optionsRaw.split(',').map((x) => x.trim()).filter(Boolean);
    const multiple = confirm('Разрешить выбрать несколько вариантов?');
    const anonymous = confirm('Анонимный опрос? (ОК=да, Отмена=нет)');
    const quiz = confirm('Режим викторины?');
    await api.createPoll(activeChatId, { question, options, multiple_choice: multiple, anonymous, quiz_mode: quiz });
    await renderMessages(activeChatId);
  };

  box.querySelector('#stickers-open').onclick = async () => {
    const panel = box.querySelector('#sticker-panel');
    panel.classList.toggle('hidden');
    if (!panel.classList.contains('hidden')) {
      await loadStickerPanel();
    }
  };

  box.querySelector('#msg-send').onclick = async () => {
    if (!activeChatId) return toast('Сначала выберите чат');
    const fd = new FormData();
    fd.append('text', box.querySelector('#msg-text').value);
    const f = box.querySelector('#msg-file').files[0];
    if (f) fd.append('file', f);
    if (selectedReply?.id) fd.append('reply_to_id', String(selectedReply.id));

    await api.sendMessage(activeChatId, fd);
    box.querySelector('#msg-text').value = '';
    box.querySelector('#msg-file').value = '';
    selectedReply = null;
    renderReplyPreview();
    await renderMessages(activeChatId);
  };

  return { el: box, renderMessages };
}
