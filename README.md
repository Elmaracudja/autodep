# autodep

Système de déploiement pour GH.

Ce projet fournit un outil Python de déploiement qui génère automatiquement un site vidéo statique à partir du contenu du dossier `videos/`. Il scanne les fichiers présents, construit une playlist, crée les fichiers web nécessaires et produit un lecteur léger qui affiche les titres des vidéos sans exposer les noms de fichiers. L’objectif est de servir de base propre, réutilisable et simple à adapter pour lancer rapidement plusieurs sites vidéo sur GitHub.

Le script peut aussi générer des fichiers de test `.jpg` et `.mp4` dans les dossiers de destination prévus afin de valider rapidement que l’arborescence et les exports fonctionnent correctement [web:1736][web:1754][web:1758].

## Fonctionnement

- Le dossier `videos/` contient les vidéos sources.
- Le script crée les fichiers du site statique.
- Le script peut créer des médias de test `.jpg` et `.mp4`.
- Les dossiers de sortie sont créés automatiquement si besoin [web:1753][web:1749].

## Lancement

```bash
python deploy_site.py
```

Si `python` ne pointe pas vers Python 3 dans ton environnement, utilise :

```bash
python3 deploy_site.py
```

## Dossiers

- `videos/` : vidéos source.
- `deploy-logs/` : journal de déploiement.
- `tests/` : fichiers de test générés.
- `assets/` : ressources statiques si besoin.
