# Rota dos Mares — Demo East Blue

Protótipo em Streamlit de um jogo de progressão por ilhas inspirado em uma
aventura pirata. A demo inclui:

- sorteio de uma tripulação com seis funções e personagens únicos;
- rankings de S a D e atributos de ataque/defesa de 1 a 10;
- mapa do East Blue com avanço do barco;
- combate automático por rodadas;
- efeitos de líder, vice-líder, atacante, defensor, espião e tático;
- rolagem de recrutamento e banco de reservas.

## Executar

```powershell
python -m streamlit run app.py --server.port 8502
```

No Windows, também é possível abrir `iniciar_jogo.bat`. O jogo usa a porta
`8502` para não conflitar com outras aplicações Streamlit na porta `8501`.

O estado da campanha fica na sessão atual do navegador.
