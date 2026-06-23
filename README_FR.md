<p align="center">
  <picture>
    <img src="https://img.shields.io/badge/AgentBridge-v0.1.0a1-8B5CF6?style=for-the-badge" alt="AgentBridge">
  </picture>
</p>

<h1 align="center">AgentBridge</h1>

<p align="center">
  <strong>Fini le copier-coller entre outils d'IA.</strong><br>
  Créez des travailleurs IA persistants entre Claude, GPT, Gemini, DeepSeek et les modèles locaux —<br>
  avec mémoire partagée, orchestration de workflows et intégration MCP.
</p>

<p align="center">
  <a href="#-démarrage-rapide"><img src="https://img.shields.io/badge/-Démarrage_rapide-10B981?style=flat-square" alt="Démarrage rapide"></a>
  <a href="#-fonctionnalités"><img src="https://img.shields.io/badge/-Fonctionnalités-3B82F6?style=flat-square" alt="Fonctionnalités"></a>
  <a href="#%EF%B8%8F-configuration"><img src="https://img.shields.io/badge/-Configuration-8B5CF6?style=flat-square" alt="Configuration"></a>
  <a href="#-exemples"><img src="https://img.shields.io/badge/-Exemples-F59E0B?style=flat-square" alt="Exemples"></a>
  <a href="#%EF%B8%8F-architecture"><img src="https://img.shields.io/badge/-Architecture-EC4899?style=flat-square" alt="Architecture"></a>
  <a href="#%EF%B8%8F-remerciements"><img src="https://img.shields.io/badge/-Remerciements-6366F1?style=flat-square" alt="Remerciements"></a>
  <a href="README_ZH.md"><img src="https://img.shields.io/badge/中文-文档-EA4335?style=flat-square" alt="中文"></a>
  <a href="README_DE.md"><img src="https://img.shields.io/badge/Deutsch-Dokument-FFD700?style=flat-square" alt="Deutsch"></a>
  <a href="README_ES.md"><img src="https://img.shields.io/badge/Español-Doc-00C853?style=flat-square" alt="Español"></a>
  <a href="README_FR.md"><img src="https://img.shields.io/badge/Français-Doc-1E90FF?style=flat-square" alt="Français"></a>
  <a href="README_JP.md"><img src="https://img.shields.io/badge/日本語-ドキュメント-FF4081?style=flat-square" alt="日本語"></a>
  <a href="README_KR.md"><img src="https://img.shields.io/badge/한국어-문서-03C75A?style=flat-square" alt="한국어"></a>
</p>

---

## 📋 Table des matières

| Section | Description |
|---------|-------------|
| [🎯 Aperçu](#-aperçu) | Ce qu'est AgentBridge et pourquoi il existe |
| [✨ Fonctionnalités](#-fonctionnalités) | Capacités actuelles |
| [⚡ Démarrage rapide](#-démarrage-rapide) | Installation et premier workflow |
| [📖 Guide d'utilisation](#-guide-dutilisation) | Workflows, terminaux, mémoire |
| [⚙️ Configuration](#%EF%B8%8F-configuration) | Fournisseurs, terminaux, routage |
| [🏗️ Architecture](#%EF%B8%8F-architecture) | Conception du système |
| [📁 Exemples](#-exemples) | Workflows prêts à l'emploi |
| [🛣️ Feuille de route](#%EF%B8%8F-feuille-de-route) | Plans futurs |
| [🙏 Remerciements](#%EF%B8%8F-remerciements) | Remerciements |
| [📄 Licence](#-licence) | MIT |

---

## 🎯 Aperçu

**AgentBridge** est une couche de coordination open-source pour les agents IA — comme Docker pour les conteneurs, mais pour les outils d'IA.

### Le problème

Vous utilisez **Claude Code** pour l'architecture, **ChatGPT** pour le raisonnement, **Gemini** pour la recherche, **DeepSeek** pour le code. Chaque outil est excellent. **Ils ne communiquent pas entre eux.** Vous perdez 30 % de votre temps à copier du contexte entre les outils et à brûler des tokens premium sur des tâches qu'un modèle gratuit pourrait effectuer.

### La solution

```
┌─────────────────────────────────────────────────────┐
│                 Vos outils IA                         │
│   Claude Code    ChatGPT    Gemini    DeepSeek       │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                   AgentBridge                        │
│                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  Pool de    │  │  Moteur de  │  │   Mémoire   │  │
│  │  Terminaux  │  │  Workflow   │  │  Partagée   │  │
│  │ (Multi-CLI) │  │  (YAML)     │  │  (SQLite)   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│  ┌─────────────┐  ┌─────────────┐                    │
│  │  Adaptateurs │  │ Client MCP │                    │
│  │ (5 fournis.) │  │  (Outils)  │                    │
│  └─────────────┘  └─────────────┘                    │
└──────────────────────────────────────────────────────┘
```

---

## ✨ Fonctionnalités

### 🤖 Pool de terminaux multiples
- Exécutez **plusieurs instances** du même outil CLI (ex. 3 terminaux Claude Code simultanément)
- Chaque terminal a une **sélection de modèle indépendante**
- **Persistant** entre les sessions (basé sur SQLite)

**Terminaux pris en charge :** `claude`, `mimo`, `opencode`, `codex`, `qcode`, `custom`

### 🔄 Moteur de workflow
- Pipelines **séquentielles** avec résolution de variables template entre les étapes
- Exécution **parallèle** sur plusieurs terminaux simultanément
- Workflows définis en YAML — aucune programmation requise

### 🧠 Mémoire partagée
- **Contexte inter-agent** : chaque agent voit la sortie des agents précédents
- **Persistance SQLite** : la mémoire survit aux sessions
- **Clés nommées** : `save_as` pour référence sémantique

### 🔗 Intégration MCP
- Connectez-vous à **n'importe quel serveur MCP** pour obtenir des outils
- Client MCP basé sur stdio avec gestion des délais d'attente et des erreurs

### 💰 Routage tenant compte des coûts (prévu)
- Modèles gratuits d'abord, payants seulement si nécessaire
- Routage par politique (qualité vs vitesse vs coût)

---

## ⚡ Démarrage rapide

### Installation

```bash
pip install agentbridge
```

### Initialisation

```bash
agentbridge init
```

Configurez vos clés API via les variables d'environnement :

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="..."
export DEEPSEEK_API_KEY="sk-..."
```

### Exécutez votre premier workflow

Créez un fichier `hello.yaml` :

```yaml
name: "Hello Multi-Agent"

steps:
  - agent: gemini
    prompt: "List 3 interesting facts about the MCP protocol."
    save_as: research

  - agent: claude
    prompt: "Based on: {{research}}\nDesign a simple architecture."
    save_as: architecture
```

Exécutez-le :

```bash
agentbridge run hello.yaml
```

### Gérer les terminaux

```bash
# Voir les types de terminaux disponibles
agentbridge terminal types

# Créer un terminal Claude Code pour l'architecture
agentbridge terminal create claude -n architect -m claude-sonnet-4-20250514

# Et un autre pour les tâches rapides
agentbridge terminal create claude -n assistant -m claude-haiku-4-20251001

# Créer un terminal Gemini pour la recherche
agentbridge terminal create google -n researcher -m gemini-2.5-flash

# Voir tous les terminaux en cours d'exécution
agentbridge terminal list

# Exécuter un prompt sur un terminal spécifique
agentbridge terminal exec opencode "Analyze this data"
```

---

## 📖 Guide d'utilisation

### Workflows

Les workflows sont des fichiers YAML définissant des pipelines multi-agents :

```yaml
name: "Pipeline Name"
description: "What this pipeline does"

vars:
  topic: "AI safety"

steps:
  - agent: gemini
    prompt: "Research {{topic}}"
    save_as: research
    system: "You are a research analyst."

  - agent: claude
    prompt: "Design based on: {{research}}"
    save_as: design
```

| Champ | Description |
|-------|-------------|
| `agent` | Type de terminal à utiliser (claude, gemini, gpt, opencode, deepseek) |
| `prompt` | Le prompt à envoyer |
| `save_as` | Clé pour stocker le résultat dans la mémoire partagée |
| `system` | Prompt système (optionnel) |
| `model` | Surcharge de modèle (optionnel) |
| `parallel` | Mettre à `true` pour exécuter l'étape dans un groupe parallèle |

### Terminaux

AgentBridge traite chaque CLI d'IA comme un "terminal" — un travailleur indépendant :

| Terminal | Binaire | Modèle par défaut | Statut |
|----------|--------|---------------|--------|
| `claude` | `claude` | claude-sonnet-4-20250514 | ✅ Disponible |
| `mimo` | `mimo` | gpt-4o | ✅ Disponible |
| `opencode` | `opencode` | deepseek-chat | ✅ Disponible |
| `codex` | `codex` | gpt-4o | ❌ Non installé |
| `qcode` | `q` | qwen2.5:7b | ❌ Non installé |
| `custom` | (configurable) | défini par l'utilisateur | ⚡ Personnalisé |

### Mémoire partagée

```bash
# Stocker
agentbridge remember my_key "some value"

# Récupérer
agentbridge recall my_key

# Lister toutes les clés
agentbridge memory-list
```

---

## ⚙️ Configuration

Emplacement du fichier de configuration : `~/.agentbridge/config.yaml` (ou `$AGENTBRIDGE_CONFIG_DIR/config.yaml`)

```yaml
providers:
  openai:
    model: gpt-4o
  anthropic:
    model: claude-sonnet-4-20250514
  google:
    model: gemini-2.5-flash
  deepseek:
    model: deepseek-chat
  ollama:
    model: qwen2.5:7b
    base_url: http://localhost:11434

terminals:
  - name: claude-main
    type: claude
    model: claude-sonnet-4-20250514
  - name: claude-fast
    type: claude
    model: claude-haiku-4-20251001
  - name: mimo-coder
    type: mimo
    model: gpt-4o

routing:
  default: balanced
  policies:
    coding: free_first
    research: quality_first
    quick: cheapest
```

**Priorité des clés API :**
1. Champ `api_key` dans le fichier de configuration
2. Variable d'environnement (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.)
3. Vide (l'adaptateur émettra un avertissement)

---

## 🏗️ Architecture

```
                    ┌─────────────────────┐
                    │   CLI (Click)       │
                    │  agentbridge run     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   AgentBridge Core    │
                    │                      │
                    │  ┌────────────────┐  │
                    │  │  Pool de       │──│──→ Claude Code, Mimo, OpenCode...
                    │  │  Terminaux     │  │
                    │  │  (Multi-Inst.) │  │
                    │  ├────────────────┤  │
                    │  │ Moteur de      │  │
                    │  │ Workflow       │  │
                    │  │ (Parseur YAML) │  │
                    │  ├────────────────┤  │
                    │  │  Planificateur  │──│──→ Séquentiel / Parallèle
                    │  ├────────────────┤  │
                    │  │ Mémoire        │  │
                    │  │ Partagée(SQLite)│  │
                    │  ├────────────────┤  │
                    │  │  Adaptateurs    │──│──→ OpenAI / Claude / Gemini...
                    │  ├────────────────┤  │
                    │  │ Client MCP     │──│──→ GitHub MCP / Filesystem MCP...
                    │  └────────────────┘  │
                    └──────────────────────┘
```

### Décisions de conception

| Décision | Choix | Justification |
|----------|--------|-----------|
| CLI d'abord | Click + YAML | Workflows sans code ; les non-développeurs peuvent créer des pipelines |
| Multi-instance | Pool de threads | Exécuter des agents simultanément sur différents modèles |
| Persistance | SQLite | Mémoire inter-sessions sans dépendance externe |
| Adaptateurs | Basé sur httpx | Dépendances minimales ; pas de SDK fournisseur |
| MCP | Client uniquement (v0.1) | Consommer des serveurs MCP ; mode Hub en v1.0 |

---

## 📁 Exemples

| Exemple | Description |
|---------|-------------|
| `examples/saas-builder.yaml` | Pipeline SaaS 4 agents : Gemini recherche → Claude conception → GPT code → DeepSeek révision |
| `examples/linguagraph-research.yaml` | Pipeline de recherche 3 agents : analyse linguistique → modèle cognitif → rédaction d'article |
| `examples/debate.yaml` | Débat 3 agents : LLM pro-local vs pro-cloud, jugé par Gemini |
| `examples/parallel-research.yaml` | Sprint de recherche parallèle 4 agents avec synthèse |

---

## 🛣️ Feuille de route

- **v0.1** — ✅ CLI, workflows YAML, 5 adaptateurs, mémoire partagée, client MCP, pool de terminaux
- **v0.2** — 🔄 Tableau de bord Web (Next.js), visualisation des workflows, routage économique, Docker
- **v0.5** — 🔄 Orchestration LangGraph, branchements conditionnels, intervention humaine
- **v1.0** — 🔄 Hub MCP bidirectionnel, système de plugins, mémoire vectorielle

---

## 🙏 Remerciements

AgentBridge est construit sur les épaules de géants. Nous exprimons notre plus profonde gratitude à :

### 🖥️ Plateformes terminales

| Plateforme | Remerciement |
|----------|--------|
| **[Claude Code](https://claude.ai)** — Propulsé par Anthropic | La plateforme de développement principale. AgentBridge a été conçu et construit en utilisant les capacités d'orchestration d'agents de Claude Code. [Conditions](https://www.anthropic.com/legal) · [Confidentialité](https://www.anthropic.com/privacy) |
| **[OpenCode](https://opencode.ai)** | Cible d'adaptateur terminal et partenaire de test. L'interface CLI d'OpenCode est utilisée par le pool de terminaux d'AgentBridge. |
| **[MimoCode](https://mimo.ai)** | Cible d'adaptateur terminal. L'intégration CLI de Mimo permet des workflows frontend multi-modèles. |
| **OpenAI Codex** | Cible d'adaptateur terminal pour les tâches de codage. |

### 🤖 Modèles d'IA utilisés dans le développement

- **Claude Opus 4.8 / Sonnet 4.6** (Anthropic) — Modèles de développement principaux
- **Gemini 2.5 Flash** (Google) — Tâches de recherche, analyse concurrentielle
- **GPT-4o** (OpenAI) — Évaluation et révision d'architecture
- **DeepSeek V3** (DeepSeek) — Révision de code et tests

### 📦 Dépendances open-source

| Dépendance | Licence | Objectif |
|------------|---------|---------|
| [Click](https://palletsprojects.com/p/click/) | BSD-3-Clause | Framework CLI |
| [PyYAML](https://pyyaml.org/) | MIT | Analyse YAML |
| [HTTPX](https://www.python-httpx.org/) | BSD-3-Clause | Client HTTP pour les API de modèles |
| [pydantic](https://docs.pydantic.dev/) (prévu) | MIT | Validation de configuration (v0.2) |

### 🧠 Compétences et sources de connaissances

- **ECC (Engineering Claude Code)** Système de plugins — modèles d'orchestration d'agents
- **Claude Scholar** — Modèles de workflow de recherche académique
- **MCP (Model Context Protocol)** — Protocole d'Anthropic pour l'intégration d'outils

### 🌍 Traductions de la communauté

Le README d'AgentBridge est disponible en :
- [中文 (Chinese)](README_ZH.md)
- [Deutsch (German)](README_DE.md)
- [Français (French)](README_FR.md)
- [Español (Spanish)](README_ES.md)
- [日本語 (Japanese)](README_JP.md)
- [한국어 (Korean)](README_KR.md)

---

## 📄 Licence

[MIT](LICENSE) © 2026 [jjjjjjjjnnjnn](https://github.com/jjjjjjjjnnjnn)

---

<p align="center">
  <strong>AgentBridge</strong> — La couche de coordination pour les agents IA.<br>
  <sub>Construit avec ❤️ pour la communauté IA open-source</sub>
</p>
