# 🎙️ Riverside Simplified Transcript Skill for Claude

A Claude skill that turns a **mixed Traditional / Simplified Chinese** transcript in the Riverside editor into **clean Simplified Chinese** in one pass — without touching your timings, cuts, or the corrections you've already made. It then helps you fix names that Whisper mis-heard.

Riverside 的中文转录经常简繁混杂，而它只有 "Chinese" 一个选项，没有简体，也没有一键繁转简。这个 skill 让 Claude 帮你一次性全部改成简体。

---

## ✨ Highlights

- **Whole episode in minutes**: converts every paragraph for every speaker at once, no word-by-word "Correct" clicking
- **Nothing else moves**: word timings, cuts (struck-through text) and your manual fixes stay exactly as they were
- **Phrase-aware conversion**: uses [OpenCC](https://github.com/BYVoid/OpenCC); handles 著 → 着 in spoken Chinese while keeping 著名 / 显著
- **Verified, with a backup**: tests on one sentence first, confirms zero Traditional characters remain afterwards, and keeps a backup in your browser so you can roll back
- **Name clean-up**: finds names that were heard as homophones and fixes only the real ones, leaving idioms like 夏虫不可语冰 alone

---

## 📦 Install

1. Download [`riverside-simplified-transcript.skill`](./riverside-simplified-transcript.skill)
2. Open **Claude** → Settings → Capabilities → Skills
3. Click **Save skill** on the downloaded file

Requires Claude with browser access to Chrome (Claude in Chrome), plus a workspace where it can `pip install opencc`.

---

## 🚀 Use

Open your episode in the Riverside editor in Chrome, then say:

> 把 Riverside 的 transcript 全部改成简体  
> Convert my Riverside transcript to Simplified Chinese

Don't edit in that tab while Claude works. When it's done, Claude reloads the editor and reports what changed.

---

## ⚠️ Notes

- This uses the same save mechanism as the Riverside web editor's **Correct** button. It is **not an official Riverside API**, may change without notice, and isn't affiliated with or endorsed by Riverside. Use at your own risk.
- Don't use **Regenerate transcript** to fix Simplified/Traditional: it doesn't help, and it wipes your manual corrections.
- After the reload, check the caption preview before exporting.

---

## 📁 Files

```
SKILL.md                                  ← skill instructions (what Claude reads)
riverside-simplified-transcript.skill     ← installable package
README.md
```

---

Made with [Claude](https://claude.ai) · Built by [@randing-create](https://github.com/randing-create)
