# Guia acadêmico de portabilidade ASM 8086 para Python 3

## 1. O que foi preservado

A porta preserva o modelo mental do interpretador: programa numerado, dispatcher de statements, avaliação de expressões, tabela de variáveis, arrays, pilha de GOSUB, frames de FOR, cursor de DATA, dispositivos e erros BASIC.

O que não foi preservado de forma literal é a representação física desses elementos em memória 8086.

## 2. Exemplo: registradores para variáveis nomeadas

No ASM, uma rotina pode usar BX como ponteiro para o texto, DX para um operando e flags para indicar o resultado. Em Python, a assinatura da função torna essas dependências explícitas:

```python
def next_for(state: RuntimeState, variable: str | None = None):
    frame = state.for_stack[-1]
    current = float(state.get_var(frame.variable)) + frame.step
```

O ganho acadêmico é que o papel de cada valor aparece no nome, em vez de depender do conhecimento da convenção local de registradores.

## 3. Exemplo: pilha FOR/NEXT

`NEXT86.ASM` documenta um frame manual de aproximadamente 16 a 19 bytes, com variável, sinal, STEP, limite, linha e ponteiro de texto. A tradução é direta em intenção:

```python
@dataclass(slots=True)
class ForFrame:
    variable: str
    limit: float
    step: float
    line_index: int
    statement_index: int
```

Isto é uma portabilidade semântica do layout da pilha.

## 4. Exemplo: FAC e avaliador

`GWEVAL.ASM`, `MATH1.ASM` e `MATH2.ASM` trabalham com o FAC, o acumulador numérico do BASIC. No Python, cada expressão retorna explicitamente seu valor. O parser de `app/services/expression.py` usa precedência própria e não chama `eval()`.

## 5. Exemplo: memória e ponteiros

`BIPTRG.ASM` procura variáveis em blocos compactados e devolve endereços. A porta usa:

```python
state.variables["A"] = 10
state.arrays["M"][(2, 3)] = 42
```

A semântica permanece, mas o endereço físico deixa de ser parte da API.

## 6. Exemplo: tela

`SCNDRV.ASM`, `GIOSCN.ASM` e `SCNEDT.ASM` dependem de cursor, teclado e tela física. Na aplicação Flask:

- `ScreenBuffer` representa a tela lógica.
- o navegador faz edição da linha de comando.
- `InputRequired` suspende a execução sem bloquear um worker HTTP.
- os comandos gráficos são enviados como objetos e renderizados em SVG.

## 7. Exemplo: arquivo

`GIO86.ASM`, `DSKCOM.ASM` e `GIODSK.ASM` usam serviços DOS e devices. O porte usa `pathlib` e handles Python, sempre restritos ao diretório `BASIC_DATA_DIR`.

## 8. Diferença entre portabilidade e emulação

Uma emulação 8086 tentaria reproduzir instruções, registradores, memória segmentada, interrupções e formatos binários. Este projeto não faz isso. Ele reimplementa o interpretador em Python mantendo a separação e a intenção do código original, para que o estudante consiga relacionar cada módulo antigo com um componente moderno.
