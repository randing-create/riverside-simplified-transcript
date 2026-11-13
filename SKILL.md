---
name: riverside-simplified-transcript
description: Bulk-convert a Riverside editor transcript from mixed Traditional/Simplified Chinese to Simplified (timings, cuts and manual corrections kept), then fix mis-heard names. Use when a Riverside Chinese transcript mixes 繁体 and 简体.
---

# Riverside transcript 繁转简 + 人名修正

Riverside 用 Whisper 转中文，经常简繁混杂。语言下拉只有 "Chinese"，没有简体选项，也没有一键繁转简。"Regenerate transcript" 解决不了问题，还会清掉所有手动修正，**不要用**。

本 skill 用的是编辑器里 Correct 按钮背后的同一个保存接口，一次改完全部段落。只改文字，不动时间轴、剪辑（删除线部分存在 edit 里，不在 transcript 里）和用户已有的手动修正。

> 这是网页编辑器的非公开接口，不是 Riverside 官方 API，随时可能变化。每一步都要先验证再继续。

## 前提

- 用户在 Chrome 里打开 Riverside 编辑器，URL 形如 `riverside.com/editor/<TAKE_ID>/<CLIP_ID>/preview`。用 Chrome 浏览器工具操作这个 tab。
- 开始前告诉用户：**处理期间别在这个 tab 里剪辑**，最后要刷新编辑器。
- workspace 里需要 OpenCC：`pip install --break-system-packages opencc`。

## 数据格式（已验证）

- GET `https://riverside.com/api/v4/transcriptions/editable/<TAKE_ID>`，带 `credentials:'include'` 即可。
- 返回 `{success, data:{speakers:[{id, name, sentences:[{index, words, wordSuggestions, editedWords?}]}]}}`。
- 每个词是 `[text, startMs, durationMs]`，噪音词是 `["", start, dur, "noise"]`。
- 显示的是 `editedWords`，没有的话才用 `words`。`editedWords` 和 `words` 长度、时间完全一致，只有文字不同。
- 保存用 PATCH 同一 URL，body 为 `{"speakers":[{"id":speakerId,"sentences":[{"index":n,"editedWords":[...]}]}]}`，成功返回 `{"success":true}`。
- PATCH 需要编辑器自己的请求头（Riverside-ID、版本、scope 等），通过第 3 步从编辑器请求里抓取。

## JS 工具注意事项

- 用 top-level `await`，不要写 async IIFE（会返回 `{}`）。
- 输出上限约 3KB。中文约 500 字一段分批输出。像 token、URL 参数的字符串可能被屏蔽，所以只输出必要的短结果。

## 步骤

### 1. 读取 transcript、备份、收集汉字

```js
const TAKE = location.pathname.split('/')[2];
const j = await (await fetch('https://riverside.com/api/v4/transcriptions/editable/' + TAKE, {credentials:'include'})).json();
window.__TAKE = TAKE; window.__tx = j; window.__txRaw = JSON.stringify(j);
let backup = false; try { localStorage.setItem('claude_tx_backup_' + TAKE, window.__txRaw); backup = true; } catch (e) {}
const set = new Set();
for (const s of j.data.speakers) for (const se of s.sentences) for (const w of (se.editedWords || se.words)) for (const c of (w[0] || '')) if (/[\u3400-\u9fff\uf900-\ufaff]/.test(c)) set.add(c);
window.__chars = [...set].join('');
({TAKE, backup, speakers: j.data.speakers.map(s => s.name + ':' + s.sentences.length), nChars: window.__chars.length})
```

然后分批取出 `window.__chars.slice(0,500)`、`slice(500,1000)`……，原样写进 workspace 的 `chars.txt`。

### 2. 用 OpenCC 生成对照表

```bash
python3 - <<'EOF'
import opencc
c = opencc.OpenCC('t2s')
u = open('chars.txt').read().strip()
m = {ch: c.convert(ch) for ch in u if c.convert(ch) != ch}
if '著' in u: m['著'] = '着'   # OpenCC 保留 著；口语里几乎都是助词 着
print(len(m)); print(''.join(k + v for k, v in m.items()))
EOF
```

把输出的成对字符串（繁简交替）注入页面并试跑：

```js
const PAIRS = "<粘贴成对字符串>";
const MAP = {}; { const a = [...PAIRS]; for (let i = 0; i < a.length; i += 2) MAP[a[i]] = a[i+1]; }
window.__MAP = MAP; window.__conv = w => [...w].map(c => MAP[c] || c).join('');
window.__buildPlan = (j) => { const plan = []; for (const s of j.data.speakers) { const sents = []; for (const se of s.sentences) { const cur = se.editedWords || se.words; const nw = cur.map(w => { const c = w.slice(); c[0] = window.__conv(w[0] || ''); return c; }); if (nw.some((w, i) => w[0] !== cur[i][0])) sents.push({index: se.index, editedWords: nw}); } if (sents.length) plan.push({id: s.id, sentences: sents}); } return plan; };
const ctx = []; for (const s of window.__tx.data.speakers) for (const se of s.sentences) { const cur = se.editedWords || se.words; cur.forEach((w, i) => { if ((w[0] || '').includes('著')) ctx.push(cur.slice(Math.max(0, i-3), i+4).map(x => x[0]).join(' ')); }); }
const plan = window.__buildPlan(window.__tx);
({sentences: plan.reduce((a, p) => a + p.sentences.length, 0), zhuoContexts: ctx.slice(0, 15)})
```

检查含 著 的上下文：著名、显著、著作、名著、土著这类要保留 著，其余都改成 着。有需要保留的，就在 `__conv` 里对那些词做例外处理。

### 3. 抓请求头（顺便手动修正一处）

先装 hook：

```js
if (!window.__netHooked) { window.__net = []; const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send, osh = XMLHttpRequest.prototype.setRequestHeader;
XMLHttpRequest.prototype.open = function(m, u) { this.__m = m; this.__u = String(u); this.__h = {}; return oo.apply(this, arguments); };
XMLHttpRequest.prototype.setRequestHeader = function(k, v) { if (this.__h) this.__h[k] = v; return osh.apply(this, arguments); };
XMLHttpRequest.prototype.send = function(b) { if (this.__u.includes('transcriptions/editable') && this.__m === 'PATCH') window.__net.push({h: this.__h}); return os.apply(this, arguments); };
window.__netHooked = true; } 'hooked'
```

然后在 UI 里修正一个繁体词：拖选或双击词 → 点 Correct → 运行 `document.querySelector('textarea').select()` → 输入简体 → 按 Enter（Enter 等于 Correct）。修正完运行 `window.__hdrs = window.__net[0].h; Object.keys(window.__hdrs)`。

### 4. 单句测试，再全量提交

```js
window.__patch = body => new Promise(res => { const x = new XMLHttpRequest(); x.open('PATCH', 'https://riverside.com/api/v4/transcriptions/editable/' + window.__TAKE); x.withCredentials = true; for (const [k, v] of Object.entries(window.__hdrs)) if (k.toLowerCase() !== 'traceparent') x.setRequestHeader(k, v); x.onload = () => res({status: x.status, text: x.responseText}); x.onerror = () => res({status: -1}); x.send(JSON.stringify(body)); });
window.__getTx = async () => (await fetch('https://riverside.com/api/v4/transcriptions/editable/' + window.__TAKE, {credentials:'include'})).json();
```

- **测试**：从 `__buildPlan(await __getTx())` 里挑最短的一句，单独 PATCH，再 GET 确认这句的 `editedWords` 变了，而 `words` 和时间没变。
- **全量**：PATCH 前重新 GET，用最新数据 `__buildPlan`，防止覆盖用户刚做的修改。每个 speaker 发一个 PATCH。
- **验证**：再 GET 一次，统计当前文字里还能被 `__MAP` 命中的字，必须是 0；逐词比对 start/duration 与 PATCH 前完全一致。

### 5. 刷新编辑器

刷新前确认顶部云图标是已保存状态，然后重新打开同一 URL，等约 20 秒。不刷新的话，编辑器内存里还是旧文字，下次手动 Correct 时会把那一句改回去。

刷新后的已知情况：
- 时间轴可能变成合并的一条轨道，用锁形图标右边那组开关切回分轨视图。
- 播放速度会变回 1×，告诉用户自己调回去就行。
- 曾出现预览字幕中文显示方块 □、英文正常的情况。Riverside 是按语言 zh 同时加载 Noto Sans SC 和 TC，没碰过的句子也是方块，所以判断是预览字体加载问题，与简繁无关，但未百分之百确认。要提醒用户导出前检查字幕；如果一直是方块，可以从备份恢复做对比（见下）。

### 6. 修正人名（走 UI，不用刷新）

先问用户：节目里有哪些名字（主持人、嘉宾、节目名）、Whisper 常听成什么字。例如主持人「Ming」可能被识别成 明 / 鸣 / 铭。然后列出疑似位置，把 `明鸣铭` 换成实际的候选字：

```js
const re = /[明鸣铭]/;
const j2 = await window.__getTx(); const out = [];
for (const s of j2.data.speakers) for (const se of s.sentences) { const cur = se.editedWords || se.words; cur.forEach((w, i) => { if (re.test(w[0] || '')) { const ms = w[1]; out.push(s.name + ' ' + Math.floor(ms/60000) + ':' + String(Math.floor(ms/1000)%60).padStart(2,'0') + ' [' + w[0] + '] ' + cur.slice(Math.max(0, i-4), i+5).map(x => x[0]).join(' ')); } }); }
out
```

- 按上下文判断，只改确实指人名的地方。成语和普通词不要动，比如「夏虫不可语冰」「秀才遇到兵」「嘉宾」这类。
- 操作：在搜索框搜这个字，用上下箭头跳到目标，双击该词 → Correct → `textarea.select()` → 输入正确名字 → 按 Enter。只有当这个词的**所有**出现都是人名时，才用 "Correct all"。
- 节目名被听错（比如听成同音词）也一并修正。
- **不要**擅自打开 "Add to dictionary"：这是 studio 级的长期设置，要先问用户。即使用户同意，也只加名字本身，绝不加「某个常用字 → 人名」这类替换规则，否则以后正常的词会被改错。

## 从备份恢复

```js
const b = JSON.parse(localStorage.getItem('claude_tx_backup_' + window.__TAKE));
for (const s of b.data.speakers) await window.__patch({speakers: [{id: s.id, sentences: s.sentences.map(se => ({index: se.index, editedWords: se.editedWords || se.words}))}]});
```

需要先有 `__hdrs`（第 3 步）。恢复后刷新编辑器。

## 给用户的汇报（简短）

- 改了多少词、多少段，已在服务器端验证繁体为 0。
- 时间轴、剪辑、之前的手动修正都保留。
- 人名修正逐条列出时间点，并说明哪些成语没动。
- 提醒导出前检查预览字幕，说明备份在浏览器里，可以恢复。
