# S0-04: Move tests that depend on missing external modules to tests/integration/
# Rule: a test file that imports a module not present in repo src/ or tests/ or
# stdlib/site-packages is an external-integration test and gets separated, NOT deleted.
import ast
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_files = {f[:-3] for f in os.listdir(os.path.join(ROOT, 'src')) if f.endswith('.py')}
stdlib = set(sys.stdlib_module_names)

# extra missing-file dependency (script not in repo)
SCRIPT_DEP = {"test_strict_shadow_output.py"}

moved, kept = [], []
for f in sorted(os.listdir(os.path.join(ROOT, 'tests'))):
    if not f.endswith('.py') or f == 'conftest.py':
        continue
    path = os.path.join(ROOT, 'tests', f)
    tree = ast.parse(open(path, encoding='utf-8').read())
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
        if m in stdlib or m in src_files or m in ('tests', 'conftest', 'src'):
            continue
        if os.path.exists(os.path.join(ROOT, 'tests', m + '.py')) or os.path.exists(os.path.join(ROOT, m + '.py')):
            continue
        if m in ('pandas', 'numpy', 'pytest', 'json', 'math', 'datetime', 'typing', 'pathlib', 'unittest.mock', 'unittest', 'io', 'os', 'sys', 're', 'copy', 'itertools', 'collections', 'dataclasses', 'enum', 'hashlib', 'random', 'warnings', 'tempfile'):
            continue
        try:
            __import__(m)
        except Exception:
            unresolved.add(m)
    if unresolved or f in SCRIPT_DEP:
        moved.append((f, sorted(unresolved)))
    else:
        kept.append(f)

dest = os.path.join(ROOT, 'tests', 'integration')
os.makedirs(dest, exist_ok=True)
for f, deps in moved:
    src_p = os.path.join(ROOT, 'tests', f)
    dst_p = os.path.join(dest, f)
    if os.path.exists(src_p):
        shutil.move(src_p, dst_p)
print(f"moved={len(moved)} kept={len(kept)}")
for f, deps in moved:
    print(f"  {f}: {','.join(deps) if deps else 'missing script file'}")
