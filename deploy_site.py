from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VIDEOS_DIR = ROOT / "videos"
LOGS_DIR = ROOT / "deploy-logs"
TESTS_DIR = ROOT / "tests"
ASSETS_DIR = ROOT / "assets"
TEST_IMAGES_DIR = TESTS_DIR / "images"
TEST_VIDEOS_DIR = TESTS_DIR / "videos"

SITE_TITLE = "autodep"
SITE_DESCRIPTION = (
    "Système de déploiement pour GH. Ce site statique est généré automatiquement "
    "à partir du dossier videos/."
)

VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".mkv", ".avi"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

README = """# autodep

Système de déploiement pour GH.

Ce projet fournit un outil Python de déploiement qui génère automatiquement un site vidéo statique à partir du contenu du dossier `videos/`. Il scanne les fichiers présents, construit une playlist, crée les fichiers web nécessaires et produit un lecteur léger qui affiche les titres des vidéos sans exposer les noms de fichiers. L’objectif est de servir de base propre, réutilisable et simple à adapter pour lancer rapidement plusieurs sites vidéo sur GitHub.

Le script peut aussi générer des fichiers de test `.jpg` et `.mp4` dans les dossiers de destination prévus afin de valider rapidement que l’arborescence et les exports fonctionnent correctement.

## Fonctionnement

- Le dossier `videos/` contient les vidéos sources.
- Le script crée les fichiers du site statique.
- Le script peut créer des médias de test `.jpg` et `.mp4`.
- Les dossiers de sortie sont créés automatiquement si besoin.

## Lancement

```bash
python deploy_site.py
```

Si `python` ne pointe pas vers Python 3 dans ton environnement, utilise :

```bash
python3 deploy_site.py
```

## Mode automatique

Pour activer la surveillance du dossier `videos/` et régénérer la playlist dès qu’un fichier change :

```bash
python deploy_site.py --watch
```

## Dossiers

- `videos/` : vidéos source.
- `deploy-logs/` : journal de déploiement.
- `tests/` : fichiers de test générés.
- `assets/` : ressources statiques si besoin.
"""

PLAYLIST_JSON = ROOT / "playlist.json"
INDEX_HTML = ROOT / "index.html"
SCRIPT_JS = ROOT / "script.js"
STYLE_CSS = ROOT / "style.css"
README_MD = ROOT / "README.md"


def slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name.lower()).strip("-")
    return s or "video"


def ensure_dirs() -> None:
    for path in [LOGS_DIR, TESTS_DIR, ASSETS_DIR, TEST_IMAGES_DIR, TEST_VIDEOS_DIR, VIDEOS_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def collect_videos() -> list[dict]:
    items = []
    for path in sorted(VIDEOS_DIR.iterdir()):
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            title = path.stem.replace("_", " ").replace("-", " ").strip()
            items.append(
                {
                    "title": title or path.stem,
                    "filename": path.name,
                    "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                }
            )
    return items


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_test_jpg() -> Path:
    target = TEST_IMAGES_DIR / "test-image.jpg"
    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (1280, 720), (32, 96, 160))
        draw = ImageDraw.Draw(img)
        draw.rectangle((60, 60, 1220, 660), outline=(255, 255, 255), width=8)
        draw.text((100, 120), "autodep test JPG", fill=(255, 255, 255))
        draw.text((100, 180), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), fill=(240, 240, 240))
        img.save(target, format="JPEG", quality=92)
    except Exception:
        target.write_bytes(b"")
    return target


def generate_test_mp4() -> Path:
    target = TEST_VIDEOS_DIR / "test-video.mp4"
    try:
        import cv2
        import numpy as np

        width, height = 1280, 720
        fps = 24
        seconds = 2
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(target), fourcc, fps, (width, height))

        for i in range(fps * seconds):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:] = (40, 80, 140)
            cv2.rectangle(frame, (60, 60), (1220, 660), (255, 255, 255), 6)
            cv2.putText(frame, "autodep test MP4", (100, 140), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4)
            cv2.putText(
                frame,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                (100, 220),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (240, 240, 240),
                3,
            )
            cv2.putText(frame, f"frame {i+1}", (100, 300), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (240, 240, 240), 3)
            writer.write(frame)

        writer.release()
    except Exception:
        target.write_bytes(b"")
    return target


def build_playlist(videos: list[dict]) -> list[dict]:
    playlist = []
    for idx, item in enumerate(videos, start=1):
        playlist.append(
            {
                "id": idx,
                "title": item["title"],
                "src": item["path"],
            }
        )
    return playlist


def render_html(playlist: list[dict]) -> str:
    items = "\n".join(
        f'<li><button data-src="{v["src"]}">{v["title"]}</button></li>' for v in playlist
    ) or "<li>Aucune vidéo trouvée dans le dossier videos/.</li>"

    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{SITE_TITLE}</title>
  <meta name="description" content="{SITE_DESCRIPTION}">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <main class="app">
    <header>
      <h1>{SITE_TITLE}</h1>
      <p>{SITE_DESCRIPTION}</p>
    </header>

    <section class="layout">
      <div class="player">
        <video id="player" controls playsinline></video>
      </div>

      <aside class="playlist">
        <h2>Vidéos</h2>
        <ul id="playlist">
          {items}
        </ul>
      </aside>
    </section>
  </main>
  <script src="script.js"></script>
</body>
</html>
"""


def render_css() -> str:
    return """
:root {
  --bg: #0b1020;
  --panel: #11182d;
  --text: #e8eefc;
  --muted: #aab6d6;
  --accent: #5d8cff;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: system-ui, sans-serif;
  background: linear-gradient(180deg, #08101f, var(--bg));
  color: var(--text);
}

.app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

.player, .playlist {
  background: rgba(17, 24, 45, 0.95);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 16px;
  padding: 16px;
}

video {
  width: 100%;
  border-radius: 12px;
  background: #000;
}

ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

li + li {
  margin-top: 8px;
}

button {
  width: 100%;
  text-align: left;
  padding: 12px 14px;
  border: 0;
  border-radius: 10px;
  background: #17213d;
  color: var(--text);
  cursor: pointer;
}

button:hover {
  background: var(--accent);
}
"""


def render_js(playlist: list[dict]) -> str:
    return f"""
const playlist = {json.dumps(playlist, ensure_ascii=False, indent=2)};
const player = document.getElementById('player');
const buttons = document.querySelectorAll('#playlist button');

function play(src) {{
  player.src = src;
  player.play().catch(() => {{}});
}}

buttons.forEach((button) => {{
  button.addEventListener('click', () => play(button.dataset.src));
}});

if (playlist.length > 0) {{
  play(playlist[0].src);
}}
"""


def generate() -> None:
    ensure_dirs()
    videos = collect_videos()
    playlist = build_playlist(videos)

    write_json(PLAYLIST_JSON, playlist)
    write_text(INDEX_HTML, render_html(playlist))
    write_text(SCRIPT_JS, render_js(playlist))
    write_text(STYLE_CSS, render_css())
    write_text(README_MD, README)

    generate_test_jpg()
    generate_test_mp4()

    log = LOGS_DIR / f"deploy-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    log.write_text(
        f"Generated at {datetime.now().isoformat()}\n"
        f"Videos: {len(videos)}\n"
        f"Playlist: {len(playlist)}\n",
        encoding="utf-8",
    )


def watch_loop(interval: float = 1.0) -> None:
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except Exception:
        print("watchdog n'est pas installé. Lance: python -m pip install watchdog")
        return

    class Handler(FileSystemEventHandler):
        def __init__(self) -> None:
            self._last = 0.0

        def on_any_event(self, event) -> None:
            if event.is_directory:
                return
            now = time.time()
            if now - self._last < 0.5:
                return
            self._last = now
            generate()
            print(f"[watch] régénération après changement: {event.src_path}")

    generate()
    handler = Handler()
    observer = Observer()
    observer.schedule(handler, str(VIDEOS_DIR), recursive=True)
    observer.start()
    print(f"[watch] surveillance active sur: {VIDEOS_DIR}")
    try:
        while True:
            time.sleep(interval)
    except KeyboardInterrupt:
        print("[watch] arrêt demandé")
    finally:
        observer.stop()
        observer.join()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true", help="Surveille videos/ et régénère automatiquement.")
    args = parser.parse_args()
    if args.watch:
        watch_loop()
    else:
        generate()


if __name__ == "__main__":
    main()
