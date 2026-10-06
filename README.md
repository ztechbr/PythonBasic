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
    legacy_basic.py      codec tokenizado/ASCII/protegido legado
    cassette.py          CAS1: WAV/MP3, FSK IBM PC e CRC
  asm_ports/             35 módulos, um por ASM original
  templates/             terminal web
  static/                CSS sem Node/React
reference/asm/            ASM original
reference/                headers e licença original
docs/ASM_ANALYSIS.md      análise dos 35 ASM
docs/ASM_ROUTINE_INDEX.json índice de PUBLIC/EXTRN/labels
docs/PORTING_GUIDE.md     método de tradução
docs/CASSETTE_AUDIO.md    compatibilidade CAS1: em WAV/MP3
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

### Cassete CAS1 em WAV

Por padrão, `CAS1:` usa `data/cassette.wav`:

```basic
10 PRINT "HELLO CASSETTE"
SAVE "CAS1:DEMO"
NEW
LOAD "CAS1:DEMO"
RUN
```

Para criar diretamente uma imagem MP3 no servidor:

```basic
MOUNT CAS1,"minhafita.mp3"
SAVE "CAS1:DEMO"
```

Para material histórico, prefira WAV. O diretório `examples/` contém `cassette_demo.wav`, já codificado no formato IBM PC CAS1, e `cassette_demo.bas`.

## Cobertura funcional atual

Implementados ou cobertos de forma útil: linhas numeradas, RUN, LIST, LLIST, NEW, CLEAR, DELETE, LET, atribuição implícita, PRINT, PRINT USING, WRITE, INPUT, LINE INPUT, IF/THEN/ELSE, GOTO, GOSUB, RETURN, ON GOTO/GOSUB, FOR/NEXT, WHILE/WEND, DATA/READ/RESTORE, DIM, arrays, ERASE, SWAP, TRON/TROFF, RANDOMIZE, POKE/PEEK, OUT/INP, OPEN/CLOSE, INPUT#/PRINT#/WRITE#, SAVE/LOAD/MERGE, BLOAD/BSAVE, DEF SEG, CAS1: em WAV/MP3, FILES, KILL, NAME, CLS, WIDTH, LOCATE, PSET, PRESET, LINE, CIRCLE, PAINT e callback CALL controlado.

Funções matemáticas e de string incluem ABS, ATN, COS, EXP, LOG, SIN, SQR, TAN, SGN, INT, FIX, CINT, CSNG, CDBL, RND, LEN, LEFT$, RIGHT$, MID$, CHR$, ASC, STR$, VAL, STRING$, SPACE$, HEX$, OCT$ e INSTR.

## Cassete IBM PC / CAS1:

A porta agora implementa o formato de fita do IBM PC usado pela família Cassette BASIC/BASICA: FSK baseado nos períodos do PIT, leader `FF`, sync `16h`, blocos de 256 bytes, CRC-16/CCITT, cabeçalhos BASIC, programas tokenizados/ASCII/protegidos e imagens `BSAVE`. A interface Flask permite montar um WAV ou MP3 antigo e usar `LOAD "CAS1:NOME"` ou `BLOAD "CAS1:NOME"`. Leia `docs/CASSETTE_AUDIO.md`.

WAV é o formato recomendado e sem perdas. MP3 é suportado com `ffmpeg`, mas não é indicado como cópia arquivística porque a compressão com perdas pode alterar transições de uma gravação antiga marginal.

## Compatibilidade deliberadamente não byte a byte

O projeto continua sendo uma porta semântica, não um emulador integral do 8086. O CAS1 e a memória segmentada necessária a `PEEK`/`POKE`/`BLOAD`/`BSAVE` são modelados explicitamente, mas não se tenta executar endereços 8086 arbitrários nem reproduzir todos os detalhes internos de descritores de string ou hardware não relacionado à fita.

## Estudo por arquivo ASM

Leia primeiro `docs/ASM_ANALYSIS.md`. Para navegação fina, `docs/ASM_ROUTINE_INDEX.json` contém todos os labels, `PUBLIC`, `EXTRN`, `INCLUDE` e números de linha encontrados automaticamente.

Para regenerar o índice:

```bash
python tools/analyze_asm.py reference/asm -o docs/ASM_ROUTINE_INDEX.json
```

## Licença

Os fontes originais fornecidos no pacote estão sob licença MIT da Microsoft. A cópia dessa licença está em `reference/LICENSE`.
