# CLAUDE.md — MediaCleaner Project

> Document de compréhension du projet, contraintes, décisions d'architecture,
> conventions de développement et plan d'évolution.

---

## 1. Compréhension du projet

### Contexte
L'utilisateur possède un serveur multimédia (TrueNAS Scale) avec un pipeline de téléchargement automatisé :
- **Sonarr** gère les séries TV (recherche, téléchargement, importation, upgrades qualité)
- **Radarr** gère les films (idem)
- **qBittorrent** est le client de téléchargement torrent
- **Emby** est le serveur multimédia de lecture

### Problème identifié
Sonarr et Radarr téléchargent régulièrement plusieurs releases successives d'un même contenu
(upgrades de qualité) avant d'atteindre le score de qualité souhaité. Seule la dernière release
est conservée dans la bibliothèque Emby, mais les anciennes releases restent dans le dossier
de téléchargement (`/mnt/Downloads`), occupant potentiellement plusieurs To inutilement.

### Objectif
Développer une application web permettant de :
1. Identifier intelligemment les releases devenues inutiles dans `/mnt/Downloads`
2. Présenter ces releases à l'utilisateur avec des explications claires
3. Permettre la suppression après validation explicite de l'utilisateur
4. Ne jamais supprimer automatiquement — sécurité absolue

---

## 2. Contraintes

### Contraintes techniques
- **Docker** : l'application doit fonctionner dans un conteneur Docker
- **TrueNAS Scale** : compatibilité avec l'environnement TrueNAS (Electric Eel 24.10+)
- **ZFS** : prise en compte du système de fichiers ZFS et de ses spécificités
- **Hardlinks** : gestion critique — ZFS ne supporte les hardlinks qu'au sein d'un même dataset
- **Linux** : droits d'accès, inodes 64 bits, montages bind

### Contraintes fonctionnelles
- Utilisation des API Sonarr v3, Radarr v3, qBittorrent Web API v2
- Analyse du dossier `/mnt/Downloads`
- Base de données locale persistante
- Interface web moderne
- Rescans à la demande
- Protection Hit & Run (7 jours minimum)

### Contraintes de sécurité
- **AUCUNE** suppression automatique
- Validation explicite obligatoire pour chaque suppression
- Affichage complet des informations avant suppression (fichiers, raison, taille, gain réel, risques)

---

## 3. Décisions d'architecture

### 3.1 Stack technique

| Composant | Choix | Justification |
|-----------|-------|---------------|
| **Backend** | Python 3.12 + FastAPI | Excellent support des APIs REST, async natif, typage fort, large écosystème, idéal pour I/O réseau + filesystem |
| **Base de données** | SQLite (via SQLAlchemy + Alembic) | Léger, sans serveur, parfait pour une app single-node sur TrueNAS, migrations versionnées |
| **Frontend** | React 18 + TypeScript + Vite | UI moderne, réactive, composants réutilisables, build rapide |
| **UI Framework** | shadcn/ui + Tailwind CSS | Design moderne, accessible, personnalisable, dark mode natif |
| **Conteneurisation** | Docker multi-stage build | Image légère, séparation build/runtime |
| **Scheduler** | APScheduler (intégré) | Scans programmés sans dépendance externe |

### 3.2 Architecture applicative

```
┌─────────────────────────────────────────────────────┐
│                   Docker Container                   │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │             Frontend (React/Vite)             │   │
│  │  Servi en statique par le backend FastAPI     │   │
│  └──────────────────────┬───────────────────────┘   │
│                         │ REST API                   │
│  ┌──────────────────────▼───────────────────────┐   │
│  │            Backend (FastAPI)                   │   │
│  │                                               │   │
│  │  ┌─────────┐  ┌──────────┐  ┌─────────────┐ │   │
│  │  │ Scanner │  │ Analyzer │  │  Deleter     │ │   │
│  │  │ Service │  │ Service  │  │  Service     │ │   │
│  │  └────┬────┘  └────┬─────┘  └──────┬──────┘ │   │
│  │       │             │               │         │   │
│  │  ┌────▼─────────────▼───────────────▼──────┐ │   │
│  │  │         Core Services Layer              │ │   │
│  │  │                                          │ │   │
│  │  │  ┌───────────┐ ┌───────────┐ ┌────────┐│ │   │
│  │  │  │ Sonarr    │ │ Radarr    │ │ qBit   ││ │   │
│  │  │  │ Client    │ │ Client    │ │ Client ││ │   │
│  │  │  └───────────┘ └───────────┘ └────────┘│ │   │
│  │  │  ┌───────────┐ ┌───────────────────────┐│ │   │
│  │  │  │ Filesystem│ │ Hardlink              ││ │   │
│  │  │  │ Service   │ │ Analyzer              ││ │   │
│  │  │  └───────────┘ └───────────────────────┘│ │   │
│  │  └─────────────────────────────────────────┘ │   │
│  │                                               │   │
│  │  ┌───────────────────────────────────────────┐│   │
│  │  │          SQLite Database                   ││   │
│  │  └───────────────────────────────────────────┘│   │
│  └───────────────────────────────────────────────┘   │
│                                                     │
│  Volumes montés :                                   │
│   - /mnt/Downloads → /downloads (lecture + suppr.)  │
│   - /mnt/.../media → /media (lecture seule)         │
│   - /config → persistance DB + config               │
└─────────────────────────────────────────────────────┘
```

### 3.3 Stratégie d'identification des releases orphelines

La stratégie repose sur un **croisement multi-sources** en 4 étapes :

#### Étape 1 — Inventaire du filesystem
Scanner récursivement `/mnt/Downloads` pour indexer tous les fichiers vidéo
(extensions : `.mkv`, `.mp4`, `.avi`, `.ts`, `.wmv`, etc.) avec leurs métadonnées :
- Chemin absolu
- Taille
- Date de modification
- Inode (`st_ino`) et device ID (`st_dev`)
- Nombre de hardlinks (`st_nlink`)

#### Étape 2 — Consultation des API Sonarr/Radarr
Interroger les API pour déterminer quels fichiers sont **actuellement utilisés** :

**Sonarr :**
- `GET /api/v3/series` → liste de toutes les séries
- `GET /api/v3/episodefile?seriesId=X` → fichiers actuellement assignés à chaque épisode
- Le champ `path` de chaque `episodeFile` donne le chemin exact du fichier conservé

**Radarr :**
- `GET /api/v3/movie` → liste de tous les films (avec `movieFile` inclus si `hasFile: true`)
- Le champ `movieFile.path` donne le chemin exact du fichier conservé

→ Résultat : un **set de chemins protégés** (fichiers actuellement dans la bibliothèque)

#### Étape 3 — Analyse des hardlinks
Pour chaque fichier trouvé dans `/mnt/Downloads` :
1. Vérifier `st_nlink` : si > 1, le fichier a des hardlinks
2. Comparer `(st_dev, st_ino)` avec les fichiers protégés de la bibliothèque
3. Si un fichier du dossier Downloads partage le même inode qu'un fichier de la bibliothèque,
   il est **protégé** — sa suppression supprimerait un lien vers le média actif
4. Si `st_nlink == 1`, le fichier est indépendant — suppression sûre
5. Si `st_nlink > 1` mais aucun lien ne pointe vers la bibliothèque, vérifier
   si d'autres liens existent dans `/mnt/Downloads` (même release en plusieurs copies)

→ Calcul du **gain réel** :
- Si `st_nlink == 1` : gain = taille du fichier
- Si `st_nlink > 1` et on supprime un lien : gain = 0 (données toujours référencées)
- Si `st_nlink > 1` et on supprime le **dernier** lien : gain = taille du fichier

#### Étape 4 — Consultation de qBittorrent
- `GET /api/v2/torrents/info` → liste de tous les torrents
- Pour chaque torrent, `content_path` donne le chemin des fichiers
- Vérifier si le torrent est encore en seed (Hit & Run protection)
- Vérifier `completion_on` pour calculer l'âge du téléchargement
- Si `completion_on` < 7 jours → fichier protégé (Hit & Run)
- `seeding_time` peut compléter cette information

#### Classification finale
Chaque fichier est classé dans une des catégories :
| Statut | Signification | Action |
|--------|--------------|--------|
| `PROTECTED_LIBRARY` | Fichier utilisé par Sonarr/Radarr (lien actif) | Aucune suppression |
| `PROTECTED_HARDLINK` | Fichier lié par hardlink à un média en bibliothèque | Aucune suppression |
| `PROTECTED_SEEDING` | Torrent encore en seed (< 7 jours) | Attendre |
| `PROTECTED_DOWNLOADING` | Torrent encore en téléchargement | Attendre |
| `ORPHAN_SAFE` | Release orpheline, suppression sans risque, gain réel | Candidate |
| `ORPHAN_NO_GAIN` | Release orpheline mais hardlink actif — gain nul | Signaler |
| `UNKNOWN` | Fichier non identifiable par les API | Signaler |

### 3.4 Architecture de la base de données

```
┌──────────────────┐     ┌──────────────────────┐
│   scan_sessions  │     │   scan_files         │
├──────────────────┤     ├──────────────────────┤
│ id (PK)          │◄────│ scan_session_id (FK) │
│ started_at       │     │ id (PK)              │
│ completed_at     │     │ file_path            │
│ status           │     │ file_size            │
│ total_files      │     │ inode                │
│ orphan_count     │     │ device_id            │
│ protected_count  │     │ hardlink_count       │
│ total_size       │     │ status               │
│ reclaimable_size │     │ status_reason        │
└──────────────────┘     │ real_space_gain      │
                         │ media_type (tv/movie)│
                         │ media_title          │
                         │ quality_info         │
                         │ torrent_hash         │
                         │ torrent_name         │
                         │ completion_date      │
                         │ seeding_time         │
                         │ created_at           │
                         └──────────────────────┘

┌──────────────────────┐  ┌──────────────────────┐
│   protected_paths    │  │   deletion_log       │
├──────────────────────┤  ├──────────────────────┤
│ id (PK)              │  │ id (PK)              │
│ file_path            │  │ file_path            │
│ source (sonarr/      │  │ file_size            │
│         radarr/      │  │ real_space_freed     │
│         qbittorrent) │  │ status_at_deletion   │
│ media_title          │  │ reason               │
│ inode                │  │ deleted_at           │
│ device_id            │  │ deleted_by (user)    │
│ last_verified_at     │  │ scan_session_id (FK) │
└──────────────────────┘  └──────────────────────┘

┌──────────────────────┐
│   app_settings       │
├──────────────────────┤
│ key (PK)             │
│ value                │
│ updated_at           │
└──────────────────────┘
```

---

## 4. Conventions de développement

### Structure du projet
```
mediacleaner/
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── README.md
├── CLAUDE.md
│
├── backend/
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, CORS, static mount
│   │   ├── config.py            # Pydantic Settings (env vars)
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   │
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── scan.py
│   │   │   ├── file.py
│   │   │   ├── protected_path.py
│   │   │   ├── deletion_log.py
│   │   │   └── settings.py
│   │   │
│   │   ├── schemas/             # Pydantic schemas (API I/O)
│   │   │   ├── __init__.py
│   │   │   ├── scan.py
│   │   │   ├── file.py
│   │   │   └── stats.py
│   │   │
│   │   ├── api/                 # Routeurs FastAPI
│   │   │   ├── __init__.py
│   │   │   ├── scans.py
│   │   │   ├── files.py
│   │   │   ├── deletions.py
│   │   │   ├── stats.py
│   │   │   └── settings.py
│   │   │
│   │   ├── services/            # Logique métier
│   │   │   ├── __init__.py
│   │   │   ├── scanner.py       # Orchestrateur de scan
│   │   │   ├── filesystem.py    # Walk, stat, inode
│   │   │   ├── hardlink.py      # Analyse hardlinks
│   │   │   ├── sonarr.py        # Client API Sonarr
│   │   │   ├── radarr.py        # Client API Radarr
│   │   │   ├── qbittorrent.py   # Client API qBittorrent
│   │   │   ├── analyzer.py      # Classification des fichiers
│   │   │   └── deleter.py       # Exécution sécurisée suppression
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── logging.py
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_scanner.py
│       ├── test_hardlink.py
│       ├── test_analyzer.py
│       └── test_api.py
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/                 # Clients API TypeScript
│   │   ├── components/          # Composants UI
│   │   ├── pages/               # Pages principales
│   │   ├── hooks/               # Custom hooks
│   │   ├── types/               # Types TypeScript
│   │   └── styles/              # CSS / Tailwind
│   └── public/
│
└── docs/
    ├── ARCHITECTURE.md
    ├── API.md
    └── DEPLOYMENT.md
```

### Conventions de code
- **Python** : PEP 8, type hints systématiques, docstrings Google style
- **TypeScript** : ESLint + Prettier, interfaces explicites
- **Commits** : Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`)
- **API** : RESTful, versionné, réponses JSON standardisées
- **Logs** : structurés (JSON), niveaux INFO/WARNING/ERROR
- **Erreurs** : gestion explicite, pas de try/except silencieux

---

## 5. Plan d'évolution

### Phase 1 — MVP (développement initial)
- [x] Architecture définie
- [ ] Backend : clients API (Sonarr, Radarr, qBittorrent)
- [ ] Backend : scanner filesystem + analyse hardlinks
- [ ] Backend : moteur de classification
- [ ] Backend : API REST complète
- [ ] Frontend : dashboard avec scan, résultats, suppression
- [ ] Docker : Dockerfile + docker-compose.yml
- [ ] Documentation

### Phase 2 — Améliorations (post-validation)
- [ ] Scans programmés (cron-like via APScheduler)
- [ ] Notifications (webhooks, Discord, email)
- [ ] Statistiques et graphiques d'espace récupéré
- [ ] Support multi-dossiers de téléchargement
- [ ] Filtres avancés dans l'interface
- [ ] Export CSV des résultats

### Phase 3 — Fonctionnalités avancées
- [ ] Intégration directe Emby/Jellyfin/Plex pour vérification croisée
- [ ] Règles de rétention personnalisables
- [ ] Dry-run mode avec simulation
- [ ] API publique documentée (OpenAPI/Swagger)
- [ ] Support Prowlarr pour enrichir les métadonnées
- [ ] Multi-utilisateurs avec authentification
