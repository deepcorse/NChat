export function initTheme() {
  const saved = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
  const accent = localStorage.getItem('accent');
  if (accent) document.documentElement.style.setProperty('--accent', accent);
}

export function themeControls() {
  const wrap = document.createElement('div');
  wrap.innerHTML = `<button id='theme-toggle'>Светлая/Тёмная</button><input id='accent' type='color' value='#5b7cfa' />`;
  wrap.querySelector('#theme-toggle').onclick = () => {
    const cur = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', cur);
    localStorage.setItem('theme', cur);
  };
  wrap.querySelector('#accent').onchange = (e) => {
    document.documentElement.style.setProperty('--accent', e.target.value);
    localStorage.setItem('accent', e.target.value);
  };
  return wrap;
}
