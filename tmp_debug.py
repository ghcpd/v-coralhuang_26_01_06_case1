import re

allow_thousands_separator = True
number_re = r"[0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?|\.[0-9]+" if allow_thousands_separator else r"[0-9]+(?:\.[0-9]+)?|\.[0-9]+"
pattern = re.compile(rf"^(?P<sign>[+-]?)(?P<number>{number_re})\s*(?P<unit>[A-Za-z]+)?$")

import inspect
from mini_humanize import parse_size

print('parse_size source (file=')
print(parse_size.__code__.co_filename)
print('---\n')
print('parse_size source:\n')
print(inspect.getsource(parse_size))

for s in ('12,34 kB', '1,234.5 kB'):
    m = pattern.match(s.strip())
    print('INPUT:', s)
    print('MATCH:', bool(m))
    if m:
        num_str = m.group('number')
        print('num_str:', repr(num_str))
        if ',' in num_str:
            int_part, _, frac_part = num_str.partition('.')
            groups = int_part.split(',')
            print('groups:', groups)
            print('len(groups[0]) > 3 ->', len(groups[0]) > 3)
            print('any(len(g) != 3 for g in groups[1:]) ->', any(len(g) != 3 for g in groups[1:]))
            if len(groups[0]) > 3 or any(len(g) != 3 for g in groups[1:]):
                print('would raise invalid thousands')
            else:
                print('would accept')
    try:
        print('parse_size ->', parse_size(s, allow_thousands_separator=True))
    except Exception as e:
        print('parse_size raised', type(e).__name__, e)
    print('---')
