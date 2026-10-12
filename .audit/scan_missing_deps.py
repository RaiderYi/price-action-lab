# S0-02 helper: scan tests for unresolvable imports
import ast, os, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_files = {f[:-3] for f in os.listdir(os.path.join(ROOT, 'src')) if f.endswith('.py')}
stdlib = set(sys.stdlib_module_names)
missing_by_test = {}
total = 0
for f in sorted(os.listdir(os.path.join(ROOT, 'tests'))):
    if not f.endswith('.py'):
        continue
    total += 1
    path = os.path.join(ROOT, 'tests', f)
    try:
        tree = ast.parse(open(path, encoding='utf-8').read())
    except Exception as e:
        missing_by_test[f] = ['PARSE_ERROR:' + str(e)]
        continue
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                mods.add(a.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mods.add(node.module.split('.')[0])
    unresolved = set()
    for m in mods:
        if m in stdlib or m in src_files or m in ('tests', 'conftest'):
            continue
        if os.path.exists(os.path.join(ROOT, 'tests', m + '.py')) or os.path.exists(os.path.join(ROOT, m + '.py')):
            continue
        try:
            __import__(m)
        except Exception:
            unresolved.add(m)
    if unresolved:
        missing_by_test[f] = sorted(unresolved)
print(json.dumps(missing_by_test, indent=1))
print('TOTAL tests:', total)
print('WITH missing deps:', len(missing_by_test))
