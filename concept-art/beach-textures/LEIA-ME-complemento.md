# Complemento da praia v1

## Mar conectado

`mar-transicao-v1.png` contém duas regiões quadradas, lidas da esquerda para a direita: orla/mar raso e mar profundo. O arquivo é uma única pintura contínua; não há montagem entre imagens independentes na borda central.

No Godot, os recursos `mar_raso-v1.tres` e `mar_profundo-v1.tres` são AtlasTextures separados usando essa mesma imagem. Para uma malha 3D contínua, a forma mais direta é usar o PNG inteiro como albedo e mapear U=0 na areia, U=0,5 na transição e U=1 no mar mais profundo. Para peças adjacentes, use as regiões do JSON no mesmo sentido, sem espelhar ou girar. AtlasTexture não substitui a configuração de UV do modelo.

A conexão foi feita somente entre a direita do raso e a esquerda do profundo. Repetição em outras bordas, mipmaps e a animação da água precisam de ajuste no modelo. Esta é uma textura de cor; o brilho, a transparência e as ondas do material não foram implementados aqui.

## Céu e telhado

`ceu-praia-v1.png`: panorama pintado 2:1, sem terreno. Base visual para fundo ou céu; a projeção e a emenda de uma volta completa ainda precisam ser verificadas na câmera final.

`telhas-azul-marinho-v1.png`: albedo de telhas cerâmicas em azul-marinho. Ajustar escala UV e repetição no telhado; sem mapas normal/roughness adicionais.

O ZIP mantém a estrutura `assets/environments/beach/textures/`: extraia na raiz de um projeto Godot para importar os PNGs e os dois AtlasTextures. Nenhuma cena ou menu foi alterado.
