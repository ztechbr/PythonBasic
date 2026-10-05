# Análise dos 35 ASM e estratégia de portabilidade

Este documento foi gerado a partir dos fontes originais incluídos em `reference/asm`. O objetivo não é emular cada instrução 8086, mas preservar a responsabilidade de cada módulo e explicar como registradores, flags, pilha, ponteiros e dispositivos físicos foram convertidos em estruturas Python legíveis.

## Regra geral de tradução

| Conceito no ASM 8086 | Equivalente Python |
|---|---|
| AX, BX, CX, DX, SI, DI | variáveis locais e argumentos nomeados |
| CS, DS, ES e offsets | referências de objeto e índices |
| PUSH/POP e frames manuais | listas/dataclasses de frames |
| FLAGS, ZF, CF, SF | booleanos, comparações e exceções |
| CALL/JMP para labels | chamadas de função e retorno `Control` |
| FAC/ARG | valores Python retornados pelo parser |
| VARTAB/ARYTAB | `dict` de variáveis e arrays |
| dispositivo CRT/BIOS | `ScreenBuffer` e SVG |
| DOS file handles | objetos de arquivo Python em sandbox |
| token binário | lexer/parser textual |

## Matriz dos módulos

| ASM | Papel | Linhas | Labels | PUBLIC | Estado da porta |
|---|---|---:|---:|---:|---|
| `ADVGRP.ASM` | Gráficos avançados | 1359 | 133 | 4 | Semântico funcional |
| `BIBOOT.ASM` | Bootstrap DOS/8086 | 74 | 1 | 1 | Adaptado |
| `BIMISC.ASM` | Controle geral do interpretador | 944 | 89 | 49 | Funcional parcial |
| `BIPRTU.ASM` | PRINT USING | 469 | 51 | 1 | Funcional parcial |
| `BIPTRG.ASM` | Variáveis e arrays | 693 | 66 | 12 | Funcional |
| `BISTRS.ASM` | Strings | 1110 | 107 | 44 | Funcional parcial |
| `CALL86.ASM` | CALL nativo | 94 | 9 | 2 | Adaptado por segurança |
| `DSKCOM.ASM` | Rotinas comuns de disco | 867 | 95 | 23 | Funcional parcial |
| `FIVEO.ASM` | Recursos BASIC 5.0 | 821 | 83 | 7 | Funcional parcial |
| `GENGRP.ASM` | Primitivas gráficas | 569 | 44 | 16 | Funcional parcial |
| `GIO86.ASM` | I/O independente de dispositivo | 2277 | 271 | 63 | Funcional parcial |
| `GIOCAS.ASM` | Cassete | 33 | 1 | 1 | Documentado |
| `GIOCOM.ASM` | Comunicação serial | 865 | 89 | 6 | Documentado/adaptável |
| `GIOCON.ASM` | Console | 119 | 7 | 3 | Funcional |
| `GIODSK.ASM` | Driver de disco | 1218 | 137 | 14 | Funcional parcial |
| `GIOKYB.ASM` | Teclado | 891 | 101 | 17 | Adaptado |
| `GIOLPT.ASM` | Impressora | 354 | 28 | 4 | Funcional parcial |
| `GIOSCN.ASM` | Dispositivo de tela | 327 | 32 | 12 | Funcional |
| `GIOTBL.ASM` | Tabela de dispositivos | 125 | 4 | 6 | Funcional conceitual |
| `GWDATA.ASM` | Dados globais e tabelas | 1565 | 19 | 296 | Funcional conceitual |
| `GWEVAL.ASM` | Avaliador de expressões | 1646 | 165 | 34 | Funcional |
| `GWINIT.ASM` | Inicialização | 456 | 28 | 4 | Adaptado |
| `GWLIST.ASM` | Listagem e edição de programa | 838 | 74 | 8 | Funcional |
| `GWMAIN.ASM` | Núcleo do interpretador | 3567 | 434 | 95 | Funcional parcial amplo |
| `GWRAM.ASM` | RAM independente de OEM | 466 | 3 | 13 | Funcional conceitual |
| `GWSTS.ASM` | Statements de tela, som e gráficos | 2347 | 259 | 52 | Funcional parcial |
| `IBMRES.ASM` | Palavras reservadas e tokens | 988 | 104 | 54 | Adaptado |
| `ITSA86.ASM` | Inicialização específica 8086 | 300 | 18 | 6 | Adaptado |
| `KANJ86.ASM` | Suporte Kanji | 43 | 4 | 4 | Adaptado |
| `MACLNG.ASM` | Linguagem macro gráfica | 258 | 36 | 9 | Parcial |
| `MATH1.ASM` | Pacote matemático principal | 3828 | 523 | 124 | Funcional parcial |
| `MATH2.ASM` | Entrada e promoção numérica | 1882 | 207 | 0 | Funcional |
| `NEXT86.ASM` | NEXT/FOR | 159 | 16 | 2 | Funcional |
| `SCNDRV.ASM` | Driver de tela | 2465 | 327 | 17 | Funcional parcial |
| `SCNEDT.ASM` | Editor orientado a tela | 462 | 44 | 17 | Adaptado |

## Análise individual

### ADVGRP.ASM

**Papel:** Gráficos avançados.  
**Título original:** ADVGRP - ADVANCED GENERALIZED GRAPHICS STUFF  
**Tamanho:** 34176 bytes, 1359 linhas, 133 labels internos, 109 referências externas.  
**Estado da porta:** Semântico funcional.

**Leitura do ASM:** PAINT, CIRCLE, GET/PUT e DRAW. Depende das primitivas genéricas de GENGRP e do driver de tela.

**Subseções declaradas no fonte:** PAINT - Fill an area with color; CIRCLE - Draw a circle; GET and PUT - read and write graphics bit array; GRAPHICS MACRO LANGUAGE SUPPORT.

**Entradas públicas principais:** `PAINT`, `CIRCLE`, `GPUTG`, `DRAW`.

**Tradução Python:** Comandos gráficos estruturados no RuntimeState e renderização SVG no navegador.

**Onde estudar a porta:** `app/asm_ports/advgrp.py`. O fonte original permanece em `reference/asm/ADVGRP.ASM`.

### BIBOOT.ASM

**Papel:** Bootstrap DOS/8086.  
**Título original:** BIBOOT - Initialization File for ASM86 BASICs  
**Tamanho:** 2176 bytes, 74 linhas, 1 labels internos, 1 referências externas.  
**Estado da porta:** Adaptado.

**Leitura do ASM:** Copia o bloco de controle do EXE para o segmento esperado pelo BASIC e transfere execução para START.

**Subseções declaradas no fonte:** ASM86 Version.

**Entradas públicas principais:** `LSTVAR`.

**Tradução Python:** Construção normal do processo Python e create_app. Segmentos ES/CS/DS deixam de existir.

**Onde estudar a porta:** `app/asm_ports/biboot.py`. O fonte original permanece em `reference/asm/BIBOOT.ASM`.

### BIMISC.ASM

**Papel:** Controle geral do interpretador.  
**Título original:** BIMISC  BASIC Interpreter miscellaneous routines/WHG/PGA etc.  
**Tamanho:** 24192 bytes, 944 linhas, 89 labels internos, 100 referências externas.  
**Estado da porta:** Funcional parcial.

**Leitura do ASM:** CLEAR, NEW/SCRATCH, RUN, STOP, END, CONT, RESTORE, pilha e traps.

**Subseções declaradas no fonte:** NODSKS, SCRATCH (NEW), RUNC, CLEARC, STKINI, QINLIN; DCOMPR, SYNCHR - REPLACEMENTS FOR COMPAR & SYNCHK IN RSTLES VERSION; TRAP ROUTINES - ON, OFF, STOP, INIT, REQUEST, FREE, RESET; RESTORE, STOP, END; CTRLPT, DDT, CONT, NULL, TRON, TROFF; SWAP, ERASE; CLEAR.

**Entradas públicas principais:** `STOPRG`, `TON`, `TOFF`, `CLEARC`, `STOP`, `ISLET`, `ISLET2`, `STKINI`, `GETSTK`, `SCRATH`, `SCRTCH`, `STPEND`, `CONT`, `ENDST`, `GTMPRT`, `RUNC`, `STPEND`, `ENDCON`, `RESTORE`, `STOP`, `RESFIN`, `STKERR`, `REASON`, `OMERR`, ... (49 entradas PUBLIC no total).

**Tradução Python:** RuntimeState.reset_runtime e dispatcher de GWBasicInterpreter.

**Onde estudar a porta:** `app/asm_ports/bimisc.py`. O fonte original permanece em `reference/asm/BIMISC.ASM`.

### BIPRTU.ASM

**Papel:** PRINT USING.  
**Título original:** BIPRTU  BASIC Interpreter PRINT USING Driver/WHG  
**Tamanho:** 16128 bytes, 469 linhas, 51 labels internos, 18 referências externas.  
**Estado da porta:** Funcional parcial.

**Leitura do ASM:** Scanner da máscara USING e formatação de campos string e numéricos.

**Subseções declaradas no fonte:** PRINT USING DRIVER.

**Entradas públicas principais:** `PRINUS`.

**Tradução Python:** app/asm_ports/biprtu.py com format_using puro.

**Onde estudar a porta:** `app/asm_ports/biprtu.py`. O fonte original permanece em `reference/asm/BIPRTU.ASM`.

### BIPTRG.ASM

**Papel:** Variáveis e arrays.  
**Título original:** BIPTRG  BASIC Interpreter pointer get routines/WHG/PGA  
**Tamanho:** 21376 bytes, 693 linhas, 66 labels internos, 46 referências externas.  
**Estado da porta:** Funcional.

**Leitura do ASM:** PTRGET, DIM, busca de variáveis, criação e expansão de arrays.

**Subseções declaradas no fonte:** DIMENSION & VARIABLE SEARCHING - PTRGET; MULTIPLE DIMENSION CODE.

**Entradas públicas principais:** `NOTFDD`, `NOTFNS`, `PTRGET`, `BSERR`, `PTRGT2`, `DIM`, `NOARYS`, `PTRGTN`, `PTRGTR`, `ERSFIN`, `ARYEXT`, `IADAHL`.

**Tradução Python:** Dicionários Python, bounds explícitos e helpers biptrg.py.

**Onde estudar a porta:** `app/asm_ports/biptrg.py`. O fonte original permanece em `reference/asm/BIPTRG.ASM`.

### BISTRS.ASM

**Papel:** Strings.  
**Título original:** BISTRS  BASIC Interpreter String  routines/WHG/PGA etc.  
**Tamanho:** 34560 bytes, 1110 linhas, 107 labels internos, 50 referências externas.  
**Estado da porta:** Funcional parcial.

**Leitura do ASM:** Descritores, heap de strings, garbage collection, concatenação e funções LEFT$, RIGHT$, MID$, LEN, VAL, STR$.

**Subseções declaradas no fonte:** STRING FUNCTIONS; STRING GARBAGE COLLECTION - GETSPA, GARBAG; STRING CONCATENATION; FREE UP STRING TEMPORARY - FRESTR, FREFAC, FRETMP, FRETMS; STRING FUNCTIONS - LEN, ASC, CHR$; STRING FUNCTIONS - LEFT$, RIGHT$, MID$; STRING FUNCTIONS - INSTR; STRING FUNCTIONS - LEFT HAND SIDE MID$; ...

**Entradas públicas principais:** `STRPRT`, `STROUI`, `LEN`, `FRESTR`, `STRCMP`, `VAL`, `STRLTI`, `FRETMS`, `FRETMP`, `RIGHT$`, `LEFT$`, `GARBA2`, `STR$`, `FRE`, `STRLIT`, `STRCPY`, `CAT`, `STRLT3`, `MID$`, `STRINI`, `STRIN1`, `STRAD1`, `PUTDEI`, `INCSTR`, ... (44 entradas PUBLIC no total).

**Tradução Python:** Strings Python eliminam gerenciamento manual; funções públicas são preservadas semanticamente.

**Onde estudar a porta:** `app/asm_ports/bistrs.py`. O fonte original permanece em `reference/asm/BISTRS.ASM`.

### CALL86.ASM

**Papel:** CALL nativo.  
**Título original:** CALL86  8086 CALL Statement  
**Tamanho:** 3200 bytes, 94 linhas, 9 labels internos, 15 referências externas.  
**Estado da porta:** Adaptado por segurança.

**Leitura do ASM:** CALL para endereços de máquina 8086.

**Entradas públicas principais:** `CALLS`, `CALLSL`.

**Tradução Python:** Registro controlado de callbacks Python por nome. Endereços arbitrários não são executados.

**Onde estudar a porta:** `app/asm_ports/call86.py`. O fonte original permanece em `reference/asm/CALL86.ASM`.

### DSKCOM.ASM

**Papel:** Rotinas comuns de disco.  
**Título original:** DSKCOM - - COMMON ROUTINES FOR DISK BASICS  
**Tamanho:** 25205 bytes, 867 linhas, 95 labels internos, 85 referências externas.  
**Estado da porta:** Funcional parcial.

**Leitura do ASM:** LOAD, SAVE, MERGE, FIELD, conversões MKI$/MKS$/MKD$ e leitura sequencial.

**Subseções declaradas no fonte:** FILINP AND FILGET -- SCAN A FILE NUMBER AND SETUP PTRFIL; FILSCN, FILFRM, AND FILIDX; Conversion Routines; Read Items From A Sequential File; LOAD and RUN routines; DISPATCH FOR DIRECT STATEMENT; SAVE COMMAND -- ASCII OR BINARY; DRIVER CODE FOR CLOSE; ...

**Entradas públicas principais:** `FIELD`, `PRGFLI`, `FILIND`, `MKI$`, `MKS$`, `MKD$`, `CVI`, `CVS`, `CVD`, `DLINE`, `PRGFL2`, `LRUN`, `LOAD`, `PRGFIN`, `MERGE`, `SAVE`, `OKGETM`, `RSET`, `LSET`, `CHNENT`, `OUTLOD`, `OKGET2`, `FIXINP`.

**Tradução Python:** pathlib e handles Python em diretório sandbox. LOAD/SAVE/MERGE e I/O sequencial estão no engine.

**Onde estudar a porta:** `app/asm_ports/dskcom.py`. O fonte original permanece em `reference/asm/DSKCOM.ASM`.

### FIVEO.ASM

**Papel:** Recursos BASIC 5.0.  
**Título original:** FIVEO 5.0 Features -WHILE/WEND, CALL, CHAIN, WRITE /P. Allen  
**Tamanho:** 24064 bytes, 821 linhas, 83 labels internos, 91 referências externas.  
**Estado da porta:** Funcional parcial.

**Leitura do ASM:** WHILE/WEND, CHAIN, COMMON, WRITE.

**Subseções declaradas no fonte:** WHILE , WEND; CHAIN; WRITE.

**Entradas públicas principais:** `WHILE`, `WEND`, `CHAIN`, `COMMON`, `CHNRET`, `SKPNAM`, `WRITE`.

**Tradução Python:** Controle estruturado por posição de programa; WRITE com csv; CHAIN simplificado.

**Onde estudar a porta:** `app/asm_ports/fiveo.py`. O fonte original permanece em `reference/asm/FIVEO.ASM`.

### GENGRP.ASM

**Papel:** Primitivas gráficas.  
**Título original:** GENGRP  GENERALIZED GRAPHICS    /WHG  
**Tamanho:** 15616 bytes, 569 linhas, 44 labels internos, 36 referências externas.  
**Estado da porta:** Funcional parcial.

**Leitura do ASM:** PSET, PRESET, POINT, LINE, scanner de coordenadas.

**Subseções declaradas no fonte:** SCAN A COORDINATE - SCAN1 AND SCAND; PSET,PRESET,POINT; UTILITY ROUTINES FOR LINE CODE; LINE COMMAND; Graphics Initialization.

**Entradas públicas principais:** `HLFDE`, `SCAND`, `ATRSCN`, `SCAN1`, `DOGRPH`, `XCHGX`, `XCHGY`, `XDELT`, `YDELT`, `PSET`, `PRESET`, `POINT`, `NEGHL`, `GLINE`, `GRPINI`, `GRPRST`.

**Tradução Python:** Objetos de comando gráfico independentes de hardware.

**Onde estudar a porta:** `app/asm_ports/gengrp.py`. O fonte original permanece em `reference/asm/GENGRP.ASM`.

### GIO86.ASM

**Papel:** I/O independente de dispositivo.  
**Título original:** GIO86   - BASIC-86 Interpreter Device Independent I/O Module  
**Tamanho:** 67200 bytes, 2277 linhas, 271 labels internos, 100 referências externas.  
**Estado da porta:** Funcional parcial.

**Leitura do ASM:** OPEN, CLOSE, PRINT, INPUT de arquivo, BLOAD/BSAVE, EOF, LOC, LOF e dispatch geral.

**Subseções declaradas no fonte:** OPEN statement; CLOSE, WIDTH Statements; BSAVE, BLOAD Statements; LPRINT, PRINT Statements; EOF, LOC, LOF  Functions; GET/PUT - Random disk I/O Statements; Misc. Parsing Routines; Major I/O Routines; ...

**Entradas públicas principais:** `OPEN`, `CLOSE`, `WIDTHS`, `BLOAD`, `BSAVE`, `LPRINT`, `PRINT`, `EOF`, `LOC`, `LOF`, `DPUTG`, `FILINP`, `FILGET`, `GETPTR`, `FILSET`, `FILSCN`, `DIRDO`, `ADRGET`, `PRGFIL`, `NULOPM`, `CLSALL`, `CLSFIL`, `INCHR`, `INDSKC`, ... (63 entradas PUBLIC no total).

**Tradução Python:** Facade única do interpretador para tela, arquivos e spool de impressora.

**Onde estudar a porta:** `app/asm_ports/gio86.py`. O fonte original permanece em `reference/asm/GIO86.ASM`.

### GIOCAS.ASM

**Papel:** Cassete.  
**Título original:** GIOCAS - Cassette Machine Independent Device Driver Code  
**Tamanho:** 640 bytes, 33 linhas, 1 labels internos, 1 referências externas.  
**Estado da porta:** Documentado.

**Leitura do ASM:** Hook do motor e dispositivo de fita.

**Entradas públicas principais:** `MOTOR`.

**Tradução Python:** Mantido como abstração documentada, sem hardware físico.

**Onde estudar a porta:** `app/asm_ports/giocas.py`. O fonte original permanece em `reference/asm/GIOCAS.ASM`.

### GIOCOM.ASM

**Papel:** Comunicação serial.  
**Título original:** GIOCOM - Communications Machine Independent Device Driver Code  
**Tamanho:** 29568 bytes, 865 linhas, 89 labels internos, 30 referências externas.  
**Estado da porta:** Documentado/adaptável.

**Leitura do ASM:** Inicialização, terminação, polling e dispatch da porta COM.

**Subseções declaradas no fonte:** Communications Generalized I/O Routines; COM OPEN.

**Entradas públicas principais:** `COMDSP`, `COMINI`, `COMTRM`, `COMINI`, `COMTRM`, `POLCOM`.

**Tradução Python:** Isolado para adapter substituível. UART não é emulada.

**Onde estudar a porta:** `app/asm_ports/giocom.py`. O fonte original permanece em `reference/asm/GIOCOM.ASM`.

### GIOCON.ASM

**Papel:** Console.  
**Título original:** GIOCON - Machine Independent CONS: Device Support  
**Tamanho:** 3200 bytes, 119 linhas, 7 labels internos, 5 referências externas.  
**Estado da porta:** Funcional.

**Leitura do ASM:** CONS e saída crua de console.

**Subseções declaradas no fonte:** CONS (Raw-CRT output Dispatch Table and Routines).

**Entradas públicas principais:** `CONDSP`, `_RET`, `CONSOT`.

**Tradução Python:** ScreenBuffer e terminal HTML.

**Onde estudar a porta:** `app/asm_ports/giocon.py`. O fonte original permanece em `reference/asm/GIOCON.ASM`.

### GIODSK.ASM

**Papel:** Driver de disco.  
**Título original:** GIODSK - BASIC-86 Generalized I/O Disk Driver  
**Tamanho:** 35456 bytes, 1218 linhas, 137 labels internos, 60 referências externas.  
**Estado da porta:** Funcional parcial.

**Leitura do ASM:** Diretório, OPEN/CLOSE hooks, FILES, KILL, NAME, RESET, SYSTEM.

**Subseções declaradas no fonte:** GLOBAL TEMPS and DEFS; Misc. Disk Routines; OPEN hook for Disk and all Directory handling; CLOSE (CLSFIL) hook for Disk files; Disk Sequential Input; Disk Sequential Output; GET and PUT for Disk Files; Primitive Disk sector I/O routines; ...

**Entradas públicas principais:** `DSKDSP`, `DFSTLD`, `PROSAV`, `CMPFBC`, `PENCOD`, `PROLOD`, `PROCHK`, `PRODIR`, `FILES`, `KILL`, `NAME`, `RESET`, `SYSTEM`, `SYSTME`.

**Tradução Python:** Filesystem sandboxado. FILES/KILL/NAME implementados; detalhes FCB/DOS não são emulados.

**Onde estudar a porta:** `app/asm_ports/giodsk.py`. O fonte original permanece em `reference/asm/GIODSK.ASM`.

### GIOKYB.ASM

**Papel:** Teclado.  
**Título original:** GIOKYB - Machine Independent Keyboard Device Driver Code  
**Tamanho:** 29056 bytes, 891 linhas, 101 labels internos, 67 referências externas.  
**Estado da porta:** Adaptado.

**Leitura do ASM:** KEYIN, INKEY$, polling, traps e buffer de teclado.

**Subseções declaradas no fonte:** Keyboard Primitive I/O Routines; Keyboard Interrupt/Trap Checking in an Operating System Environment; CHKKYB - OEM Version of POLKEY; CNTCCN, PKQUE, TRPKTB; Machine independent Keyboard input routines CHSNS, INKEY$; Cursor Support.

**Entradas públicas principais:** `KYBDSP`, `KYBINI`, `KYBTRM`, `KYBCLR`, `KYBSIN`, `INCHRI`, `CHGET`, `KEYIN`, `POLKEY`, `CHKKYB`, `CHSNS`, `SFTOFF`, `KYBSNS`, `FKYSNS`, `INKEY`, `STCTYP`, `SETCSR`.

**Tradução Python:** INPUT assíncrono por requisição HTTP. O navegador faz edição de linha.

**Onde estudar a porta:** `app/asm_ports/giokyb.py`. O fonte original permanece em `reference/asm/GIOKYB.ASM`.

### GIOLPT.ASM

**Papel:** Impressora.  
**Título original:** GIOLPT - Line Printer Machine Independent Device Driver Code  
**Tamanho:** 11136 bytes, 354 linhas, 28 labels internos, 19 referências externas.  
**Estado da porta:** Funcional parcial.

**Leitura do ASM:** Driver LPT e posição da impressora.

**Subseções declaradas no fonte:** Line Printer Primitive I/O Routines.

**Entradas públicas principais:** `LPTDSP`, `LPTINI`, `LPTTRM`, `LPOS`.

**Tradução Python:** Spool de texto em memória para LPRINT/LLIST.

**Onde estudar a porta:** `app/asm_ports/giolpt.py`. O fonte original permanece em `reference/asm/GIOLPT.ASM`.

### GIOSCN.ASM

**Papel:** Dispositivo de tela.  
**Título original:** GIOSCN - Screen Machine Independent Device Driver Code  
**Tamanho:** 9216 bytes, 327 linhas, 32 labels internos, 20 referências externas.  
**Estado da porta:** Funcional.

**Leitura do ASM:** Bridge para primitives de CRT e posição.

**Subseções declaradas no fonte:** CRT Primitive I/O Routines.

**Entradas públicas principais:** `SCNDSP`, `SCNINI`, `SCNTRM`, `SCNSWD`, `SCNSOT`, `SCNGPS`, `SCNGWD`, `SCNSCW`, `SCNGCW`, `CALTTY`, `$CATTY`, `POS`.

**Tradução Python:** ScreenBuffer.

**Onde estudar a porta:** `app/asm_ports/gioscn.py`. O fonte original permanece em `reference/asm/GIOSCN.ASM`.

### GIOTBL.ASM

**Papel:** Tabela de dispositivos.  
**Título original:** GIOTBL - Device Name Table, Dispatch Table Address Tables  
**Tamanho:** 3072 bytes, 125 linhas, 4 labels internos, 15 referências externas.  
**Estado da porta:** Funcional conceitual.

**Leitura do ASM:** Nomes de dispositivos e tabelas de ponteiros para dispatch.

**Subseções declaradas no fonte:** Device name table.

**Entradas públicas principais:** `_DVTBL`, `_DVPTR`, `_DVINI`, `_DVTRM`, `$_NDEV`, `$_&NAM`.

**Tradução Python:** Dicionário simbólico de adapters em giotbl.py.

**Onde estudar a porta:** `app/asm_ports/giotbl.py`. O fonte original permanece em `reference/asm/GIOTBL.ASM`.

### GWDATA.ASM

**Papel:** Dados globais e tabelas.  
**Título original:** GWDATA copied from BINTRP.MAC  
**Tamanho:** 37632 bytes, 1565 linhas, 19 labels internos, 234 referências externas.  
**Estado da porta:** Funcional conceitual.

**Leitura do ASM:** Tokens, mensagens de erro, constantes e RAM compartilhada do interpretador.

**Subseções declaradas no fonte:** ROM VERSION INITALIZATION, AND CONSTANTS; ERROR MESSAGE TABLE; CONSTANTS FOR ROM BASIC I/O, RNDX, FDIV, USRGO; LOW SEGMENT -- RAM-- IE THIS STUFF IS NOT CONSTANT; LOW SEGMENT -- RAM-- IE THIS STUFF IS NOT CONSTANT; TEXT CONSTANTS FOR PRINT OUT.

**Entradas públicas principais:** `BEGCSG`, `CPMWRM`, `CPMENT`, `$START`, `START`, `OPTAB`, `FRCTBL`, `DBLDSP`, `OPCNT`, `SNGDSP`, `INTDSP`, `ERRTAB`, `ERRNF`, `ERRSN`, `ERRRG`, `ERROD`, `ERRFC`, `$OVMSG`, `OVRMSG`, `ERROV`, `ERROM`, `ERRUS`, `ERRBS`, `ERRDD`, ... (296 entradas PUBLIC no total).

**Tradução Python:** Constantes em gwdata.py e estado mutável em RuntimeState.

**Onde estudar a porta:** `app/asm_ports/gwdata.py`. O fonte original permanece em `reference/asm/GWDATA.ASM`.

### GWEVAL.ASM

**Papel:** Avaliador de expressões.  
**Título original:** GWEVAL Copied from BINTRP.MAC  
**Tamanho:** 50304 bytes, 1646 linhas, 165 labels internos, 325 referências externas.  
**Estado da porta:** Funcional.

**Leitura do ASM:** FRMEVL/EVAL, operadores lógicos e relacionais, constantes, variáveis e chamadas de função.

**Subseções declaradas no fonte:** FORMULA EVALUATION CODE; EVAL - EVALUATE VARIABLE, CONSTANT, FUNCTION CALL; MORE FORMULA EVALUATION - LOGICAL, RELATIONAL OPS; USER DEFINED (USR) ASSEMBLY LANGUAGE FUNCTION CODE; SIMPLE-USER-DEFINED-FUNCTION CODE; STRING FUNCTIONS - LEFT HAND SIDE MID$; INP, OUT, WAIT, CONSOLE, WIDTH; EXECUTE BASIC PROGRAM ON PROM.

**Entradas públicas principais:** `DEF`, `FNINP`, `FNOUT`, `FNWAIT`, `LABBCK`, `FRMEQL`, `FRMPRN`, `FRMEVL`, `FRMCHK`, `TSTOP`, `INTDIV`, `EVAL`, `PARCHK`, `ISVAR`, `RETVAR`, `MAKUPL`, `MAKUPS`, `CNSGET`, `$OHCNS`, `OCTCNS`, `HOCFIN`, `MINPLS`, `GETYPR`, `GIVDBL`, ... (34 entradas PUBLIC no total).

**Tradução Python:** Lexer e Pratt parser sem eval do Python.

**Onde estudar a porta:** `app/services/expression.py + app/asm_ports/gweval.py`. O fonte original permanece em `reference/asm/GWEVAL.ASM`.

### GWINIT.ASM

**Papel:** Inicialização.  
**Título original:** GWINIT GW-BASIC-86 Initialization  
**Tamanho:** 14720 bytes, 456 linhas, 28 labels internos, 80 referências externas.  
**Estado da porta:** Adaptado.

**Leitura do ASM:** Parâmetros do SO, buffers de disco e ponteiros de memória TXTTAB/VARTAB/STREND.

**Subseções declaradas no fonte:** INIT - System Initialization Code; Read Operating System Parameters (memsiz etc.); Allocate Space for Disk Buffers; INIT TXTAB, STKTOP, VARTAB, MEMSIZ, FRETOP, STREND.

**Entradas públicas principais:** `INIT`, `CMDERR`, `$LAST`, `LASTWR`.

**Tradução Python:** Inicialização de objetos e diretório de dados.

**Onde estudar a porta:** `app/asm_ports/gwinit.py`. O fonte original permanece em `reference/asm/GWINIT.ASM`.

### GWLIST.ASM

**Papel:** Listagem e edição de programa.  
**Título original:** GWLIST Copied from BINTRP.MAC  
**Tamanho:** 22912 bytes, 838 linhas, 74 labels internos, 317 referências externas.  
**Estado da porta:** Funcional.

**Leitura do ASM:** LIST, LLIST, DELETE e reconstrução textual de linhas tokenizadas.

**Subseções declaradas no fonte:** ROM VERSION INITALIZATION, AND CONSTANTS; EXTENDED LIST, DELETE, LLIST.

**Entradas públicas principais:** `LLIST`, `LIST`, `LISPRT`, `BUFLIN`, `PLOOP2`, `TSTANM`, `DELETE`, `DEL`.

**Tradução Python:** Programa em dict line_number -> source; LIST/DELETE trabalham diretamente sobre texto.

**Onde estudar a porta:** `app/asm_ports/gwlist.py`. O fonte original permanece em `reference/asm/GWLIST.ASM`.

### GWMAIN.ASM

**Papel:** Núcleo do interpretador.  
**Título original:** GWMAIN Copied from BINTRP.MAC  
**Tamanho:** 108800 bytes, 3567 linhas, 434 labels internos, 330 referências externas.  
**Estado da porta:** Funcional parcial amplo.

**Leitura do ASM:** Loop principal, dispatcher de statements, FOR/GOTO/GOSUB/IF/INPUT/LET, erros e memória.

**Subseções declaradas no fonte:** ROM VERSION INITALIZATION, AND CONSTANTS; GENERAL STORAGE MANAGEMENT ROUTINES - FNDFOR, BLTU, GETSTK; ERROR HANDLING; STPRDY, READY, MAIN, CHEAD; SCNLIN, FNDLIN - SCAN LINE RANGE AND FIND LINE # IN PROGRAM; PRE FAST CRUNCH - COMPACTIFICATION; FAST CRUNCH - COMPACTIFICATION; THE NON-EXTENDED "LIST" COMMAND; ...

**Entradas públicas principais:** `AUTO`, `DATAS`, `DEFDBL`, `DEFINT`, `DEFREA`, `DEFSTR`, `ELSES`, `ERRORS`, `FOR`, `GOSUB`, `GOTO`, `IFS`, `INPUT`, `LET`, `LINE`, `ONGOTO`, `OPTION`, `PEEK`, `POKE`, `RANDOM`, `READ`, `REM`, `RESEQ`, `RESUME`, ... (95 entradas PUBLIC no total).

**Tradução Python:** GWBasicInterpreter em app/services/interpreter.py.

**Onde estudar a porta:** `app/services/interpreter.py + app/asm_ports/gwmain.py`. O fonte original permanece em `reference/asm/GWMAIN.ASM`.

### GWRAM.ASM

**Papel:** RAM independente de OEM.  
**Título original:** GWRAM - GW BASIC OEM Independent RAM Declarations  
**Tamanho:** 12672 bytes, 466 linhas, 3 labels internos, 0 referências externas.  
**Estado da porta:** Funcional conceitual.

**Leitura do ASM:** Declarações mutáveis de estado e buffers.

**Subseções declaradas no fonte:** Sign on message and other data to be discarded after INIT; Page Dependent OEM Independent Variables; Page Independent Uninitialized RAM Location Definitions.

**Entradas públicas principais:** `HEDING`, `$DATE`, `CERMSG`, `NAME`, `NAME`, `NAME`, `PDIDS1`, `FPDVAR`, `LPDVAR`, `NAME`, `NAME`, `FOPTSZ`, `KYBQSZ`.

**Tradução Python:** Campos nomeados de RuntimeState.

**Onde estudar a porta:** `app/models/runtime.py + app/asm_ports/gwram.py`. O fonte original permanece em `reference/asm/GWRAM.ASM`.

### GWSTS.ASM

**Papel:** Statements de tela, som e gráficos.  
**Título original:** GWSTS - GW-BASIC Common Statement Support  
**Tamanho:** 63232 bytes, 2347 linhas, 259 labels internos, 125 referências externas.  
**Estado da porta:** Funcional parcial.

**Leitura do ASM:** CLS, LOCATE, WIDTH, COLOR, SCREEN, PUT/GET, PLAY, SOUND e parsers auxiliares.

**Subseções declaradas no fonte:** CLS,LOCATE,WIDTH (of screen),LCOPY; COLOR,GETLIN,SCREEN (function and statement); PUT & GET (Distinguish Disk from Graphics); Parsing Routines for GWSTS; Graphics Support Specific to the 8086; VARPT2 - VARPTR$ Function; PLAY/SOUND statements; General Event Trapping Code; ...

**Entradas públicas principais:** `PATCHG`, `CLS`, `LOCATE`, `GWWID`, `LCOPYS`, `COLOR`, `GETLIN`, `SCRENF`, `SCREEN`, `PUT`, `GET`, `SCNINT`, `EOSCHK`, `LINLP3`, `VARPT2`, `PLAYS`, `SNDINI`, `SNDRST`, `BEEPS`, `BEEP`, `SOUNDS`, `ONGOTP`, `SETGSB`, `CHKINT`, ... (52 entradas PUBLIC no total).

**Tradução Python:** Tela e gráficos implementados; som é registrado como evento; detalhes físicos são abstraídos.

**Onde estudar a porta:** `app/asm_ports/gwsts.py`. O fonte original permanece em `reference/asm/GWSTS.ASM`.

### IBMRES.ASM

**Papel:** Palavras reservadas e tokens.  
**Título original:** IBMRES - IBM compatible reserved words / MLC  
**Tamanho:** 16256 bytes, 988 linhas, 104 labels internos, 15 referências externas.  
**Estado da porta:** Adaptado.

**Leitura do ASM:** Tabela de palavras reservadas, CRUNCH tokenizador e reconstrução LIST.

**Subseções declaradas no fonte:** Equates and External Declarations; Extended reserved words; CRUNCH code to handle extended reserved words; LIST code for extended reserved words; Extended Statement Dispatching; EVAL code for extended functions.

**Entradas públicas principais:** `$KEY2B`, `$COM2B`, `$PEN2B`, `$STR2B`, `STMDSP`, `NUMCMD`, `THENTK`, `TABTK`, `STEPTK`, `USRTK`, `FNTK`, `SPCTK`, `NOTTK`, `ERLTK`, `ERCTK`, `USINTK`, `INSRTK`, `SNGQTK`, `CLINTK`, `GREATK`, `EQULTK`, `LESSTK`, `PLUSTK`, `MINUTK`, ... (54 entradas PUBLIC no total).

**Tradução Python:** Parser textual direto. Tokens binários ficam como referência acadêmica.

**Onde estudar a porta:** `app/asm_ports/ibmres.py`. O fonte original permanece em `reference/asm/IBMRES.ASM`.

### ITSA86.ASM

**Papel:** Inicialização específica 8086.  
**Título original:** ITSA86 - Resident Initialization for I8086  
**Tamanho:** 8704 bytes, 300 linhas, 18 labels internos, 30 referências externas.  
**Estado da porta:** Adaptado.

**Leitura do ASM:** Mapeamento de segmentos e suporte residente.

**Subseções declaradas no fonte:** INITSA; Initialization Support Routines; End of the New CS:.

**Entradas públicas principais:** `WORDS`, `INITSA`, `BASVAR`, `MAPCLC`, `MAPINI`, `SEGOFF`.

**Tradução Python:** Sem segmentos de memória em Python. Responsabilidade absorvida pelo bootstrap do processo.

**Onde estudar a porta:** `app/asm_ports/itsa86.py`. O fonte original permanece em `reference/asm/ITSA86.ASM`.

### KANJ86.ASM

**Papel:** Suporte Kanji.  
**Título original:** KANJ86 - KANJI String Function Support for Basic-86  
**Tamanho:** 768 bytes, 43 linhas, 4 labels internos, 1 referências externas.  
**Estado da porta:** Adaptado.

**Leitura do ASM:** Funções de comprimento, posição e conversão específicas do encoding da época.

**Entradas públicas principais:** `KTNFN`, `JISFN`, `KLENFN`, `KPOSFN`.

**Tradução Python:** Unicode Python e helpers kanj86.py.

**Onde estudar a porta:** `app/asm_ports/kanj86.py`. O fonte original permanece em `reference/asm/KANJ86.ASM`.

### MACLNG.ASM

**Papel:** Linguagem macro gráfica.  
**Título original:** MACLNG - MACRO LANGUAGE DRIVER  
**Tamanho:** 6528 bytes, 258 linhas, 36 labels internos, 13 referências externas.  
**Estado da porta:** Parcial.

**Leitura do ASM:** Driver do macro DRAW, leitura de valores e variáveis.

**Entradas públicas principais:** `FETCHR`, `FETCHZ`, `DECFET`, `VALSCN`, `VALSC2`, `VARGET`, `NEGD`, `MACLNG`, `MCLXEQ`.

**Tradução Python:** DRAW é preservado como comando estruturado para adapter gráfico; parser completo pode ser expandido.

**Onde estudar a porta:** `app/asm_ports/maclng.py`. O fonte original permanece em `reference/asm/MACLNG.ASM`.

### MATH1.ASM

**Papel:** Pacote matemático principal.  
**Título original:** MATH86 8086 MATH PACK  
**Tamanho:** 117888 bytes, 3828 linhas, 523 labels internos, 50 referências externas.  
**Estado da porta:** Funcional parcial.

**Leitura do ASM:** FAC, operações aritméticas, transcendentes, conversões e formatação numérica.

**Subseções declaradas no fonte:** $FOTCI  CONVERT INTEGER IN (FACLO) TO ASCII DIGITS; $PUFXE  PRINT USING FIX-UP CODE; $FOTZS  ZERO SUPRESSION UPON OUTPUT ROUTINE; $PUFE	 PRINT USING FLOATING IN "E" TYPE FORMAT; CON86	 8086 BASIC CONSTANTS; $SIN	 SINGLE PRECISION SINE/COSINE/TANGENT/ARCTANGENT; $FINE	 ROUTINE TO ADJUST INPUT NUMBER FOR EXPONENT; $OVFLS  OVERFLOW CODE; ...

**Entradas públicas principais:** `ABSFN`, `ATN`, `COS`, `DADD`, `DDIV`, `DMULT`, `EXP`, `FINDBL`, `FIN`, `FOUT`, `FRCDBL`, `FRCINT`, `FRCSNG`, `INEG`, `INEG2`, `INT`, `LOG`, `LOPFND`, `NEG`, `PUFOUT`, `RND`, `SIGN`, `SIN`, `SQR`, ... (124 entradas PUBLIC no total).

**Tradução Python:** math Python e funções explícitas em math1.py.

**Onde estudar a porta:** `app/asm_ports/math1.py`. O fonte original permanece em `reference/asm/MATH1.ASM`.

### MATH2.ASM

**Papel:** Entrada e promoção numérica.  
**Título original:** (sem TITLE)  
**Tamanho:** 71424 bytes, 1882 linhas, 207 labels internos, 0 referências externas.  
**Estado da porta:** Funcional.

**Leitura do ASM:** Leitura de dígitos, expoentes e promoção integer -> single -> double.

**Subseções declaradas no fonte:** $FIDIG  ADD TEXT DIGIT TO CURRENT ACCUMULATED NUMBER; $FINEX  EXPONENT INPUT ROUTINE; FINFC	 INPUT FORCE ROUTINES FOR "#","%","!"; $FLT	 CONVERT INTEGER IN (DX) TO REAL AND STORE IN FAC; $FMULD  DOUBLE PRECISION MULTIPLICATION; $FMULS  SINGLE PRECISION 8086 MULTIPLICATION; $FOTAN  ROUTINE TO PUT IN DECIMAL POINT AND LEADING ZEROS; $FOTCV  CONVERT FAC TO ASCII DIGITS; ...

**Entradas públicas:** o arquivo não declara `PUBLIC`; ele participa como suporte interno ligado a outros módulos.

**Tradução Python:** parse_basic_number em math2.py.

**Onde estudar a porta:** `app/asm_ports/math2.py`. O fonte original permanece em `reference/asm/MATH2.ASM`.

### NEXT86.ASM

**Papel:** NEXT/FOR.  
**Título original:** NEXT86 CODE  
**Tamanho:** 4480 bytes, 159 linhas, 16 labels internos, 23 referências externas.  
**Estado da porta:** Funcional.

**Leitura do ASM:** Formato exato do frame FOR na pilha e lógica de STEP/limite.

**Entradas públicas principais:** `NEXT`, `NEXTS`.

**Tradução Python:** ForFrame dataclass e next_for.

**Onde estudar a porta:** `app/asm_ports/next86.py`. O fonte original permanece em `reference/asm/NEXT86.ASM`.

### SCNDRV.ASM

**Papel:** Driver de tela.  
**Título original:** SCNDRV  This is the OS independent Screen Driver for GW BASIC  
**Tamanho:** 77056 bytes, 2465 linhas, 327 labels internos, 39 referências externas.  
**Estado da porta:** Funcional parcial.

**Leitura do ASM:** Cursor, clear, output, leitura de linha, scroll e dimensões físicas.

**Subseções declaradas no fonte:** DATA DEFINITIONS - Miscellaneous; DATA DEFINITIONS - Internal routines(with usage description); DATA DEFINITIONS - External routines and data; DATA DEFINITIONS - Literals; SCNIPL, SCNSWI AND SCNWDO   The parameter setting routines; CURSOR READ/WRITE; TERMINATOR TABLE READ/WRITE/INITIALIZE; CHARACTER OUTPUT; ...

**Entradas públicas principais:** `SCNSWI`, `SCNCLR`, `SCNLOC`, `SCNOUT`, `SCNRDL`, `SCNPOS`, `SCNRDT`, `SCNGWI`, `SCNMRK`, `SCNIPL`, `SCNBRK`, `TRMLNF`, `TRMEOL`, `TRMWRP`, `TRMNWP`, `TRMNUL`, `SCNSIZ`.

**Tradução Python:** ScreenBuffer e wrappers scndrv.py.

**Onde estudar a porta:** `app/models/runtime.py + app/asm_ports/scndrv.py`. O fonte original permanece em `reference/asm/SCNDRV.ASM`.

### SCNEDT.ASM

**Papel:** Editor orientado a tela.  
**Título original:** SCNEDT  Screen Oriented Editor for GW-BASIC  
**Tamanho:** 13184 bytes, 462 linhas, 44 labels internos, 38 referências externas.  
**Estado da porta:** Adaptado.

**Leitura do ASM:** Entrada de programa, INPUT, edição, break e auto-edit de erro.

**Subseções declaradas no fonte:** DATA DEFINITIONS; Entry points for editing; MAIN loop of editor; Exit, return current logical line; EDIT code; ASCII LOAD and SAVE line handler.

**Entradas públicas principais:** `PINLIN`, `INLIN`, `SINLIN`, `QINLIN`, `SCNSEM`, `EDTBRK`, `ERREDT`, `EDIT`, `CHRLNF`, `CHRRET`, `PINLIN`, `QINLIN`, `INLIN`, `SINLIN`, `EDIT`, `ERREDT`, `OUTCH1`.

**Tradução Python:** Campo de comando no browser e estado InputRequired.

**Onde estudar a porta:** `app/controllers/basic_controller.py + app/asm_ports/scnedt.py`. O fonte original permanece em `reference/asm/SCNEDT.ASM`.

## Limites deliberados

A versão atual é uma porta acadêmica executável, não uma reprodução binária do GW-BASIC. Os pontos que exigiriam emulação completa de hardware ou compatibilidade byte a byte, como Microsoft Binary Format, BIOS, UART, cassette, BLOAD/BSAVE de memória bruta, VARPTR/DEF SEG e chamada de endereços 8086, foram convertidos em abstrações seguras e legíveis. O índice completo de labels, PUBLIC, EXTRN, INCLUDE e números de linha está em `docs/ASM_ROUTINE_INDEX.json`.
