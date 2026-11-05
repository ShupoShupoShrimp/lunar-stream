import pygit2
import re
import sys

repo = pygit2.Repository(".")

ADAPTER_PATTERN = r"adapters/(\w+)_\w+\.py$"
NOTE_PATTERN = r"docs/evidence/(\w+)_protocol_note\.md$"

first_seen_adapters = {}
first_seen_notes = {}

if repo.is_empty:
    raise ValueError("Repository is empty")

commits = list(
    repo.walk(
        repo.head.target,
        pygit2.GIT_SORT_TOPOLOGICAL | pygit2.GIT_SORT_REVERSE,
    )
)

print(f"Analyzing {len(commits)} commits based on their chronology")

for index, commit in enumerate(commits):
    current_tree = commit.tree

    if commit.parents:
        parent_tree = commit.parents[0].tree
        diff = repo.diff(parent_tree, current_tree)
    else:
        diff = current_tree.diff_to_tree()

    for patch in diff:
        if patch.delta.status != pygit2.GIT_DELTA_ADDED:
            continue

        filepath = patch.delta.new_file.path

        if not filepath:
            continue

        note_match = re.search(NOTE_PATTERN, filepath)
        if note_match:
            component_name = note_match.group(1)
            if component_name not in first_seen_notes:
                first_seen_notes[component_name] = index

        adapter_match = re.search(ADAPTER_PATTERN, filepath)
        if adapter_match:
            adapter_type = adapter_match.group(1)
            filename = filepath.split("/")[-1]

            if adapter_type not in first_seen_adapters:
                first_seen_adapters[adapter_type] = (index, filename)

violations = 0

for adapter_type, (adapter_index, filename) in first_seen_adapters.items():
    note_index = first_seen_notes.get(adapter_type)

    if note_index is None:
        print(f"FAIL: {filename}")
        print("Missing protocol note before adapter introduction.\n")
        violations += 1

    elif adapter_index < note_index:
        print(f"FAIL: {filename}")
        print(
            f"Adapter introduced in commit index {adapter_index}, "
            f"but protocol note came later in commit index {note_index}.\n"
        )
        violations += 1

if violations:
    print(f"Found {violations} violation(s).")
    sys.exit(1)

print("All check rules passed successfully.")
sys.exit(0)
