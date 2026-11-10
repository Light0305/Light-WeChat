const form = document.querySelector('#style-selection');
const panels = [...document.querySelectorAll('[data-effect]')];
const intro = document.querySelector('[data-intro-wordmark]');
const feedback = document.querySelector('#notes');
const copyButton = document.querySelector('.copy-button');
const copyStatus = document.querySelector('#copy-status');
const fallback = document.querySelector('#copy-fallback');
const presetForm = document.querySelector('#preset-form');
const presetName = document.querySelector('#preset-name');
const presetList = document.querySelector('#preset-list');
const presetStatus = document.querySelector('#preset-status');
const presetPanel = document.getElementById('studio-presets');
const presetToggle = document.querySelector('.preset-toggle');
const jumpButton = document.querySelector('#jump-preview');
const key = 'lsf-wechat-editorial-layout:named-presets-v1';
// 与左栏、文章顺序一致：章节 → 截图背景 → 文末贴纸
const groups = ['chapters', 'screenshot-background', 'stickers']
  .filter(group => form.elements.namedItem(group));
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
const twoPane = matchMedia('(min-width: 720px)');
let renaming = null;
let activePreset = null;
let lastTarget = document.getElementById('studio-article');
const screenshotPreview = document.getElementById('preview-screenshot-background');
const drawScreenshot = screenshotPreview && window.startScreenshotBackgrounds
  ? startScreenshotBackgrounds(form) : null;

if (presetToggle) {
  const sidebar = presetPanel.closest('.sidebar');
  const compact = matchMedia('(max-width: 959px)');
  const isOpen = () => sidebar.classList.contains('preset-open');
  function setOpen(open) {
    sidebar.classList.toggle('preset-open', open);
    presetToggle.setAttribute('aria-expanded', String(open));
  }
  presetToggle.addEventListener('click', () => {
    setOpen(!isOpen());
    if (isOpen()) presetPanel.focus({preventScroll: true});
  });
  document.addEventListener('click', event => {
    if (isOpen() && !presetToggle.contains(event.target) && !presetPanel.contains(event.target)) setOpen(false);
  });
  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape' || event.defaultPrevented || !isOpen()) return;
    setOpen(false);
    presetToggle.focus({preventScroll: true});
  });
  compact.addEventListener('change', () => setOpen(false));
}

function paintSelections() {
  for (const panel of panels) {
    const selected = form.elements.namedItem(panel.dataset.effect);
    panel.hidden = selected?.value !== panel.dataset.option;
  }
  // 每组标题旁写出当前选择，翻到别页也知道选了什么
  for (const group of form.querySelectorAll('.style-group')) {
    const picked = group.querySelector('[data-picked]');
    const selected = group.querySelector('.choice > input:checked');
    if (picked) picked.textContent = selected ? selected.closest('.choice').querySelector('.choice-name').textContent : '未选';
  }
}

for (const preview of form.querySelectorAll('[data-option-preview]')) {
  const choice = preview.closest('.choice').querySelector('input');
  for (const panel of panels.filter(panel => panel.dataset.effect === choice.name && panel.dataset.option === choice.value)) {
    const sample = new Image();
    sample.alt = '';
    sample.src = panel.dataset.still || panel.src;
    preview.append(sample);
  }
}

function syncStickerMotion() {
  for (const image of panels.filter(panel => panel.dataset.still)) {
    image.src = reduced.matches ? image.dataset.still : image.dataset.animated;
  }
}

reduced.addEventListener('change', syncStickerMotion);
syncStickerMotion();

function clearCopyState() {
  copyStatus.textContent = '';
  fallback.hidden = true;
  copyButton.textContent = '复制选择';
  copyButton.classList.remove('is-done');
}

function revealTarget(target) {
  if (!target) return;
  lastTarget = target;
  if (!reduced.matches) {
    target.getAnimations().forEach(animation => animation.cancel());
    target.animate([{opacity: .55}, {opacity: 1}], {duration: 260, easing: 'ease-out'});
  }
  if (!twoPane.matches) return; // 单栏时由「看效果」跳转，不抢用户的滚动位置
  const scrolling = target.closest('.reading-scroll');
  if (scrolling && scrolling.scrollHeight > scrolling.clientHeight + 4) {
    scrolling.scrollTo({top: target.getBoundingClientRect().top - scrolling.getBoundingClientRect().top
      + scrolling.scrollTop - 24, behavior: reduced.matches ? 'instant' : 'smooth'});
  }
}

form.addEventListener('input', event => {
  clearCopyState();
  markPreset(null);
  const choice = event.target;
  if (choice.type !== 'radio') {
    if (intro?.contains(choice)) lastTarget = document.getElementById('preview-intro');
    return;
  }
  paintSelections();
  if (choice.name === 'screenshot-background') drawScreenshot?.();
  revealTarget(document.getElementById(`preview-${choice.name}`));
  choicePagers.get(choice.closest('.choices'))?.refresh();
});

/* 单栏时由按钮跳到当前选项的文章位置。 */
if (jumpButton) {

  jumpButton.addEventListener('click', () => {
    lastTarget.scrollIntoView({behavior: reduced.matches ? 'instant' : 'smooth', block: 'start'});
  });
  const syncJump = () => { jumpButton.hidden = twoPane.matches; };
  twoPane.addEventListener('change', syncJump);
  syncJump();
}

function readPresets() {
  try {
    const stored = JSON.parse(localStorage.getItem(key) || '[]');
    return Array.isArray(stored) ? stored.filter(item => typeof item?.id === 'string'
      && typeof item?.name === 'string' && item.selection && item.intro) : [];
  } catch {
    return [];
  }
}

function readPresetBackup(text) {
  const backup = JSON.parse(text);
  if (backup?.format !== 'lsf-wechat-presets' || backup.version !== 1 || !Array.isArray(backup.presets)) {
    throw new Error('请选择 Dinamo 导出的预设备份');
  }
  return backup.presets.map(item => {
    const {name, selection, intro} = item ?? {};
    if (typeof name !== 'string' || !name.trim() || name.length > 32
      || !selection || typeof selection !== 'object' || Array.isArray(selection)
      || typeof intro?.value !== 'string' || typeof intro.presetId !== 'string'
      || !['manual', 'article'].includes(intro.source)
      || (intro.articleDraft != null && typeof intro.articleDraft !== 'string')
      || (intro.manualDraft != null && typeof intro.manualDraft !== 'string')
      || (intro.logoUrl && (typeof intro.logoUrl !== 'string'
        || !/^data:image\/png;base64,[A-Za-z0-9+/]+={0,2}$/.test(intro.logoUrl)))) {
      throw new Error('备份中的预设格式不完整');
    }
    return {
      id: crypto.randomUUID?.() ?? `${Date.now()}-${Math.random()}`,
      name: name.trim(),
      selection: Object.fromEntries(['chapters', 'screenshot-background', 'stickers']
        .filter(group => typeof selection[group] === 'string').map(group => [group, selection[group]])),
      intro: {value: intro.value, presetId: intro.presetId, source: intro.source,
        articleDraft: intro.articleDraft ?? '', manualDraft: intro.manualDraft ?? null,
        logoUrl: intro.logoUrl || '', articleWorkflow: intro.articleWorkflow === 'deferred' ? 'deferred' : undefined},
    };
  });
}

if (presetPanel) {
  const fileInput = document.getElementById('preset-import-file');
  document.getElementById('preset-export').addEventListener('click', () => {
    const presets = readPresets();
    if (!presets.length) {
      presetStatus.textContent = '还没有可导出的预设';
      return;
    }
    const content = JSON.stringify({format: 'lsf-wechat-presets', version: 1, presets}, null, 2);
    const url = URL.createObjectURL(new Blob([content], {type: 'application/json'}));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'dinamo-presets.json';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  document.getElementById('preset-import').addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', async () => {
    const file = fileInput.files[0];
    fileInput.value = '';
    if (!file) return;
    try {
      if (file.size > 5 * 1024 * 1024) throw new Error('预设备份不能超过 5 MB');
      const imported = readPresetBackup(await file.text());
      const presets = readPresets();
      const names = new Set(presets.map(item => item.name));
      let added = 0;
      for (const item of imported) {
        if (names.has(item.name)) continue;
        names.add(item.name);
        presets.push(item);
        added++;
      }
      if (added && !storePresets(presets)) return;
      if (added) renderPresets();
      const skipped = imported.length - added;
      presetStatus.textContent = `已导入 ${added} 个预设${skipped ? `，跳过 ${skipped} 个同名预设` : ''}`;
    } catch (error) {
      presetStatus.textContent = error instanceof SyntaxError ? '无法读取预设备份 JSON' : error.message;
    }
  });
}

function storePresets(presets) {
  try {
    localStorage.setItem(key, JSON.stringify(presets));
    return true;
  } catch {
    presetStatus.textContent = '浏览器无法保存预设，可能是 Logo 太大或储存空间不足';
    return false;
  }
}

function makeButton(label, action, className) {
  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = label;
  if (className) button.className = className;
  button.addEventListener('click', action);
  return button;
}

/* 分页：每页最多三行；翻页不改变选择；当前选择不在本页时给出提示 */
const choicePagers = new Map();

function paginateChoices(grid) {
  if (choicePagers.has(grid)) return;
  const cards = [...grid.children];
  const label = grid.closest('.style-step')?.querySelector('.step-label')
    ?? grid.closest('fieldset').querySelector('legend');
  const slot = grid.closest('.style-step')?.querySelector('.step-head')
    ?? grid.closest('fieldset').querySelector(':scope > .group-head');
  const pager = document.createElement('div');
  const pageNumber = document.createElement('span');
  const elsewhere = makeButton('', () => showPage(selectedPage()), 'pager-elsewhere');
  const previous = makeButton('‹', () => showPage(page - 1, -1), 'pager-step');
  const next = makeButton('›', () => showPage(page + 1, 1), 'pager-step');
  previous.setAttribute('aria-label', '上一页');
  next.setAttribute('aria-label', '下一页');
  pager.className = 'choice-pager';
  pager.setAttribute('role', 'group');
  pager.setAttribute('aria-label', `${label.textContent.trim()}翻页`);
  pageNumber.className = 'choice-page-number';
  pageNumber.setAttribute('aria-live', 'polite');
  pager.append(elsewhere, previous, pageNumber, next);
  (slot ?? grid.parentElement).append(pager);

  let page = 0;
  let pageSize = 0;
  const total = () => Math.max(1, Math.ceil(cards.length / pageSize));
  const selectedIndex = () => cards.findIndex(card => card.querySelector('input:checked'));
  const selectedPage = () => Math.max(0, Math.floor(selectedIndex() / pageSize));

  function refresh() {
    const all = total();
    pager.hidden = all <= 1;
    pageNumber.textContent = `${page + 1} / ${all}`;
    previous.disabled = page === 0;
    next.disabled = page === all - 1;
    const sel = selectedIndex();
    const away = sel !== -1 && Math.floor(sel / pageSize) !== page;
    elsewhere.hidden = !away;
    elsewhere.textContent = away ? `已选在第 ${Math.floor(sel / pageSize) + 1} 页` : '';
  }

  function showPage(target, direction = 0) {
    if (target < 0 || target >= total()) return;
    const changed = target !== page;
    page = target;
    const first = page * pageSize;
    cards.forEach((card, index) => {
      card.hidden = index < first || index >= first + pageSize;
    });
    refresh();
    if (changed && direction && !reduced.matches) {
      grid.animate([{opacity: 0, transform: `translateX(${direction * 12}px)`}, {opacity: 1, transform: 'none'}],
        {duration: 200, easing: 'cubic-bezier(.2,.7,.2,1)'});
    }
  }

  function fitPage() {
    const columns = getComputedStyle(grid).gridTemplateColumns.split(/\s+/).filter(Boolean).length || 1;
    const nextPageSize = columns * 3;
    if (nextPageSize === pageSize) return;
    const first = page * pageSize;
    const checked = selectedIndex();
    const anchor = checked >= first && (pageSize === 0 || checked < first + pageSize) ? checked : first;
    pageSize = nextPageSize;
    showPage(Math.floor(Math.max(0, anchor) / pageSize));
  }

  // 手机上左右滑动翻页
  let touchX = null;
  grid.addEventListener('touchstart', e => { touchX = e.touches[0].clientX; }, {passive: true});
  grid.addEventListener('touchend', e => {
    if (touchX === null) return;
    const dx = e.changedTouches[0].clientX - touchX;
    touchX = null;
    if (Math.abs(dx) > 48) showPage(page + (dx < 0 ? 1 : -1), dx < 0 ? 1 : -1);
  });

  fitPage();
  new ResizeObserver(fitPage).observe(grid);
  choicePagers.set(grid, {
    refresh,
    reveal(value) {
      const index = cards.findIndex(card => card.querySelector('input').value === value);
      if (index !== -1) showPage(Math.floor(index / pageSize));
    },
  });
}

form.querySelectorAll('.choices').forEach(paginateChoices);
if (intro) {
  const observer = new MutationObserver(() => {
    const grid = intro.querySelector('.intro-choices');
    if (!grid) return;
    observer.disconnect();
    paginateChoices(grid);
    paintSelections();
  });
  observer.observe(intro, {childList: true, subtree: true});
  intro.addEventListener('intro-preset-change', () => {
    paintSelections();
    choicePagers.get(intro.querySelector('.intro-choices'))?.refresh();
  });
  intro.addEventListener('click', event => {
    if (!event.target.closest('.segmented button')) return;
    clearCopyState();
    markPreset(null);
    revealTarget(document.getElementById('preview-intro'));
  });
}
feedback.addEventListener('input', clearCopyState);

function markPreset(id) {
  activePreset = id;
  presetList?.querySelectorAll('.preset-row').forEach(row => {
    row.setAttribute('aria-current', String(row.dataset.id === id));
  });
}

function renderPresets() {
  presetList.replaceChildren();
  const presets = readPresets();
  if (!presets.length) {
    const empty = document.createElement('li');
    empty.className = 'preset-empty';
    empty.textContent = '还没有预设';
    presetList.append(empty);
    return;
  }
  for (const item of presets) {
    const row = document.createElement('li');
    row.className = 'preset-row';
    row.dataset.id = item.id;
    const apply = makeButton(item.name, () => {
      for (const group of groups) {
        const choice = [...form.querySelectorAll(`input[name="${group}"]`)]
          .find(input => input.value === item.selection[group]);
        if (choice) {
          choice.checked = true;
          choicePagers.get(choice.closest('.choices'))?.reveal(choice.value);
        }
      }
      intro?.dispatchEvent(new CustomEvent('restore-intro-state', { detail: item.intro }));
      choicePagers.get(intro?.querySelector('.intro-choices'))?.reveal(item.intro.presetId);
      paintSelections();
      drawScreenshot?.();
      choicePagers.forEach(pager => pager.refresh());
      presetStatus.textContent = `已套用「${item.name}」`;
      clearCopyState();
      markPreset(item.id);
    }, 'preset-apply');
    apply.setAttribute('aria-label', `套用 ${item.name}`);
    const edit = makeButton('改名', () => {
      renaming = item.id;
      presetName.value = item.name;
      presetForm.querySelector('button').textContent = '确认改名';
      presetStatus.textContent = '输入新名字后确认，按 Esc 取消';
      presetName.focus();
      presetName.select();
    });
    edit.setAttribute('aria-label', `改名 ${item.name}`);
    const remove = makeButton('删除', () => {
      if (remove.dataset.confirm !== 'true') {
        remove.textContent = '确认删除';
        remove.dataset.confirm = 'true';
        remove.addEventListener('blur', () => {
          remove.textContent = '删除';
          delete remove.dataset.confirm;
        }, { once: true });
        return;
      }
      if (storePresets(readPresets().filter(other => other.id !== item.id))) {
        if (renaming === item.id) resetPresetForm();
        renderPresets();
        presetStatus.textContent = `已删除「${item.name}」`;
      }
    }, 'preset-remove');
    remove.setAttribute('aria-label', `删除 ${item.name}`);
    row.append(apply, edit, remove);
    presetList.append(row);
  }
  markPreset(activePreset);
}

function resetPresetForm() {
  renaming = null;
  presetForm.reset();
  presetForm.querySelector('button').textContent = '保存预设';
}

presetForm?.addEventListener('submit', event => {
  event.preventDefault();
  const name = presetName.value.trim();
  if (!name) {
    presetStatus.textContent = '请填写预设名称';
    presetName.focus();
    return;
  }
  const presets = readPresets();
  if (presets.some(item => item.name === name && item.id !== renaming)) {
    presetStatus.textContent = '已有同名预设，请换个名字';
    return;
  }
  const existing = presets.find(item => item.id === renaming);
  let id = existing?.id;
  if (existing) {
    existing.name = name;
  } else {
    const state = intro?.readIntroState?.();
    if (!state) {
      presetStatus.textContent = '样式仍在加载，请稍后再试';
      return;
    }
    const selection = Object.fromEntries(groups.map(group => [group, form.elements.namedItem(group).value]));
    id = crypto.randomUUID?.() ?? String(Date.now());
    presets.push({ id, name, selection, intro: state });
  }
  if (!storePresets(presets)) return;
  presetStatus.textContent = `已${existing ? '改名为' : '保存'}「${name}」`;
  resetPresetForm();
  activePreset = id;
  renderPresets();
});
presetForm?.addEventListener('keydown', event => {
  if (event.key === 'Escape' && renaming) {
    event.preventDefault();
    resetPresetForm();
    presetStatus.textContent = '已取消改名';
  }
});
addEventListener('storage', event => {
  if (presetList && event.key === key) renderPresets();
});
if (presetList) renderPresets();
paintSelections();
drawScreenshot?.();

form.addEventListener('submit', async event => {
  event.preventDefault();
  const lines = [];
  const articleTitle = document.querySelector('#studio-article[data-draft] h1');
  if (articleTitle) lines.push(`稿件标题：${articleTitle.textContent}`);
  for (const group of form.querySelectorAll('.style-group')) {
    const title = group.querySelector('legend').textContent.trim();
    const selected = group.querySelector('.choice > input:checked');
    if (!selected) {
      copyStatus.textContent = `请先选择${title}`;
      group.scrollIntoView({behavior: reduced.matches ? 'instant' : 'smooth', block: 'start'});
      return;
    }
    lines.push(`${title}：${selected.closest('.choice').querySelector('.choice-name').textContent}`);
    if (intro && group.contains(intro)) {
      const state = intro.readIntroState?.();
      if (state?.source === 'article') {
        lines.push('开篇文案来源：Agent 提炼文章');
        const scenes = state.articleDraft.split('\n').map(line => line.trim()).filter(Boolean).slice(0, 4);
        if (scenes.length) {
          lines.push('开篇文案（已回填）：', ...(state.hasScenes ? scenes : scenes.slice(0, 1)));
        } else {
          const length = state.hasScenes ? '给 1–4 条短句，每行一句。' : '给 1 条短句。';
          lines.push(`开篇文案任务：根据我提供的当前文章，提炼与主题和所选动效匹配的简短开篇文案。${length}只返回文案，方便我粘贴回预览。如果还没有收到文章，先向我索取正文。`);
        }
      } else {
        lines.push('开篇文案来源：自己写');
        lines.push(`署名文字：${state?.value?.trim() || intro.dataset.author}`);
        if (state?.hasScenes && state.manualDraft?.trim()) {
          const scenes = state.manualDraft.split('\n').map(line => line.trim()).filter(Boolean).slice(0, 4);
          lines.push('开篇分镜（每行一句）：', ...scenes);
        }
      }
      if (selected.value === 'emboss' && state?.logoUrl) lines.push('浮雕 Logo：已在预览中上传');
    }
  }
  if (feedback.value.trim()) lines.push(`补充意见：${feedback.value.trim()}`);
  const summary = lines.join('\n');
  const done = () => {
    copyStatus.textContent = `已复制 ${lines.length} 行，粘贴到对话即可`;
    copyButton.textContent = '已复制';
    copyButton.classList.add('is-done');
    clearTimeout(copyButton._t);
    copyButton._t = setTimeout(() => { copyButton.textContent = '复制选择'; copyButton.classList.remove('is-done'); }, 1800);
  };
  try {
    await navigator.clipboard.writeText(summary);
    done();
  } catch {
    fallback.value = summary;
    fallback.hidden = false;
    fallback.select();
    if (document.execCommand('copy')) {
      fallback.hidden = true;
      done();
    } else copyStatus.textContent = '浏览器不允许自动复制，文字已选中，请手动复制';
  }
});
