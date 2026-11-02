# Gale Breaker - convenções do projeto

- Existe um único GDD: `docs/gdd/` (v0.10). Mudanças de design são feitas nele (fonte: `build_gdd.py`, que gera `index.html` e o PDF). Não criar novas versões nem PDFs numerados.
- Tudo do protótipo web fica em `web/`. A versão principal é `godot/`.
- Logs ficam em `logs/` (godot/, art-source/). Não criar `.log` em outras pastas.
- `godot/data/game_data.json` é gerado por `npm run sync-godot-data` (dentro de `web/`).
- Testes Godot: `./godot/tools/test.ps1 -GodotPath <Godot console exe>`. Testes web: `npm test` em `web/`.
- Não há repositório git; backups antigos estão em `art-source/revisions/`.
