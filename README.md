# Rota dos Mares — East Blue

Jogo de progressão por ilhas desenvolvido em Streamlit. A campanha inclui:

- montagem progressiva da tripulação, escolhendo uma função por equipe sorteada;
- até três resorteios da equipe candidata durante a composição;
- rankings de S a D e atributos de ataque/defesa de 1 a 10;
- mapa do East Blue com avanço do barco;
- resolução automática dos confrontos;
- efeitos de líder, vice-líder, atacante, defensor, espião e tático;
- recrutamento após vitórias e banco de reservas.

## Executar

```powershell
python -m streamlit run app.py --server.port 8502
```

No Windows, também é possível abrir `iniciar_jogo.bat`. O jogo usa a porta
`8502` para não conflitar com outras aplicações Streamlit na porta `8501`.

O estado da campanha fica na sessão atual do navegador.
