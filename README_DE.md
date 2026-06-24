<p align="center">
  <picture>
    <img src="https://img.shields.io/badge/RelayOS-v0.2.0a12-8B5CF6?style=for-the-badge" alt="RelayOS">
  </picture>
</p>

<h1 align="center">RelayOS</h1>

<p align="center">
  <strong>Git für KI-Konversationen.</strong><br>
  <br>
  Forke, merge und verwebe KI-Gespräche.<br>
  Ein Arbeitsbereich für Claude, GPT, Gemini, DeepSeek und lokale Modelle.
</p>

<p align="center">
  <a href="#-schnellstart"><img src="https://img.shields.io/badge/Schnellstart-10B981?style=for-the-badge" alt="Schnellstart"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/English-FFFFFF?style=flat-square" alt="English"></a>
  <a href="README_ZH.md"><img src="https://img.shields.io/badge/中文-EA4335?style=flat-square" alt="中文"></a>
</p>

---

## Das Problem

Du wechselst ständig zwischen ChatGPT, Claude, Gemini und DeepSeek. Kopierst Ausgaben von einem, fügst sie in den nächsten ein. Kontext geht zwischen Sessions verloren. **30% deiner Zeit verschwendest du mit Tool-Management statt mit Bauen.**

## Die Lösung

**RelayOS behandelt KI-Gespräche wie Code.** Forke, merge und verwebe sie.

```
pip install relayos && relay
```

### Kernfunktionen

| Funktion | Beschreibung |
|----------|-------------|
| 🔀 Konversationsgraph | `/fork` `/merge` `/attach` — Git für Gespräche |
| 🧠 Auto-Routing | Freie Modelle zuerst, Premium nur bei Bedarf |
| 💰 Budget-Wächter | Harte Limits pro Aufgabe/Tag/Monat |
| 🔌 Unified Provider | API + CLI Nullkonfiguration, Auto-Erkennung |
| ⌨️ OpenCode-TUI | Ctrl+P Palette, Tab-Wechsel, Chat-Oberfläche |
| 💾 Sitzungsübergreifendes Wissen | `/remember` Fakten speichern |

### Schnellstart

```bash
pip install relayos
relay
```

### Befehle

```
/fork              Session abzweigen
/merge id1 id2     Sessions zusammenführen
/attach id         Kontext importieren
/remember k: val   Wissen speichern
Ctrl+P             Befehlspalette
Ctrl+X N           Neue Session
Ctrl+X S           Session-Liste
Ctrl+X G           Konversationsgraph
```

### Installation

```bash
pip install relayos
```

[Apache 2.0 Lizenz](LICENSE)
