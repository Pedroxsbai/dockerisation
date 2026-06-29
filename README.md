#  Dockerisation — Projet 1 & Projet 2

> Stratégie de conteneurisation pour les deux projets du stage. Ces Dockerfiles sont volontairement **minimalistes** ("hello-world") pour que toute la chaîne CI/CD (build → ECR → ECS) soit testable **sans attendre le vrai code applicatif**.

---

##  Vue d'ensemble

| Service | Stack | Port | Repo cible |
|---|---|---|---|
| `projet1-backend` | Laravel (PHP 8.3) + Nginx | 80 | `projet1-backend` |
| `projet1-ai-service` | FastAPI (Python 3.12) | 8000 | `projet1-ai-service` |
| `projet1-frontend` | React + Nginx | 80 | `projet1-frontend` |
| `projet2-orchestrator` | FastAPI (Python 3.12) | 8000 | `projet2-orchestrator` |

---

##  Stratégie "hello-world first"

Chaque Dockerfile expose un endpoint `/health` retournant `{"status": "ok"}`. Ça permet :

1. **De tester toute la chaîne CI/CD** dès maintenant (build → push ECR → deploy ECS) sans attendre le code applicatif
2. **De fournir un template** aux devs sur lequel greffer leur code
3. **De valider l'infra** avant le développement métier
4. **De découpler** le travail DevOps du travail applicatif

Quand le vrai code arrive, on **remplace juste le contenu de l'app** — Dockerfile, structure et pipeline restent identiques.

---

##  Bonnes pratiques appliquées partout

Chaque Dockerfile suit ces principes :

### 1. Multi-stage build
Sépare la phase de **build** (compilation, install des dépendances) de la phase **runtime** (image finale). Résultat : image finale **3 à 10× plus petite** = pull plus rapide sur ECS = scaling plus réactif + moins cher.

### 2. Utilisateur non-root
Chaque conteneur tourne sous un utilisateur dédié (`spring`, `appuser`). Si un attaquant compromet l'app, il n'a pas les droits root dans le conteneur. **Exigence de base en production.**

### 3. Health check intégré
Le `HEALTHCHECK` permet à Docker (et plus tard à ECS) de savoir si le conteneur fonctionne réellement, pas juste s'il est démarré. ECS s'en sert pour décider quand redémarrer un conteneur défaillant.

### 4. Cache des dépendances optimisé
Les fichiers de dépendances (`pom.xml`, `requirements.txt`, `package.json`) sont copiés **avant** le code source. Comme ils changent rarement, Docker met en cache l'étape d'installation. Conséquence : un build après modification d'une ligne de code prend **5 secondes** au lieu de 3 minutes.

### 5. `.dockerignore` strict
Exclut tout ce qui n'a pas besoin d'être dans l'image (tests, IDE, `.git`, logs, docs). Réduit la taille du contexte de build et évite de leaker des fichiers sensibles.

### 6. Images de base "slim" ou "alpine"
- **Alpine** (5 MB) : ultra léger, mais peut poser souci avec certaines libs Python compilées (musl vs glibc)
- **Slim** (~80 MB) : Debian épuré, compromis idéal pour Python avec des libs natives (NumPy, etc.)

---

##  Comment tester en local

### Tester un service isolé

```bash
# Backend Laravel
cd projet1-backend
docker build -t projet1-backend:dev .
docker run -p 8080:80 projet1-backend:dev
curl http://localhost:8080/health

# Service IA Python
cd projet1-ai-service
docker build -t projet1-ai-service:dev .
docker run -p 8000:8000 projet1-ai-service:dev
curl http://localhost:8000/health

# Frontend
cd projet1-frontend
docker build -t projet1-frontend:dev .
docker run -p 3000:80 projet1-frontend:dev
curl http://localhost:3000/health
```

### Tester tout en même temps (Projet 1)

```bash
docker compose up --build
```

Lance Postgres + pgvector + backend + service IA + frontend, tous interconnectés. Pratique pour le dev local avant déploiement ECS.

---

##  Cycle de vie d'une image (du commit à la prod)

```
1. Dev push code dans projet1-backend
       ↓
2. GitHub Actions :
   - Lint + tests
   - docker build avec tag = SHA du commit (ex: a3f8b9c)
   - Scan de vulnérabilités (Trivy)
   - docker push vers ECR
       ↓
3. ECS récupère la nouvelle image et redémarre les tâches (rolling update)
       ↓
4. ALB redirige progressivement le trafic vers les nouveaux conteneurs
```

### Convention de tagging
- `<sha-commit>` → traçabilité exacte (ex: `a3f8b9c`)
- `dev-latest` / `prod-latest` → pratique pour les déploiements, mais à éviter en prod (préférer le SHA)

---

##  Sécurité — checklist avant de passer en prod

- [ ] Aucun secret en dur dans le Dockerfile (utiliser Secrets Manager + variables d'env injectées par ECS)
- [ ] Utilisateur non-root activé ✅ (déjà fait)
- [ ] Image scannée par Trivy ou ECR scan (à activer côté ECR)
- [ ] Image basée sur une version **figée** (`python:3.12-slim`, pas `python:latest`)
- [ ] `.dockerignore` à jour (pas de `.env` ni de `.git` dans l'image)
- [ ] Health check qui teste vraiment l'app, pas juste `return 200`

---

##  Pourquoi pas une seule image qui contient tout ?

Question fréquente : *"Pourquoi 3 images séparées pour le Projet 1 ? Pourquoi pas tout dans une seule ?"*

**Réponse** : chaque service a son propre cycle de vie. Le backend peut être redéployé sans toucher au service IA. Le service IA peut scaler à 5 instances pendant que le backend reste à 2. Une seule image = couplage fort, scaling impossible, redéploiement de tout pour un changement minime. C'est exactement ce qu'on veut éviter en passant aux conteneurs.

---

##  Pour la suite

Une fois que ces Dockerfiles tournent en local et sont pushés sur ECR, les prochaines étapes côté infra sont :

1. Provisionner ECR (un repo par service) via Terraform
2. Provisionner ECS Fargate + cluster + service + task definition
3. Connecter le pipeline GitHub Actions à ECR (auth OIDC, sans clés statiques)
4. Configurer le rolling deployment ECS pour zéro downtime

Tous les Dockerfiles seront alors **prêts à l'emploi** sans changement.
