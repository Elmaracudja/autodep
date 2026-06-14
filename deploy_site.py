#!/usr/bin/env python3
import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VIDEOS = ROOT / "videos"
ASSETS = ROOT / "assets"
OUT = ROOT
LOG_DIR = ROOT / "deploy-logs"

PLAYLIST_JSON = OUT / "playlist.json"
INDEX_HTML = OUT / "index.html"
SCRIPT_JS = OUT / "script.js"
STYLE_CSS = OUT / "style.css"
README_MD = OUT / "README.md"
DEPLOY_LOG = LOG_DIR / "deploy.log"

VIDEO_EXTS = {".mp4", ".m4v", ".webm", ".mov", ".ogg"}

DEFAULT_AUTHOR = "EKWallegory Prod"
DEFAULT_CHANNEL = "EM101 Webradio"

HTML = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Autolist</title>
  <link rel="stylesheet" href="./style.css">
</head>
<body>
  <main class="app">
    <header class="hero">
      <p class="eyebrow">Lecture vidéo automatique</p>
      <h1 id="videoTitle">Chargement…</h1>
      <p id="videoDescription" class="description"></p>
      <p id="videoMeta" class="meta"></p>
    </header>

    <section class="player-shell">
      <video
        id="player"
        controls
        autoplay
        muted
        playsinline
        preload="metadata"
        controlslist="nodownload noremoteplayback"
        disablepictureinpicture
        oncontextmenu="return false;"
      ></video>
    </section>

    <section class="playlist-shell">
      <div class="playlist-head">
        <h2>Playlist</h2>
        <p id="playlistCount">0 vidéo</p>
      </div>
      <ul id="playlistList" class="playlist-list"></ul>
    </section>
  </main>
  <script src="./script.js" defer></script>
</body>
</html>
"""

CSS = """:root{
  color-scheme: dark;
  --bg:#0c1118;
  --panel:#121a23;
  --panel2:#182231;
  --text:#eef4fb;
  --muted:#98a6b7;
  --line:rgba(255,255,255,.12);
  --accent:#39c7ff;
  --radius:18px;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  min-height:100vh;
  font-family:Inter,Arial,sans-serif;
  background:radial-gradient(circle at top, rgba(57,199,255,.12), transparent 30%), linear-gradient(180deg,#0c1118 0%,#101923 100%);
  color:var(--text);
}
.app{
  width:min(1100px, calc(100% - 32px));
  margin:0 auto;
  padding:24px 0 48px;
}
.hero,.player-shell,.playlist-shell{
  background:rgba(18,26,35,.92);
  border:1px solid var(--line);
  border-radius:var(--radius);
  box-shadow:0 18px 60px rgba(0,0,0,.32);
}
.hero{padding:24px;margin-bottom:20px}
.eyebrow{
  margin:0 0 8px;
  text-transform:uppercase;
  letter-spacing:.08em;
  color:var(--accent);
  font-size:.8rem;
}
h1{margin:0 0 10px;font-size:clamp(1.8rem,3vw,2.8rem)}
.description,.meta{margin:0;color:var(--muted)}
.player-shell{overflow:hidden;margin-bottom:20px;background:#000}
video{display:block;width:100%;aspect-ratio:16/9;background:#000}
.playlist-shell{padding:20px 24px 24px}
.playlist-head{display:flex;justify-content:space-between;gap:16px;align-items:center;margin-bottom:16px}
.playlist-head h2,.playlist-head p{margin:0}
.playlist-list{list-style:none;margin:0;padding:0;display:grid;gap:12px}
.playlist-item{
  width:100%;
  border:1px solid var(--line);
  background:var(--panel2);
  color:var(--text);
  border-radius:14px;
  padding:14px 16px;
  text-align:left;
  cursor:pointer;
}
.playlist-item:hover,.playlist-item:focus-visible{border-color:rgba(57,199,255,.55);outline:none}
.playlist-item.active{background:rgba(57,199,255,.14);border-color:rgba(57,199,255,.65)}
.playlist-item-title{margin:0 0 4px;font-size:1rem}
.playlist-item-meta{margin:0;color:var(--muted);font-size:.92rem}
.empty-state{color:var(--muted);padding:18px;border:1px dashed var(--line);border-radius:14px}
@media (max-width:780px){.playlist-head{flex-direction:column;align-items:flex-start}}
"""

JS = """const player = document.getElementById('player');
const titleEl = document.getElementById('videoTitle');
const descEl = document.getElementById('videoDescription');
const metaEl = document.getElementById('videoMeta');
const playlistList = document.getElementById('playlistList');
const playlistCount = document.getElementById('playlistCount');

let playlist = [];
let currentIndex = 0;

function renderPlaylist() {
  playlistList.innerHTML = '';
  playlistCount.textContent = `${playlist.length} vidéo${playlist.length > 1 ? 's' : ''}`;

  if (!playlist.length) {
    playlistList.innerHTML = '<li class="empty-state">Aucune vidéo détectée dans videos/.</li>';
    return;
  }

  playlist.forEach((item, index) => {
    const li = document.createElement('li');
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'playlist-item';
    if (index === currentIndex) btn.classList.add('active');
    btn.innerHTML = `<p class="playlist-item-title">${item.title}</p><p class="playlist-item-meta">${item.channel || ''}</p>`;
    btn.addEventListener('click', () => loadVideo(index, true));
    li.appendChild(btn);
    playlistList.appendChild(li);
  });
}

function updateMeta(item) {
  titleEl.textContent = item.title || 'Sans titre';
  descEl.textContent = item.description || '';
  metaEl.textContent = [item.author, item.channel].filter(Boolean).join(' · ');
}

function loadVideo(index, autoplay = true) {
  currentIndex = index;
  const item = playlist[index];
  player.src = item.src;
  player.load();
  updateMeta(item);
  renderPlaylist();
  if (autoplay) player.play().catch(() => {});
}

function nextVideo() {
  if (!playlist.length) return;
  loadVideo((currentIndex + 1) % playlist.length, true);
}

async function init() {
  document.addEventListener('contextmenu', e => e.preventDefault());

  try {
    const response = await fetch('./playlist.json', { cache: 'no-store' });
    const data = await response.json();
    playlist = Array.isArray(data.playlist) ? data.playlist : [];
    renderPlaylist();

    if (playlist.length) {
      loadVideo(0, true);
    } else {
      updateMeta({
        title: 'Aucune vidéo disponible',
        description: 'Dépose des fichiers dans videos/ puis relance le déploiement.',
        author: '',
        channel: ''
      });
    }
  } catch (error) {
    titleEl.textContent = 'Erreur de chargement';
    descEl.textContent = 'Impossible de lire playlist.json.';
    metaEl.textContent = '';
    playlistList.innerHTML = '<li class="empty-state">Erreur de chargement de la playlist.</li>';
    console.error(error);
  }
}

player.addEventListener('ended', nextVideo);
init();
"""

README = """# Autolist

Ce projet génère automatiquement un site vidéo statique à partir du contenu du dossier `videos/`.

## Principe

Le script scanne les fichiers vidéo présents, construit une playlist, génère les fichiers web nécessaires et affiche uniquement des titres lisibles dans l’interface, sans exposer les noms de fichiers.

## Usage

```bash
python deploy_site.py
```

## Dossiers

- `videos/` : vidéos source.
- `assets/` : ressources optionnelles.
- `deploy-logs/` : journal de déploiement.
"""

def log(msg):
    LOG_DIR.mkdir(exist_ok=True)
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    with DEPLOY_LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def slug_to_title(name):
    stem = Path(name).stem
    stem = re.sub(r"[_-]+", " ", stem)
    stem = re.sub(r"(?<=[a-z])(?=[A-Z0-9])", " ", stem)
    stem = re.sub(r"\s+", " ", stem).strip()
    return stem.title() if stem else "Sans titre"

def scan_videos():
    VIDEOS.mkdir(exist_ok=True)
    return sorted([p for p in VIDEOS.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTS], key=lambda p: p.name.lower())

def build_playlist():
    items = []
    for i, p in enumerate(scan_videos(), start=1):
        title = slug_to_title(p.name)
        items.append({
            "id": i,
            "title": title,
            "src": f"./videos/{p.name}",
            "author": DEFAULT_AUTHOR,
            "channel": DEFAULT_CHANNEL,
            "description": f"Vidéo {i}: {title}."
        })
    return items

def write_text(path, content):
    path.write_text(content, encoding="utf-8")

def generate():
    playlist = build_playlist()
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "playlist": playlist
    }
    write_text(PLAYLIST_JSON, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    write_text(INDEX_HTML, HTML)
    write_text(SCRIPT_JS, JS)
    write_text(STYLE_CSS, CSS)
    write_text(README_MD, README)
    log(f"Build terminé: {len(playlist)} vidéo(s) détectée(s).")
    for item in playlist:
        log(f"OK: {item['src']} -> {item['title']}")
    if not playlist:
        log("INFO: aucun média détecté dans videos/.")

def main():
    parser = argparse.ArgumentParser(description="Déploie un site vidéo statique depuis videos/.")
    parser.parse_args()
    log("Déploiement lancé.")
    generate()
    log("Déploiement terminé.")

if __name__ == "__main__":
    main()
