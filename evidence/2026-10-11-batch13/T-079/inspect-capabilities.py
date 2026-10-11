#!/usr/bin/env python3
"""Save installed Herdr help and schema; this probe does not contact the server."""
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

target = Path(sys.argv[1])
commands = []
for argv in (["herdr", "--version"], ["herdr", "pane", "--help"],
             ["herdr", "pane", "get", "--help"], ["herdr", "pane", "split", "--help"],
             ["herdr", "pane", "process-info", "--help"], ["herdr", "agent", "start", "--help"],
             ["herdr", "api", "schema", "--json"]):
    result = subprocess.run(argv, text=True, capture_output=True, check=True)
    if argv[-2:] == ["schema", "--json"]:
        schema = json.loads(result.stdout)
    else:
        commands.append(dict(argv=argv, stdout=result.stdout, stderr=result.stderr))
definitions = schema["schemas"]["success_response"]["$defs"]
base_url = "https://raw.githubusercontent.com/herdrdev/herdr/v0.9.3/"
sources = []
for path, start, end in (
    ("src/platform/mod.rs", "pub(crate) fn available_pane_shell_from_job(", "\nfn normalized_process_name("),
    ("src/platform/mod.rs", "pub(crate) fn is_pane_shell_process_name(", "\n#["),
    ("src/platform/macos.rs", "pub(crate) fn available_pane_shell(", "\n///"),
    ("src/app/api/panes.rs", "    pub(super) fn handle_pane_process_info(", "    pub(super) fn handle_pane_neighbor("),
):
    url = base_url + path
    with urllib.request.urlopen(url, timeout=30) as response:
        raw = response.read().decode("utf-8")
    snippet = raw[raw.index(start):]
    snippet = snippet[:snippet.index(end)]
    sources.append(dict(url=url, source=snippet, license="Apache-2.0 (Herdr upstream)"))
data = dict(commands=commands, protocol=schema["protocol"], schema_version=schema["schema_version"],
            definitions={name: definitions[name] for name in
                         ("PaneInfo", "PaneProcessInfo", "PaneProcessInfoProcess", "AgentInfo")},
            sources=sources)
with target.open("x", encoding="utf-8") as output:
    json.dump(data, output, ensure_ascii=False, indent=2)
    output.write("\n")
print(target)
