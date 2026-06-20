# Orientações para agentes

## Visão geral

Este repositório contém o protótipo **Rota dos Mares**, um jogo de progressão
por ilhas inspirado em One Piece. A interface é construída com Streamlit e o
estado da campanha permanece na sessão do navegador.

O projeto usa Python 3.10 ou superior e não possui etapa de compilação.

## Estrutura principal

- `app.py`: interface Streamlit, estado da sessão, mapa, composição da equipe,
  batalhas e eventos cinematográficos.
- `game_engine.py`: regras de sorteio, combate, recrutamento e cálculos do jogo.
- `game_data.py`: personagens, funções, localidades, estágios e constantes.
- `tests/test_engine.py`: testes unitários do motor.
- `assets/`: mídias utilizadas pela interface.
- `gerar_status_personagens_pdf.py`: geração do relatório de personagens.
- `iniciar_jogo.bat`: inicialização do jogo no Windows.

## Instalação e execução

Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

Execute o jogo:

```powershell
python -m streamlit run app.py --server.port 8502
```

No Windows, `iniciar_jogo.bat` executa o mesmo comando.

## Validação

Execute os testes antes de concluir alterações:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest discover -s tests -v
```

Valide também a sintaxe:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m py_compile app.py game_engine.py game_data.py tests\test_engine.py
```

O ambiente pode não ter `pytest` instalado. A suíte oficial usa
`unittest`, portanto não adicione `pytest` como dependência sem necessidade.

## Convenções de implementação

- Mantenha regras e cálculos em `game_engine.py`; evite colocá-los diretamente
  na interface.
- Mantenha dados declarativos de personagens e fases em `game_data.py`.
- Use `random.Random` opcional nas funções aleatórias para permitir testes
  determinísticos.
- Personagens não podem ocupar duas funções na mesma equipe.
- Chefes listados em `MAIN_VILLAINS` não podem integrar a equipe do jogador nem
  ser recrutados.
- A campanha só pode começar quando todas as funções de `ROLES` estiverem
  preenchidas.
- Preserve compatibilidade com estados antigos da sessão quando adicionar ou
  renomear chaves de `st.session_state`.
- Ao alterar regras do motor, adicione ou atualize testes em
  `tests/test_engine.py`.

## Interface e mídias

- Textos exibidos ao jogador devem estar em português do Brasil.
- Preserve o tema visual marítimo e a legibilidade em telas menores.
- Mídias consumidas pelo jogo devem permanecer em `assets/`.
- Evite arquivos temporários, frames intermediários e caches Python no commit.
- Vídeos de eventos devem usar formatos compatíveis com navegador, de
  preferência H.264 com áudio AAC em contêiner MP4.
- Considere que navegadores podem bloquear áudio automático; eventos com som
  devem possuir uma forma de liberar a reprodução por interação.

## Cuidados com o repositório

- O diretório de trabalho pode conter alterações do usuário. Não reverta nem
  sobrescreva mudanças que não façam parte da tarefa.
- Não versione `__pycache__`, arquivos temporários ou resultados de diagnóstico.
- Antes de finalizar, execute `git diff --check` e confira `git status --short`.
