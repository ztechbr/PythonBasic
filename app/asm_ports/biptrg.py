"""Port of BIPTRG.ASM, variable lookup and DIM support.

PTRGET in the original walks the packed VARTAB/ARYTAB memory structures and
returns an address. Python dictionaries replace the address arithmetic. DIM
still records dimensions and array accesses still use integer subscripts.
"""
from __future__ import annotations
from app.models.runtime import RuntimeState, BasicError


def dim_array(state: RuntimeState, name: str, bounds: list[int]) -> None:
    if any(int(b) < 0 for b in bounds):
        raise BasicError('Subscript out of range')
    state.arrays[state.normalize_var(name)] = {'__bounds__': tuple(int(b) for b in bounds)}


def array_get(state: RuntimeState, name: str, indices: list[int]):
    key=state.normalize_var(name); arr=state.arrays.get(key)
    if arr is None: raise BasicError('Subscript out of range')
    idx=tuple(int(i) for i in indices)
    _check(arr, idx)
    return arr.get(idx, state.default_value(key))


def array_set(state: RuntimeState, name: str, indices: list[int], value) -> None:
    key=state.normalize_var(name); arr=state.arrays.get(key)
    if arr is None:
        # GW-BASIC implicitly dimensions arrays to 10 when first used.
        arr={'__bounds__': tuple(10 for _ in indices)}; state.arrays[key]=arr
    idx=tuple(int(i) for i in indices); _check(arr, idx); arr[idx]=value


def _check(arr, idx):
    bounds=arr.get('__bounds__', ())
    if len(idx)!=len(bounds) or any(i < 0 or i > b for i,b in zip(idx,bounds)):
        raise BasicError('Subscript out of range')
