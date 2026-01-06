from mini_humanize import parse_size

for s in ('1,234.5 kB', '12,34 kB'):
    try:
        print(s, '=>', parse_size(s, allow_thousands_separator=True))
    except Exception as e:
        print(s, 'ERROR:', type(e).__name__, e)
