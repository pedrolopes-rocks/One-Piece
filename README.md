# Rota dos Mares — East Blue

Jogo de progressão por ilhas desenvolvido em Streamlit. A campanha inclui:

- montagem progressiva da tripulação, escolhendo uma função por equipe sorteada;
- sorteio por grupo, seguido da escolha de um personagem e de sua função;
- até seis personagens são exibidos por grupo, usando somente grupos com ao
  menos cinco personagens;
- até dois resorteios, reduzindo pela metade a chance de grupos já exibidos;
- ranks de SSS a F, mantendo os valores numéricos de atributos ocultos;
- mapa do East Blue com avanço do barco;
- confrontos animados contra até seis inimigos da mesma filiação;
- três velocidades de animação selecionáveis durante o confronto;
- efeitos de capitão, imediato, atacante, defensor, espião e tático;
- filiações sorteadas com dificuldade crescente ao longo da rota;
- filiações enfrentadas não se repetem na mesma campanha;
- equipes inimigas incompletas recebem 25% de força por vaga ausente;
- o poder ofensivo inimigo cresce 25% a cada ilha, com bônus adicionais para
  tiers A, S, SS e SSS e para Capitães;
- recrutamento escolhido pelo jogador, com substituição imediata de um
  sobrevivente compatível.

Os personagens e valores de balanceamento são carregados de
`assets/rei_dos_mares.xlsx`.

## Executar

```powershell
python -m streamlit run app.py --server.port 8502
```

No Windows, também é possível abrir `iniciar_jogo.bat`. O jogo usa a porta
`8502` para não conflitar com outras aplicações Streamlit na porta `8501`.

O estado da campanha fica na sessão atual do navegador.
