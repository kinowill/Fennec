# Politique de securite

## Signaler une vulnerabilite

Si tu decouvres une faille de securite dans Fennec, **ne cree pas d'issue publique**.

Contacte le mainteneur directement via GitHub ([@kinowill](https://github.com/kinowill)) en message prive ou par email si disponible.

## Delai de reponse

- Accusee de reception sous 48h
- Evaluation et plan de correction sous 7 jours
- Patch publie des que possible

## Perimetre

### Couvert
- Injection de commandes via l'agent ou `exec`
- Path traversal (acces a des fichiers hors perimetre)
- Bypass de la whitelist agent
- Fuite de donnees personnelles

### Hors perimetre
- Vulnerabilites dans Ollama, Python ou les dependances tierces
- Acces physique a la machine (Fennec est un outil local)
- Attaques reseau (Fennec n'expose pas de port)

## Architecture de securite

- **100% local** : aucune donnee envoyee sauf recherches DuckDuckGo (initiees par l'utilisateur)
- **Whitelist agent** : l'agent IA ne peut utiliser que les commandes Fennec approuvees
- **Protection path traversal** : les chemins `..` sont bloques dans le contexte agent
- **Corbeille reversible** : `delete` ne supprime jamais definitivement (sauf `emptytrash`)
- **Confirmations** : toutes les actions destructives demandent confirmation (sauf en mode `sudo`)
- **Config isolee** : `fennec_config.json` ne contient aucun secret, uniquement des preferences
