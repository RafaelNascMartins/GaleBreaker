GALE BREAKER GDD VISUAL v0.10

Documento principal: Gale_Breaker_GDD_Visual_v0_10.pdf
Versão navegável e editável: index.html

REGRA: existe um único GDD (v0.10). Mudanças são feitas nele, editando build_gdd.py e regenerando HTML e PDF; não crie novas versões. GDD_rascunho_v0.1.md é o texto histórico original, mantido só por conter decisões que o visual não repete.

Edição 0.9: página 10 refeita com infográfico de escolha, habilidades, limite de pontos e modos; página 12 com novas concepts de pausa e HUD usando os designs atuais de Kaze e Ignis. As imagens são referências de interface, ainda sem integração ao jogo. Prompts registrados em concept-art/prompts-gdd-paginas-10-12-v1.json.

Edição 0.8: diagramação em papel marfim com texto escuro, títulos editoriais, detalhes nas cores dos quatro elementos e fontes próprias para os personagens. Retratos padronizados em molduras de mesma dimensão no elenco e nas quatro fichas. Comandos vetoriais: traço = básico; traço duplo = forte; estrela = elemental; losango duplo = ultimate. São categorias de ação, não teclas ou botões definitivos. As fontes locais estão na pasta assets e acompanham o HTML.

Abra o HTML no navegador e use Editar textos. Salvar edição HTML baixa uma cópia com os textos alterados; mantenha essa cópia ao lado da pasta assets. Imprimir PDF permite exportar a edição pelo navegador, com gráficos de fundo habilitados e sem cabeçalhos/rodapés do navegador.

O PDF tem 34 páginas em formato paisagem. Inclui personagens atuais, arenas, UI, os 16 ícones, fluxo, habilidades, modos, decisões em aberto e 16 fichas ilustradas de ataques nas páginas 14-29. Os básicos mostram três ataques J1/J2/J3; os outros mostram três fases de um golpe. Kaze e Ignis preservam as sequências orientadas pelo autor e seus desenhos originais. As outras 14 pranchas foram desenvolvidas com ImageGen nativo a partir dessa linguagem. Efeitos, respostas e custos são propostas; dano, alcance, hitboxes e tempos finais dependem de teste. O redesign ainda não foi implementado no jogo.

Os assets de referência continuam preservados em concept-art. As imagens em assets são cópias para manter o documento independente do layout de pastas do jogo.

build_gdd.py é a fonte de geração do PDF e da versão HTML. Alterar o HTML não altera automaticamente essa fonte nem o PDF já gerado. A pasta qa contém apenas material de verificação interna.
