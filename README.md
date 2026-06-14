# autodep
Système de déploiement pour GH
Ce projet fournit un outil Python de déploiement qui génère automatiquement un site vidéo statique à partir du contenu du dossier `videos/`. Il scanne les fichiers présents, construit une playlist, crée les fichiers web nécessaires et produit un lecteur léger qui affiche les titres des vidéos sans exposer les noms de fichiers. L’objectif est de servir de base propre, réutilisable et simple à adapter pour lancer rapidement plusieurs sites vidéo sur GitHub.

# Autolist

Ce projet génère automatiquement un site vidéo statique à partir du contenu du dossier `videos/`.

## Principe

Le script scanne les fichiers vidéo présents, construit une playlist, génère les fichiers web nécessaires et affiche uniquement des titres lisibles dans l’interface, sans exposer les noms de fichiers.

## Usage

```bash
python deploy_site.py
```

## Dossiers

- `videos/` : vidéos source.
- `deploy-logs/` : journal de déploiement.
