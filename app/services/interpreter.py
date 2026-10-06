"""High-level GW-BASIC interpreter engine.

This is a semantic Python 3 port of the control flow distributed mainly across
GWMAIN.ASM, BIMISC.ASM, NEXT86.ASM, FIVEO.ASM, DSKCOM.ASM and GIO86.ASM.

The original code is tightly coupled to 8086 registers, tokenized program RAM,
DOS file handles and jump tables. Here the same responsibilities are explicit:
program counter tuples, Python exceptions for BASIC errors, dict-backed program
storage, structured FOR/GOSUB stacks and a sandboxed file directory.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import io
import math
import os
import random
import re
from typing import Any

from app.models.runtime import RuntimeState, BasicError, InputRequired, FileHandle
from app.services.expression import ExpressionParser
from app.services import cassette, legacy_basic
from app.asm_ports import biptrg, next86, bistrs, biprtu


@dataclass
class Control:
    jump: tuple[int, int] | None = None
    stop: bool = False


class GWBasicInterpreter:
    """A readable interpreter rather than a cycle-accurate 8086 emulator."""

    def __init__(self, data_dir: str | os.PathLike = "data", max_steps: int = 100_000):
        self.state = RuntimeState()
        self.expr = ExpressionParser(self.state)
        self.data_dir = Path(data_dir).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.max_steps = int(max_steps)
        # CAS1: is a mounted audio cassette image. WAV is the lossless default;
        # MP3 can be mounted/generated when ffmpeg is available.
        self.cassette_path = self.data_dir / 'cassette.wav'

    # ------------------------------------------------------------------
    # Front-door API. Roughly MAIN/STPRDY in GWMAIN.ASM plus SCNEDT input.
    # ------------------------------------------------------------------
    def submit(self, text: str) -> dict[str, Any]:
        text = text.rstrip("\r\n")
        try:
            if self.state.pending_input is not None:
                return self.feed_input(text)

            m = re.match(r"^\s*(\d+)\s*(.*)$", text)
            if m:
                number = int(m.group(1)); body = m.group(2).rstrip()
                if body:
                    self.state.program[number] = body
                else:
                    self.state.program.pop(number, None)
                return self.result("ok")

            if not text.strip():
                return self.result("ok")

            control = self.execute_statement(text.strip(), -1, 0, direct=True)
            if isinstance(control, _ResultControl):
                return control.result
            if control and control.jump:
                # Direct GOTO/GOSUB begins execution at a stored line.
                return self.run(position=control.jump)
            return self.result("ok")
        except InputRequired as req:
            self.state.pending_input = req.variables
            self.state.pending_prompt = req.prompt
            return self.result("waiting_input", prompt=req.prompt)
        except BasicError as exc:
            self.state.last_error = str(exc)
            self.state.emit(f"?{exc}")
            return self.result("error", error=str(exc))
        except Exception as exc:
            self.state.last_error = str(exc)
            self.state.emit(f"?Internal port error: {exc}")
            return self.result("error", error=str(exc))

    def result(self, status: str, **extra) -> dict[str, Any]:
        payload = {
            "status": status,
            "output": self.state.consume_output(),
            "screen": self.state.screen.text(),
            "program_lines": len(self.state.program),
            "variables": dict(sorted(self.state.variables.items())),
            "graphics": self.state.graphics_commands[-500:],
        }
        payload.update(extra)
        return payload

    # --------------------------------------------------------------
    # Program execution. NEWSTT in GWMAIN.ASM is the conceptual peer.
    # --------------------------------------------------------------
    def run(self, position: tuple[int, int] | None = None) -> dict[str, Any]:
        self.collect_data()
        if position is None:
            self.state.data_pointer = 0
            self.state.gosub_stack.clear()
            self.state.for_stack.clear()
            self.state.while_stack.clear()
            position = (0, 0)

        lines = self.sorted_lines()
        li, si = position
        self.state.running = True
        steps = 0

        while li < len(lines):
            if steps >= self.max_steps:
                self.state.running = False
                raise BasicError("Execution step limit exceeded", lines[li])
            steps += 1
            line_no = lines[li]
            statements = split_statements(self.state.program[line_no])
            if si >= len(statements):
                li += 1; si = 0; continue

            self.state.pc_line_index, self.state.pc_statement_index = li, si
            stmt = statements[si].strip()
            next_pos = self.advance_position(li, si)
            try:
                control = self.execute_statement(stmt, li, si, line_no=line_no)
            except InputRequired as req:
                self.state.pending_input = req.variables
                self.state.pending_prompt = req.prompt
                self.state.pending_resume = next_pos
                self.state.running = True
                return self.result("waiting_input", prompt=req.prompt)
            except BasicError as exc:
                self.state.running = False
                if exc.line is None: exc.line = line_no
                raise

            if self.state.trace:
                self.state.emit(f"[{line_no}]", newline=False)
            if control and control.stop:
                self.state.running = False
                return self.result("stopped")
            if control and control.jump is not None:
                li, si = self.normalize_position(*control.jump)
            else:
                li, si = next_pos

        self.state.running = False
        return self.result("ended")

    def feed_input(self, text: str) -> dict[str, Any]:
        variables = self.state.pending_input or []
        values = parse_csv_values(text)
        if len(values) != len(variables):
            self.state.emit("?Redo from start")
            return self.result("waiting_input", prompt=self.state.pending_prompt)
        for name, raw in zip(variables, values):
            self.assign_input(name, raw)
        resume = self.state.pending_resume
        self.state.pending_input = None
        self.state.pending_resume = None
        if self.state.running and resume is not None:
            return self.run(position=resume)
        return self.result("ok")

    def sorted_lines(self) -> list[int]:
        return sorted(self.state.program)

    def line_index(self, line_number: int) -> int:
        lines = self.sorted_lines()
        try: return lines.index(int(line_number))
        except ValueError: raise BasicError("Undefined line number")

    def advance_position(self, li: int, si: int) -> tuple[int, int]:
        lines=self.sorted_lines()
        if li < 0: return (0,0)
        stmts=split_statements(self.state.program[lines[li]])
        return (li, si+1) if si+1 < len(stmts) else (li+1, 0)

    def normalize_position(self, li: int, si: int) -> tuple[int, int]:
        lines=self.sorted_lines()
        while li < len(lines):
            stmts=split_statements(self.state.program[lines[li]])
            if si < len(stmts): return li,si
            li += 1; si=0
        return li,si

    # --------------------------------------------------------------
    # Statement dispatcher. STMDSP/OPTAB jump tables become this method.
    # --------------------------------------------------------------
    def execute_statement(self, stmt: str, li: int, si: int,
                          line_no: int | None = None, direct: bool = False) -> Control | None:
        stmt=stmt.strip()
        if not stmt: return None
        if stmt.startswith("'"): return None
        if stmt.startswith('?'): stmt='PRINT '+stmt[1:].lstrip()
        upper=stmt.upper()
        if upper.startswith('REM') and (len(stmt)==3 or stmt[3].isspace()): return None
        if upper.startswith('ELSE '): stmt=stmt[5:].lstrip(); upper=stmt.upper()

        # Direct/program management commands: GWLIST.ASM + BIMISC.ASM.
        if upper == 'RUN' or upper.startswith('RUN '):
            target=upper[3:].strip()
            if target and target.isdigit(): return Control((self.line_index(int(target)),0))
            if direct: return _ResultControl(self.run())
            return Control((0,0))
        if upper == 'LIST' or upper.startswith('LIST '): self.cmd_list(stmt[4:].strip()); return None
        if upper == 'LLIST' or upper.startswith('LLIST '): self.cmd_list(stmt[5:].strip(), printer=True); return None
        if upper == 'NEW': self.state.reset_runtime(preserve_program=False); return None
        if upper == 'CLEAR': self.state.reset_runtime(preserve_program=True); return None
        if upper.startswith('DELETE'): self.cmd_delete(stmt[6:].strip()); return None
        if upper.startswith('AUTO') or upper.startswith('RENUM') or upper.startswith('EDIT'):
            raise BasicError('Command intentionally not interactive in web port')

        # Core execution: GWMAIN.ASM.
        if kw(upper,'PRINT'): self.cmd_print(stmt[5:].lstrip()); return None
        if kw(upper,'LPRINT'): self.cmd_print(stmt[6:].lstrip(), printer=True); return None
        if kw(upper,'WRITE'): self.cmd_write(stmt[5:].lstrip()); return None
        if kw(upper,'LET'): self.cmd_assignment(stmt[3:].lstrip()); return None
        if kw(upper,'INPUT'): self.cmd_input(stmt[5:].lstrip()); return None
        if upper.startswith('LINE INPUT'):
            self.cmd_line_input(stmt[10:].lstrip()); return None
        if kw(upper,'GOTO'): return Control((self.line_index(int(self.eval_int(stmt[4:]))),0))
        if kw(upper,'GOSUB'):
            if li < 0: raise BasicError('Illegal direct')
            self.state.gosub_stack.append(self.advance_position(li,si))
            return Control((self.line_index(int(self.eval_int(stmt[5:]))),0))
        if upper == 'RETURN':
            if not self.state.gosub_stack: raise BasicError('RETURN without GOSUB')
            return Control(self.state.gosub_stack.pop())
        if kw(upper,'IF'): return self.cmd_if(stmt[2:].lstrip(), li, si, line_no)
        if kw(upper,'ON'): return self.cmd_on(stmt[2:].lstrip(), li, si)
        if kw(upper,'FOR'):
            target=self.cmd_for(stmt[3:].lstrip(), li, si)
            return Control(target) if target else None
        if kw(upper,'NEXT'):
            variables=[v.strip() for v in split_top_level(stmt[4:].strip(), ',') if v.strip()]
            if not variables: variables=[None]
            for variable in variables:
                target=next86.next_for(self.state, variable)
                if target: return Control(target)
            return None
        if kw(upper,'WHILE'): return self.cmd_while(stmt[5:].lstrip(), li, si)
        if upper == 'WEND': return self.cmd_wend(li,si)
        if kw(upper,'DATA'): return None
        if kw(upper,'READ'): self.cmd_read(stmt[4:].lstrip()); return None
        if kw(upper,'RESTORE'): self.state.data_pointer=0; return None
        if kw(upper,'DIM'): self.cmd_dim(stmt[3:].lstrip()); return None
        if kw(upper,'ERASE'): self.cmd_erase(stmt[5:].lstrip()); return None
        if kw(upper,'SWAP'): self.cmd_swap(stmt[4:].lstrip()); return None
        if upper in ('STOP','END','SYSTEM'): return Control(stop=True)
        if upper == 'CONT': raise BasicError('CONT requires suspended execution context')
        if upper == 'TRON': self.state.trace=True; return None
        if upper == 'TROFF': self.state.trace=False; return None
        if kw(upper,'RANDOMIZE'):
            arg=stmt[9:].strip(); random.seed(self.expr.evaluate(arg) if arg else None); return None
        if upper.startswith('DEF SEG'):
            self.cmd_def_seg(stmt[7:].strip()); return None
        if kw(upper,'POKE'): self.cmd_poke(stmt[4:].lstrip()); return None
        if upper.startswith('OUT '): self.cmd_out(stmt[3:].lstrip()); return None
        if upper.startswith('DEFINT') or upper.startswith('DEFSNG') or upper.startswith('DEFDBL') or upper.startswith('DEFSTR'):
            # Type-default tables from GWMAIN are not needed when values carry Python types.
            return None
        if upper.startswith('OPTION BASE'): return None
        if upper.startswith('DEF FN'): raise BasicError('DEF FN not yet implemented')

        # File/device statements: GIO86/DSKCOM/GIODSK.
        if kw(upper,'OPEN'): self.cmd_open(stmt[4:].lstrip()); return None
        if kw(upper,'CLOSE'): self.cmd_close(stmt[5:].lstrip()); return None
        if kw(upper,'KILL'): self.cmd_kill(stmt[4:].lstrip()); return None
        if kw(upper,'NAME'): self.cmd_name(stmt[4:].lstrip()); return None
        if upper.startswith('MOUNT CAS1'):
            self.cmd_mount_cassette(stmt[len('MOUNT CAS1'):].lstrip()); return None
        if kw(upper,'BSAVE'): self.cmd_bsave(stmt[5:].lstrip()); return None
        if kw(upper,'BLOAD'): self.cmd_bload(stmt[5:].lstrip()); return None
        if kw(upper,'SAVE'): self.cmd_save(stmt[4:].lstrip()); return None
        if kw(upper,'LOAD'): self.cmd_load(stmt[4:].lstrip(), merge=False); return None
        if kw(upper,'MERGE'): self.cmd_load(stmt[5:].lstrip(), merge=True); return None
        if kw(upper,'COMMON'): self.cmd_common(stmt[6:].lstrip()); return None
        if kw(upper,'CHAIN'): self.cmd_chain(stmt[5:].lstrip()); return Control((0,0))
        if upper == 'FILES': self.cmd_files(); return None

        # Screen/graphics: GWSTS/GENGRP/ADVGRP/SCNDRV.
        if upper == 'CLS' or upper.startswith('CLS '): self.state.screen.clear(); return None
        if kw(upper,'WIDTH'): self.cmd_width(stmt[5:].lstrip()); return None
        if kw(upper,'LOCATE'): self.cmd_locate(stmt[6:].lstrip()); return None
        if kw(upper,'COLOR') or kw(upper,'SCREEN'): return None
        if kw(upper,'PSET'): self.cmd_pset(stmt[4:].lstrip(), preset=False); return None
        if kw(upper,'PRESET'): self.cmd_pset(stmt[6:].lstrip(), preset=True); return None
        if kw(upper,'LINE'): self.cmd_graphics_line(stmt[4:].lstrip()); return None
        if kw(upper,'CIRCLE'): self.cmd_circle(stmt[6:].lstrip()); return None
        if kw(upper,'PAINT'): self.cmd_paint(stmt[5:].lstrip()); return None
        if kw(upper,'DRAW') or kw(upper,'PLAY') or kw(upper,'SOUND') or upper=='BEEP':
            self.state.graphics_commands.append({'op': upper.split()[0], 'source': stmt}); return None

        # CALL86 cannot safely call a raw 8086 address. Named Python call registry only.
        if kw(upper,'CALL'): self.cmd_call(stmt[4:].lstrip()); return None

        # Assignment without LET.
        if find_assignment(stmt) is not None:
            self.cmd_assignment(stmt); return None

        raise BasicError(f"Syntax error: {stmt}")

    # -------------------------- statements --------------------------
    def cmd_assignment(self, text: str) -> None:
        pos=find_assignment(text)
        if pos is None: raise BasicError('Syntax error')
        lhs=text[:pos].strip(); rhs=text[pos+1:].strip()
        value=self.expr.evaluate(rhs)
        m=re.match(r'^([A-Za-z][\w.]*[$%!#&]?)\s*\((.*)\)$',lhs)
        if m:
            indices=[self.expr.evaluate(x) for x in split_top_level(m.group(2), ',')]
            biptrg.array_set(self.state,m.group(1),indices,value)
        else:
            if not re.match(r'^[A-Za-z][\w.]*[$%!#&]?$',lhs): raise BasicError('Syntax error')
            self.state.set_var(lhs,value)

    def cmd_print(self, text: str, printer: bool=False) -> None:
        text=text.strip()
        if text.upper().startswith('USING '):
            self.cmd_print_using(text[6:].lstrip(), printer=printer)
            return
        if text.startswith('#'):
            m=re.match(r'#\s*(\d+)\s*,?\s*(.*)$',text,re.S)
            if not m: raise BasicError('Bad file number')
            n=int(m.group(1)); rest=m.group(2); rendered=self.render_print(rest)
            fh=self.get_file(n); fh.handle.write(rendered + ('' if rest.rstrip().endswith(';') else '\n')); fh.handle.flush(); return
        rendered,newline=self.render_print(text, return_newline=True)
        if printer:
            self.state.printer_output.append(rendered + ('\n' if newline else ''))
        else:
            self.state.emit(rendered,newline=newline)


    def cmd_print_using(self, text: str, printer: bool=False) -> None:
        # BIPRTU.ASM expects: PRINT USING <format>; <value-list>
        parts=split_print_items(text)
        if not parts:
            raise BasicError('Syntax error')
        # Find the first top-level semicolon or comma separating format from values.
        in_string=False; depth=0; sep_at=None
        for i,c in enumerate(text):
            if c=='"': in_string=not in_string
            elif not in_string:
                if c=='(': depth+=1
                elif c==')': depth=max(0,depth-1)
                elif c in ';,' and depth==0:
                    sep_at=i; break
        if sep_at is None:
            raise BasicError('Syntax error')
        pattern=self.expr.evaluate(text[:sep_at].strip())
        values_text=text[sep_at+1:].strip()
        values=[self.expr.evaluate(x) for x in split_top_level(values_text, ',')] if values_text else []
        rendered=biprtu.format_using(str(pattern),values)
        if printer:
            self.state.printer_output.append(rendered+'\n')
        else:
            self.state.emit(rendered)

    def render_print(self,text: str,return_newline=False):
        if not text: return ('',True) if return_newline else ''
        parts=split_print_items(text); out=[]
        newline=not text.rstrip().endswith((';', ','))
        for expr,sep in parts:
            if expr.strip():
                value=self.expr.evaluate(expr)
                if isinstance(value,str): out.append(value)
                else: out.append(bistrs.format_number(value))
            if sep==',': out.append(' ' * (14 - (sum(map(len,out)) % 14)))
            elif sep==';': pass
        rendered=''.join(out)
        return (rendered,newline) if return_newline else rendered

    def cmd_write(self,text: str) -> None:
        target_file=None
        if text.strip().startswith('#'):
            m=re.match(r'#\s*(\d+)\s*,\s*(.*)$',text,re.S)
            if not m: raise BasicError('Bad file number')
            target_file=int(m.group(1)); text=m.group(2)
        vals=[self.expr.evaluate(x) for x in split_top_level(text, ',')] if text.strip() else []
        buf=io.StringIO(); csv.writer(buf,lineterminator='').writerow(vals); line=buf.getvalue()
        if target_file is None: self.state.emit(line)
        else:
            fh=self.get_file(target_file); fh.handle.write(line+'\n'); fh.handle.flush()

    def cmd_input(self,text: str) -> None:
        text=text.strip()
        if text.startswith('#'):
            m=re.match(r'#\s*(\d+)\s*,\s*(.*)$',text,re.S)
            if not m: raise BasicError('Bad file number')
            fh=self.get_file(int(m.group(1))); line=fh.handle.readline()
            if line=='': raise BasicError('Input past end')
            vals=parse_csv_values(line.rstrip('\r\n')); vars=[v.strip() for v in split_top_level(m.group(2), ',')]
            if len(vals)<len(vars): raise BasicError('Input past end')
            for name,val in zip(vars,vals): self.assign_input(name,val)
            return
        prompt='? '
        if text.startswith('"'):
            end=find_string_end(text,0)
            prompt=text[1:end].replace('""','"')
            rest=text[end+1:].lstrip()
            if rest.startswith(';') or rest.startswith(','): rest=rest[1:].lstrip()
            text=rest
        variables=[v.strip() for v in split_top_level(text, ',') if v.strip()]
        if not variables: raise BasicError('Syntax error')
        raise InputRequired(prompt,variables)

    def cmd_line_input(self,text: str) -> None:
        if text.startswith('#'):
            m=re.match(r'#\s*(\d+)\s*,\s*([A-Za-z][\w.]*\$)$',text,re.I)
            if not m: raise BasicError('Syntax error')
            line=self.get_file(int(m.group(1))).handle.readline()
            if line=='': raise BasicError('Input past end')
            self.state.set_var(m.group(2),line.rstrip('\r\n')); return
        prompt='? '
        m=re.match(r'(?:("(?:[^"]|"")*")\s*[;,]\s*)?([A-Za-z][\w.]*\$)$',text,re.I)
        if not m: raise BasicError('Syntax error')
        if m.group(1): prompt=m.group(1)[1:-1].replace('""','"')
        raise InputRequired(prompt,[m.group(2)])

    def assign_input(self,name,raw):
        name=name.strip()
        if name.endswith('$'): self.state.set_var(name,raw)
        else:
            try: self.state.set_var(name,float(raw) if any(c in raw.upper() for c in '.E') else int(raw))
            except ValueError: raise BasicError('Redo from start')

    def cmd_if(self,text,li,si,line_no):
        m=re.search(r'\bTHEN\b',text,re.I)
        if not m: raise BasicError('Syntax error')
        cond_text=text[:m.start()].strip(); tail=text[m.end():].strip()
        then_part,else_part=split_else(tail)
        chosen=then_part if self.truth(self.expr.evaluate(cond_text)) else else_part
        if chosen is None or not chosen.strip(): return None
        chosen=chosen.strip()
        if chosen.isdigit(): return Control((self.line_index(int(chosen)),0))
        return self.execute_statement(chosen,li,si,line_no=line_no)

    def cmd_on(self,text,li,si):
        m=re.match(r'(.+?)\s+(GOTO|GOSUB)\s+(.+)$',text,re.I|re.S)
        if not m: raise BasicError('Syntax error')
        index=int(self.expr.evaluate(m.group(1)))
        targets=[x.strip() for x in split_top_level(m.group(3), ',')]
        if index<1 or index>len(targets): return None
        line=int(targets[index-1])
        if m.group(2).upper()=='GOSUB': self.state.gosub_stack.append(self.advance_position(li,si))
        return Control((self.line_index(line),0))

    def cmd_for(self,text,li,si):
        m=re.match(r'([A-Za-z][\w.]*[%!#&]?)\s*=\s*(.+?)\s+TO\s+(.+?)(?:\s+STEP\s+(.+))?$',text,re.I|re.S)
        if not m: raise BasicError('Syntax error')
        start=self.expr.evaluate(m.group(2)); limit=self.expr.evaluate(m.group(3)); step=self.expr.evaluate(m.group(4)) if m.group(4) else 1
        resume=self.advance_position(li,si)
        next86.begin_for(self.state,m.group(1),start,limit,step,*resume)
        if (float(step) >= 0 and float(start) > float(limit)) or (float(step) < 0 and float(start) < float(limit)):
            # Skip the loop body just as NEXT86/FNDFOR logic eventually would.
            self.state.for_stack.pop()
            return self.find_matching_next(li,si)
        return None


    def find_matching_next(self,li,si):
        depth=0
        for p,stmt in self.iter_positions_after(li,si):
            u=stmt.strip().upper()
            if kw(u,'FOR'): depth+=1
            elif kw(u,'NEXT'):
                if depth==0: return self.advance_position(*p)
                depth-=1
        raise BasicError('FOR without NEXT')

    def cmd_while(self,condition,li,si):
        value=self.expr.evaluate(condition)
        if self.truth(value): return None
        return Control(self.find_matching_wend(li,si))

    def cmd_wend(self,li,si):
        pos=self.find_matching_while(li,si)
        lines=self.sorted_lines(); stmt=split_statements(self.state.program[lines[pos[0]]])[pos[1]]
        condition=stmt.strip()[5:].strip()
        if self.truth(self.expr.evaluate(condition)): return Control(pos)
        return None

    def find_matching_wend(self,li,si):
        depth=0
        for p,stmt in self.iter_positions_after(li,si):
            u=stmt.strip().upper()
            if kw(u,'WHILE'): depth+=1
            elif u=='WEND':
                if depth==0: return self.advance_position(*p)
                depth-=1
        raise BasicError('WHILE without WEND')

    def find_matching_while(self,li,si):
        flat=list(self.iter_all_positions())
        current=flat.index(((li,si), split_statements(self.state.program[self.sorted_lines()[li]])[si]))
        depth=0
        for p,stmt in reversed(flat[:current]):
            u=stmt.strip().upper()
            if u=='WEND': depth+=1
            elif kw(u,'WHILE'):
                if depth==0: return p
                depth-=1
        raise BasicError('WEND without WHILE')

    def iter_all_positions(self):
        for li,line in enumerate(self.sorted_lines()):
            for si,stmt in enumerate(split_statements(self.state.program[line])):
                yield (li,si),stmt

    def iter_positions_after(self,li,si):
        found=False
        for p,stmt in self.iter_all_positions():
            if found: yield p,stmt
            if p==(li,si): found=True

    def cmd_read(self,text):
        for name in split_top_level(text, ','):
            if self.state.data_pointer>=len(self.state.data_values): raise BasicError('Out of DATA')
            value=self.state.data_values[self.state.data_pointer]; self.state.data_pointer+=1
            self.state.set_var(name.strip(),value)

    def collect_data(self):
        vals=[]
        for line in self.sorted_lines():
            for stmt in split_statements(self.state.program[line]):
                if kw(stmt.strip().upper(),'DATA'):
                    for raw in split_top_level(stmt.strip()[4:].lstrip(), ','):
                        raw=raw.strip()
                        if raw.startswith('"') and raw.endswith('"'): vals.append(raw[1:-1].replace('""','"'))
                        else:
                            try: vals.append(float(raw) if any(c in raw.upper() for c in '.E') else int(raw))
                            except ValueError: vals.append(raw)
        self.state.data_values=vals

    def cmd_dim(self,text):
        for spec in split_top_level(text, ','):
            m=re.match(r'^([A-Za-z][\w.]*[$%!#&]?)\s*\((.*)\)$',spec.strip())
            if not m: raise BasicError('Syntax error')
            bounds=[int(self.expr.evaluate(x)) for x in split_top_level(m.group(2), ',')]
            biptrg.dim_array(self.state,m.group(1),bounds)

    def cmd_erase(self,text):
        for name in split_top_level(text, ','): self.state.arrays.pop(self.state.normalize_var(name),None)

    def cmd_swap(self,text):
        parts=[x.strip() for x in split_top_level(text, ',')]
        if len(parts)!=2: raise BasicError('Syntax error')
        a,b=parts; va,vb=self.state.get_var(a),self.state.get_var(b); self.state.set_var(a,vb); self.state.set_var(b,va)

    def cmd_def_seg(self, text):
        """Port of DEF SEG/SAVSEG used by PEEK, POKE, BLOAD and BSAVE.

        ``DEF SEG=expr`` selects a 16-bit real-mode segment. A bare ``DEF SEG``
        restores the educational port's default segment 0.
        """
        text=text.strip()
        if not text:
            self.state.def_seg=0; return
        if not text.startswith('='):
            raise BasicError('Syntax error')
        value=int(self.expr.evaluate(text[1:].strip()))
        if value < -32768 or value > 65535:
            raise BasicError('Illegal function call')
        self.state.def_seg=value & 0xFFFF

    def cmd_poke(self,text):
        parts=split_top_level(text, ',')
        if len(parts)!=2: raise BasicError('Syntax error')
        offset=int(self.expr.evaluate(parts[0])); value=int(self.expr.evaluate(parts[1]))
        self.state.memory[self.state.linear_address(offset)]=value & 0xFF

    def cmd_out(self,text):
        parts=split_top_level(text, ',')
        if len(parts)!=2: raise BasicError('Syntax error')
        self.state.io_ports[int(self.expr.evaluate(parts[0]))]=int(self.expr.evaluate(parts[1])) & 0xFF

    # -------------------------- file I/O --------------------------
    def safe_path(self,name: str) -> Path:
        name=name.strip()
        if name.startswith('"') and name.endswith('"'): name=name[1:-1]
        p=(self.data_dir/name).resolve()
        if self.data_dir != p and self.data_dir not in p.parents: raise BasicError('Bad file name')
        return p

    def cmd_open(self,text):
        m=re.match(r'("(?:[^"]|"")*")\s+FOR\s+(INPUT|OUTPUT|APPEND|RANDOM|BINARY)\s+AS\s+#?(\d+)',text,re.I)
        if not m:
            m2=re.match(r'"([IOA])"\s*,\s*#?(\d+)\s*,\s*("(?:[^"]|"")*")',text,re.I)
            if not m2: raise BasicError('Syntax error')
            mode={'I':'INPUT','O':'OUTPUT','A':'APPEND'}[m2.group(1).upper()]; num=int(m2.group(2)); filename=m2.group(3)
        else:
            filename=m.group(1); mode=m.group(2).upper(); num=int(m.group(3))
        path=self.safe_path(filename); path.parent.mkdir(parents=True,exist_ok=True)
        py_mode={'INPUT':'r','OUTPUT':'w','APPEND':'a','RANDOM':'r+','BINARY':'r+b'}[mode]
        if mode=='RANDOM' and not path.exists(): path.touch()
        try:
            if 'b' in py_mode:
                handle=open(path,py_mode)
            else:
                handle=open(path,py_mode,encoding='utf-8',newline='')
        except OSError as e: raise BasicError(str(e))
        self.state.file_handles[num]=FileHandle(num,path,mode,handle)

    def get_file(self,n):
        if n not in self.state.file_handles: raise BasicError('Bad file number')
        return self.state.file_handles[n]

    def cmd_close(self,text):
        nums=[] if not text.strip() else [int(x.strip().lstrip('#')) for x in split_top_level(text, ',')]
        if not nums: nums=list(self.state.file_handles)
        for n in nums:
            fh=self.state.file_handles.pop(n,None)
            if fh: fh.handle.close()

    def cmd_kill(self,text):
        try: self.safe_path(text).unlink()
        except FileNotFoundError: raise BasicError('File not found')

    def cmd_name(self,text):
        m=re.match(r'(.+?)\s+AS\s+(.+)$',text,re.I)
        if not m: raise BasicError('Syntax error')
        self.safe_path(m.group(1)).rename(self.safe_path(m.group(2)))

    def _filename_and_options(self, text):
        parts=[p.strip() for p in split_top_level(text, ',')]
        if not parts or not parts[0]: raise BasicError('Bad file name')
        try: filename=self.expr.evaluate(parts[0])
        except BasicError: raise
        if not isinstance(filename,str): raise BasicError('Type mismatch')
        return filename, [p.strip().upper() for p in parts[1:] if p.strip()]

    @staticmethod
    def _cassette_name(filename: str) -> str | None:
        if filename.upper().startswith('CAS1:'):
            return filename[5:][:8]
        return None

    def mount_cassette(self, path: str | os.PathLike) -> Path:
        path=Path(path).resolve()
        if path.suffix.lower() not in ('.wav','.mp3'):
            raise BasicError('Cassette image must be WAV or MP3')
        self.cassette_path=path
        return path

    def cmd_mount_cassette(self,text):
        # Extension command for the web port: MOUNT CAS1,"capture.wav"
        text=text.lstrip(' ,')
        if not text: raise BasicError('Syntax error')
        filename,_=self._filename_and_options(text)
        self.mount_cassette(self.safe_path(filename))
        self.state.emit(f'CAS1: mounted {self.cassette_path.name}')

    def _program_payload(self, option: str) -> tuple[int, bytes]:
        if option == 'A':
            return cassette.TYPE_ASCII, legacy_basic.ascii_program_bytes(self.state.program)
        payload=legacy_basic.tokenize_program(self.state.program)
        if option == 'P':
            return cassette.TYPE_PROTECTED, legacy_basic.protect_payload(payload)
        if option:
            raise BasicError('Syntax error')
        return cassette.TYPE_TOKENISED, payload

    def cmd_save(self,text):
        filename,options=self._filename_and_options(text)
        option=options[0] if options else ''
        file_type,payload=self._program_payload(option)
        tape_name=self._cassette_name(filename)
        if tape_name is not None:
            try:
                cassette.append_file(self.cassette_path, cassette.TapeFile(tape_name,file_type,payload))
            except cassette.CassetteError as exc:
                raise BasicError(str(exc)) from exc
            self.state.emit(f'{tape_name}.{cassette.TapeFile(tape_name,file_type,b"").type_letter}')
            return

        path=self.safe_path(filename); path.parent.mkdir(parents=True,exist_ok=True)
        if file_type == cassette.TYPE_ASCII:
            path.write_bytes(payload)
        elif file_type == cassette.TYPE_PROTECTED:
            # GIODSK uses FE as the protected disk-file marker.
            path.write_bytes(b'\xFE'+payload+b'\x1A')
        else:
            # DSKCOM/GIODSK tokenised disk program marker.
            path.write_bytes(b'\xFF'+payload)

    def _decode_program_payload(self,file_type: int,payload: bytes) -> dict[int,str]:
        if file_type == cassette.TYPE_ASCII:
            return legacy_basic.parse_ascii_program(payload)
        if file_type in (cassette.TYPE_PROTECTED,0x20):
            payload=legacy_basic.unprotect_payload(payload)
        return legacy_basic.detokenize_program(payload)

    def cmd_load(self,text,merge=False):
        filename,options=self._filename_and_options(text)
        tape_name=self._cassette_name(filename)
        if tape_name is not None:
            try:
                tf=cassette.find_file(self.cassette_path,tape_name,cassette.PROGRAM_TYPES)
            except cassette.CassetteError as exc:
                raise BasicError(str(exc)) from exc
            if not tf.crc_ok: raise BasicError('Device I/O error')
            if merge and tf.file_type != cassette.TYPE_ASCII:
                raise BasicError('Bad file mode')
            program=self._decode_program_payload(tf.file_type,tf.payload)
            self.state.emit(f'{tf.name}.{tf.type_letter}')
        else:
            path=self.safe_path(filename)
            if not path.exists(): raise BasicError('File not found')
            raw=path.read_bytes()
            if raw[:1] == b'\xFF':
                if merge: raise BasicError('Bad file mode')
                program=legacy_basic.detokenize_program(raw[1:])
            elif raw[:1] == b'\xFE':
                if merge: raise BasicError('Bad file mode')
                enc=raw[1:-1] if raw.endswith(b'\x1A') else raw[1:]
                program=legacy_basic.detokenize_program(legacy_basic.unprotect_payload(enc))
            else:
                program=legacy_basic.parse_ascii_program(raw)
        if not merge: self.state.program.clear()
        self.state.program.update(program)
        # LOAD filename,R exists historically. In this web port execution remains an
        # explicit RUN so HTTP command/result boundaries stay deterministic.

    def cmd_bsave(self,text):
        parts=[p.strip() for p in split_top_level(text, ',')]
        if len(parts)!=3: raise BasicError('Syntax error')
        filename=self.expr.evaluate(parts[0])
        if not isinstance(filename,str): raise BasicError('Type mismatch')
        offset_raw=int(self.expr.evaluate(parts[1])); length_raw=int(self.expr.evaluate(parts[2]))
        if not -32768 <= offset_raw <= 0xFFFF or not -32768 <= length_raw <= 0xFFFF:
            raise BasicError('Overflow')
        offset=offset_raw & 0xFFFF; length=length_raw & 0xFFFF
        if length == 0: raise BasicError('Illegal function call')
        payload=bytes(self.state.memory.get(self.state.linear_address(offset+i),0) for i in range(length))
        tape_name=self._cassette_name(filename)
        if tape_name is not None:
            try:
                cassette.append_file(self.cassette_path,cassette.TapeFile(
                    tape_name,cassette.TYPE_MEMORY,payload,self.state.def_seg,offset))
            except cassette.CassetteError as exc:
                raise BasicError(str(exc)) from exc
            self.state.emit(f'{tape_name}.M'); return
        # GIO86 disk BSAVE header: FD, segment, offset, length, payload.
        path=self.safe_path(filename); path.parent.mkdir(parents=True,exist_ok=True)
        header=b'\xFD'+self.state.def_seg.to_bytes(2,'little')+offset.to_bytes(2,'little')+length.to_bytes(2,'little')
        path.write_bytes(header+payload)

    def cmd_bload(self,text):
        parts=[p.strip() for p in split_top_level(text, ',')]
        if not 1 <= len(parts) <= 2: raise BasicError('Syntax error')
        filename=self.expr.evaluate(parts[0])
        if not isinstance(filename,str): raise BasicError('Type mismatch')
        explicit_offset=int(self.expr.evaluate(parts[1])) if len(parts)==2 and parts[1] else None
        if explicit_offset is not None:
            if not -32768 <= explicit_offset <= 0xFFFF: raise BasicError('Overflow')
            explicit_offset &= 0xFFFF
        tape_name=self._cassette_name(filename)
        if tape_name is not None:
            try: tf=cassette.find_file(self.cassette_path,tape_name,{cassette.TYPE_MEMORY})
            except cassette.CassetteError as exc: raise BasicError(str(exc)) from exc
            if not tf.crc_ok: raise BasicError('Device I/O error')
            payload=tf.payload
            segment=self.state.def_seg if explicit_offset is not None else tf.segment
            offset=explicit_offset if explicit_offset is not None else tf.offset
            self.state.emit(f'{tf.name}.M')
        else:
            path=self.safe_path(filename)
            if not path.exists(): raise BasicError('File not found')
            raw=path.read_bytes()
            if len(raw)<7 or raw[0] != 0xFD: raise BasicError('Bad file mode')
            file_segment=int.from_bytes(raw[1:3],'little')
            file_offset=int.from_bytes(raw[3:5],'little')
            length=int.from_bytes(raw[5:7],'little')
            payload=raw[7:7+length]
            if len(payload) < length: raise BasicError('Input past end')
            segment=self.state.def_seg if explicit_offset is not None else file_segment
            offset=explicit_offset if explicit_offset is not None else file_offset
        for i,value in enumerate(payload):
            self.state.memory[self.state.linear_address(offset+i,segment)]=value


    def cmd_common(self,text):
        for spec in split_top_level(text, ','):
            name=spec.strip()
            if name:
                # COMMON can describe arrays too. Store the canonical base name.
                name=name.split('(',1)[0].strip().upper()
                self.state.common_variables.add(name)

    def cmd_chain(self,text):
        # Preserve scalar variables declared by COMMON, mirroring FIVEO.ASM at
        # a high level. Array COMMON semantics are intentionally not byte exact.
        keep={k:v for k,v in self.state.variables.items() if k in self.state.common_variables}
        common=set(self.state.common_variables)
        self.cmd_load(text,merge=False)
        self.state.variables=keep
        self.state.common_variables=common

    def cmd_files(self):
        for p in sorted(self.data_dir.iterdir()):
            if p.is_file(): self.state.emit(p.name)

    # -------------------------- list/program editing --------------------------
    def cmd_list(self,arg,printer=False):
        wanted=self.select_line_range(arg)
        target=[]
        for n in wanted: target.append(f"{n} {self.state.program[n]}")
        text='\n'.join(target)
        if printer: self.state.printer_output.append(text+'\n')
        else: self.state.emit(text)

    def select_line_range(self,arg):
        lines=self.sorted_lines()
        if not arg: return lines
        arg=arg.strip()
        if '-' in arg:
            a,b=arg.split('-',1); lo=int(a) if a.strip() else -math.inf; hi=int(b) if b.strip() else math.inf
            return [n for n in lines if lo<=n<=hi]
        n=int(arg); return [n] if n in self.state.program else []

    def cmd_delete(self,arg):
        if not arg: raise BasicError('Illegal function call')
        for n in self.select_line_range(arg): self.state.program.pop(n,None)

    # -------------------------- screen/graphics --------------------------
    def cmd_width(self,text):
        vals=[x.strip() for x in split_top_level(text, ',')]
        if vals and vals[0]: self.state.screen.width=int(self.expr.evaluate(vals[0]))
        if len(vals)>1 and vals[1]: self.state.screen.height=int(self.expr.evaluate(vals[1]))

    def cmd_locate(self,text):
        vals=split_top_level(text, ',')
        if vals and vals[0].strip(): self.state.screen.cursor_row=int(self.expr.evaluate(vals[0]))
        if len(vals)>1 and vals[1].strip(): self.state.screen.cursor_col=int(self.expr.evaluate(vals[1]))

    def parse_point(self,text):
        m=re.search(r'\(([^,]+),([^\)]+)\)',text)
        if not m: raise BasicError('Syntax error')
        return float(self.expr.evaluate(m.group(1))),float(self.expr.evaluate(m.group(2))),m.end()

    def cmd_pset(self,text,preset=False):
        x,y,end=self.parse_point(text); rest=text[end:].lstrip(' ,'); color=self.expr.evaluate(rest) if rest else (0 if preset else 1)
        self.state.graphics_commands.append({'op':'PRESET' if preset else 'PSET','x':x,'y':y,'color':color})

    def cmd_graphics_line(self,text):
        pts=re.findall(r'\(([^,]+),([^\)]+)\)',text)
        if not pts: raise BasicError('Syntax error')
        coords=[(float(self.expr.evaluate(a)),float(self.expr.evaluate(b))) for a,b in pts[:2]]
        color=None
        tail=text[text.rfind(')')+1:].lstrip(' ,')
        if tail: color=self.expr.evaluate(split_top_level(tail, ',')[0])
        self.state.graphics_commands.append({'op':'LINE','points':coords,'color':color})

    def cmd_circle(self,text):
        x,y,end=self.parse_point(text); rest=text[end:].lstrip(' ,'); args=split_top_level(rest, ',')
        if not args or not args[0].strip(): raise BasicError('Syntax error')
        radius=float(self.expr.evaluate(args[0])); color=self.expr.evaluate(args[1]) if len(args)>1 and args[1].strip() else 1
        self.state.graphics_commands.append({'op':'CIRCLE','x':x,'y':y,'radius':radius,'color':color})

    def cmd_paint(self,text):
        x,y,end=self.parse_point(text); rest=text[end:].lstrip(' ,'); color=self.expr.evaluate(split_top_level(rest, ',')[0]) if rest else 1
        self.state.graphics_commands.append({'op':'PAINT','x':x,'y':y,'color':color})

    def cmd_call(self,text):
        m=re.match(r'([A-Za-z_]\w*)\s*(?:\((.*)\))?$',text,re.S)
        if not m: raise BasicError('Illegal function call')
        name=m.group(1).upper(); fn=self.state.call_registry.get(name)
        if fn is None: raise BasicError('Illegal function call')
        args=[] if m.group(2) is None else [self.expr.evaluate(x) for x in split_top_level(m.group(2), ',')]
        fn(self.state,*args)

    def eval_int(self,text): return int(self.expr.evaluate(text.strip()))
    @staticmethod
    def truth(value): return bool(value)


class _ResultControl(Control):
    """Internal marker only used by direct RUN; controller detects state output."""
    def __init__(self,result): super().__init__(); self.result=result


# -------------------------- lexical helpers --------------------------
def kw(upper: str, keyword: str) -> bool:
    return upper == keyword or upper.startswith(keyword+' ')


def split_statements(text: str) -> list[str]:
    return split_top_level(text, ':')


def split_top_level(text: str, delimiter: str) -> list[str]:
    out=[]; start=0; depth=0; in_string=False; i=0
    while i<len(text):
        c=text[i]
        if c=='"':
            if in_string and i+1<len(text) and text[i+1]=='"': i+=2; continue
            in_string=not in_string
        elif not in_string:
            if c=='(': depth+=1
            elif c==')': depth=max(0,depth-1)
            elif c==delimiter and depth==0:
                out.append(text[start:i]); start=i+1
        i+=1
    out.append(text[start:]); return out


def split_print_items(text: str):
    items=[]; start=0; depth=0; in_string=False; i=0
    while i<len(text):
        c=text[i]
        if c=='"':
            if in_string and i+1<len(text) and text[i+1]=='"': i+=2; continue
            in_string=not in_string
        elif not in_string:
            if c=='(': depth+=1
            elif c==')': depth=max(0,depth-1)
            elif c in ',;' and depth==0:
                items.append((text[start:i],c)); start=i+1
        i+=1
    items.append((text[start:],None)); return items


def find_assignment(text: str):
    in_string=False; depth=0
    for i,c in enumerate(text):
        if c=='"': in_string=not in_string
        elif not in_string:
            if c=='(': depth+=1
            elif c==')': depth=max(0,depth-1)
            elif c=='=' and depth==0:
                if i and text[i-1] in '<>': continue
                if i+1<len(text) and text[i+1]=='>': continue
                return i
    return None


def split_else(text: str):
    in_string=False; depth=0; upper=text.upper(); i=0
    while i<len(text):
        c=text[i]
        if c=='"': in_string=not in_string
        elif not in_string:
            if c=='(': depth+=1
            elif c==')': depth=max(0,depth-1)
            elif depth==0 and upper.startswith('ELSE',i) and (i==0 or text[i-1].isspace()) and (i+4==len(text) or text[i+4].isspace()):
                return text[:i].strip(),text[i+4:].strip()
        i+=1
    return text.strip(),None


def find_string_end(text,start):
    i=start+1
    while i<len(text):
        if text[i]=='"':
            if i+1<len(text) and text[i+1]=='"': i+=2; continue
            return i
        i+=1
    raise BasicError('Unterminated string')


def parse_csv_values(text: str) -> list[str]:
    try: return next(csv.reader([text],skipinitialspace=True))
    except Exception as e: raise BasicError('Redo from start') from e
