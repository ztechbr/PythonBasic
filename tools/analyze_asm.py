#!/usr/bin/env python3
"""Static indexer for the original GW-BASIC ASM sources.

This utility is intentionally simple and reproducible. It extracts TITLE,
SUBTTL, PUBLIC, EXTRN and labels so students can navigate the original source
without needing an 8086 assembler.
"""
from __future__ import annotations
from pathlib import Path
import argparse, json, re


def analyze(path: Path) -> dict:
    text=path.read_text(errors='replace').replace('\x00','')
    lines=text.splitlines()
    def one(pattern):
        m=re.search(pattern,text,re.M|re.I)
        return m.group(1).strip() if m else ''
    publics=[]; externs=[]; subtitles=[]; labels=[]; includes=[]
    for no,line in enumerate(lines,1):
        m=re.match(r'^\s*PUBLIC\s+(.+)$',line,re.I)
        if m:
            publics += [{'name':x.strip(),'line':no} for x in m.group(1).split(';')[0].split(',') if x.strip()]
        m=re.match(r'^\s*EXTRN\s+(.+)$',line,re.I)
        if m:
            externs += [{'name':x.split(':')[0].strip(),'line':no} for x in m.group(1).split(';')[0].split(',') if x.strip()]
        m=re.match(r'^\s*SUBTTL\s+(.+)$',line,re.I)
        if m: subtitles.append({'text':m.group(1).strip(),'line':no})
        m=re.match(r'^\s*INCLUDE\s+(.+)$',line,re.I)
        if m: includes.append({'name':m.group(1).strip(),'line':no})
        m=re.match(r'^([A-Za-z_$?][\w$?@.]*)\s*:',line)
        if m: labels.append({'name':m.group(1),'line':no})
    return {
        'file':path.name,
        'title':one(r'^\s*TITLE\s+(.+)$'),
        'bytes':path.stat().st_size,
        'lines':len(lines),
        'includes':includes,
        'subtitles':subtitles,
        'public':publics,
        'extern':externs,
        'labels':labels,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('directory',nargs='?',default='reference/asm')
    ap.add_argument('-o','--output',default='docs/ASM_ROUTINE_INDEX.json')
    args=ap.parse_args()
    root=Path(args.directory)
    data=[analyze(p) for p in sorted(root.glob('*.ASM'))]
    Path(args.output).write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
    print(f'wrote {args.output}: {len(data)} ASM files')

if __name__=='__main__': main()
