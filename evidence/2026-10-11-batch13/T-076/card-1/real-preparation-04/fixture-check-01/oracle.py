import importlib.util, pathlib, sys
root = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("fixture_normalize", root / "src/normalize.py")
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
assert module.normalize([]) == {"entries": [], "total_minutes": 0}
assert module.normalize([{"name": " B ", "minutes": 30}, {"name": "A", "minutes": 61},
                         {"name": "B", "minutes": 45}, {"name": "中文", "minutes": 0}]) == {
    "entries": [{"name": "A", "minutes": 61}, {"name": "B", "minutes": 75}, {"name": "中文", "minutes": 0}],
    "total_minutes": 136}
for invalid in [True, False, -1, 1.5, "1", None]:
    try: module.normalize([{"name": "A", "minutes": invalid}])
    except ValueError as error: assert str(error) == "invalid_minutes"
    else: raise AssertionError("invalid minutes accepted")
for invalid in ["", "   ", None, 1]:
    try: module.normalize([{"name": invalid, "minutes": 0}])
    except ValueError as error: assert str(error) == "invalid_name"
    else: raise AssertionError("invalid name accepted")
print("independent single-file oracle PASS")
