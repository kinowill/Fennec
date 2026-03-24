# Contribuer a Fennec

Merci de ton interet pour Fennec ! Voici comment contribuer.

## Signaler un bug

Ouvre une [issue](https://github.com/kinowill/Fennec/issues) avec :
- Ta version de Fennec (`help` dans le shell)
- Ton OS (Windows 10/11)
- Les etapes pour reproduire le bug
- Le message d'erreur ou le comportement observe

## Proposer une fonctionnalite

Ouvre une issue avec le tag **enhancement** et decris :
- Le probleme que ca resout
- Comment ca devrait fonctionner
- Des exemples d'utilisation

## Pull requests

1. Fork le repo
2. Cree une branche : `git checkout -b ma-feature`
3. Code et teste
4. Commit avec un message clair : `feat: description` ou `fix: description`
5. Push et ouvre une PR

### Regles

- **Un seul fichier principal** : `fennec.py`. Pas de refactoring en modules sauf discussion prealable.
- **i18n obligatoire** : toute string utilisateur doit passer par `t()` avec cles fr + en.
- **Pas de dependances lourdes** : Fennec reste leger. Discuter avant d'ajouter un pip install.
- **Tester localement** : `python fennec.py` doit demarrer sans erreur.
- **Securite** : pas de `shell=True` sans justification, pas de chemins non valides.

### Style de commit

```
feat: nouvelle fonctionnalite
fix: correction de bug
docs: documentation
refactor: refactoring sans changement fonctionnel
chore: maintenance (gitignore, deps, etc.)
```

## Questions ?

Ouvre une issue ou utilise `helpchat` dans Fennec.
