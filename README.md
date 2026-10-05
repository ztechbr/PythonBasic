# GW-BASIC ASM to Python 3 - Flask MVC Academic Port

Portabilidade acadêmica dos 35 arquivos ASM fornecidos do GW-BASIC para uma aplicação Python 3 com Flask e arquitetura MVC.

## Objetivo

O projeto mantém os fontes ASM em `reference/asm` e cria um módulo Python correspondente para cada arquivo em `app/asm_ports`. As partes centrais são implementadas de forma executável. As partes estritamente ligadas ao 8086, DOS ou hardware são convertidas em abstrações equivalentes e documentadas.

## Arquitetura

```text
app/
  controllers/           HTTP e sessão do terminal
  models/                RuntimeState, pilhas, tela, arquivos
  services/
    interpreter.py       dispatcher e execução dos statements
    expression.py        lexer e parser de expressões
  asm_ports/             35 módulos, um por ASM original
  templates/             terminal web
  static/                CSS sem Node/React
reference/asm/            ASM original
reference/                headers e licença original
docs/ASM_ANALYSIS.md      análise dos 35 ASM
docs/ASM_ROUTINE_INDEX.json índice de PUBLIC/EXTRN/labels
docs/PORTING_GUIDE.md     método de tradução
examples/                 programas BASIC de teste
```

## Execução com Docker

```bash
cp .env.example .env
docker compose up --build
```

Acesse `http://localhost:8000`.

No Easypanel, publique a porta `8000`, configure `SECRET_KEY` e monte um volume persistente em `/app/data`. O Dockerfile usa um worker Gunicorn com múltiplas threads porque o estado das sessões BASIC está em memória. Para escalar horizontalmente, mova o SessionManager para Redis ou outro armazenamento compartilhado.

## Execução local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

No Windows PowerShell, use `.venv\\Scripts\\Activate.ps1`.

## Exemplos no terminal

```basic
10 FOR I=1 TO 5
20 PRINT I;
30 NEXT I
RUN
```

```basic
10 DATA 3,"ABC",5
20 READ A,B$,C
30 PRINT A;B$;C
RUN
```

```basic
10 INPUT "NOME";N$
20 PRINT "OLA ";N$
RUN
```

## Cobertura funcional atual

Implementados ou cobertos de forma útil: linhas numeradas, RUN, LIST, LLIST, NEW, CLEAR, DELETE, LET, atribuição implícita, PRINT, PRINT USING, WRITE, INPUT, LINE INPUT, IF/THEN/ELSE, GOTO, GOSUB, RETURN, ON GOTO/GOSUB, FOR/NEXT, WHILE/WEND, DATA/READ/RESTORE, DIM, arrays, ERASE, SWAP, TRON/TROFF, RANDOMIZE, POKE/PEEK, OUT/INP, OPEN/CLOSE, INPUT#/PRINT#/WRITE#, SAVE/LOAD/MERGE, FILES, KILL, NAME, CLS, WIDTH, LOCATE, PSET, PRESET, LINE, CIRCLE, PAINT e callback CALL controlado.

Funções matemáticas e de string incluem ABS, ATN, COS, EXP, LOG, SIN, SQR, TAN, SGN, INT, FIX, CINT, CSNG, CDBL, RND, LEN, LEFT$, RIGHT$, MID$, CHR$, ASC, STR$, VAL, STRING$, SPACE$, HEX$, OCT$ e INSTR.

## Compatibilidade deliberadamente não byte a byte

O projeto não tenta reproduzir Microsoft Binary Format, layout exato de descritores de string, BIOS, memória segmentada, UART, cassete, BLOAD/BSAVE de RAM bruta ou execução de endereços 8086. Esses itens exigiriam um emulador de máquina e reduziriam o valor didático da porta Python.

## Estudo por arquivo ASM

Leia primeiro `docs/ASM_ANALYSIS.md`. Para navegação fina, `docs/ASM_ROUTINE_INDEX.json` contém todos os labels, `PUBLIC`, `EXTRN`, `INCLUDE` e números de linha encontrados automaticamente.

Para regenerar o índice:

```bash
python tools/analyze_asm.py reference/asm -o docs/ASM_ROUTINE_INDEX.json
```

## Licença

Os fontes originais fornecidos no pacote estão sob licença MIT da Microsoft. A cópia dessa licença está em `reference/LICENSE`.
