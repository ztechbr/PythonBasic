"""Port of GIOTBL.ASM device-name and dispatch tables.

8086 tables contain near pointers. Python uses symbolic adapter names.
"""
DEVICE_TABLE = {
    'CONS': 'console',
    'SCRN': 'screen',
    'KYBD': 'keyboard',
    'LPT1': 'printer',
    'CAS1': 'cassette',
    'COM1': 'communications',
    'DSK': 'disk',
}
