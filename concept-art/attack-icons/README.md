# Gale Breaker — 16 ícones de ataque

Gerados com a ferramenta nativa ImageGen. Cada arquivo é um PNG RGBA de 1254 × 1254 px, com transparência real, sem texto e sem moldura. Não foram redimensionados nem aplicados automaticamente ao jogo.

Abra `index.html` para comparar todos os ícones e alternar fundo claro/escuro. A galeria também exibe miniaturas de 64 e 32 px. Os arquivos originais estão disponíveis ao clicar em cada imagem.

| Lutador | Básico (`light`) | Forte (`heavy`) | Elemental (`elemental`) | Ultimate (`ultimate`) |
|---|---|---|---|---|
| Kaze | Palma de Jade | Chute do Vendaval | Rajada de Vento | Tufão Celestial |
| Ignis | Soco de Roça | Marreta Caipira | Pisada da Fornalha | Fúria do Meio-Dia |
| Tophia | Punho de Arenito | Martelo de Pedra | Erupção Rochosa | Colosso de Terra |
| Volt | Tiro de Sucata | Disparo Carregado | Curto-Circuito | Sobrecarga Total |

Os nomes são propostas artísticas para identificar os arquivos. Os nomes, regras, alcance e dano dos golpes no código não foram alterados. Os quatro tipos correspondem às ações principais J/K/L/U do HUD existente; lançador baixo e soco aéreo são variantes contextuais do básico e não fazem parte deste conjunto de 16.

Direção: Kaze jade/vento e pés descalços; Ignis mãos vermelhas de sol, bota e chapéu de cowboy; Tophia pedra laranja; Volt sucata e canhão de mão com energia ciano. Cada ícone foi gerado separadamente com um prompt de estilo comum.

`manifest.json` relaciona IDs, personagens, ações, nomes e arquivos. `prompts.json` contém todos os prompts finais. Os PNGs podem ser importados como texturas de interface no Godot. Ajustar margens e tamanho de exibição na interface, mantendo a transparência.
