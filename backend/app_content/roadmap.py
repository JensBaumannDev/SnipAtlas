"""Roadmap and folder tree of a project for a choice of building blocks."""

from dataclasses import dataclass, field

from django.db.models import Prefetch, QuerySet

from .models import (
    Concept,
    ErrorMessage,
    PathChange,
    RoadmapBlock,
    RoadmapPath,
    RoadmapPhase,
    RoadmapPhaseCondition,
    RoadmapStep,
    RoadmapStepCondition,
)

Origin = tuple[str, str]


# Paths
def parent_of(path: str) -> str:
    """Return the folder that contains a path, or an empty string for the project folder."""
    head = path.rstrip('/').rpartition('/')[0]
    return f'{head}/' if head else ''


def folders_above(path: str) -> list[str]:
    """Return all folders above a path, from the top down."""
    folders = []
    parent = parent_of(path)
    while parent:
        folders.insert(0, parent)
        parent = parent_of(parent)
    return folders


def name_of(path: str) -> str:
    """Return the last part of a path without a trailing slash."""
    return path.rstrip('/').rpartition('/')[2]


def sort_key(path: str) -> tuple[bool, str]:
    """Return the key that puts folders first, then files, by name ignoring case."""
    return (not path.endswith('/'), name_of(path).lower())


# Tree
@dataclass
class TreeEntry:
    """File or folder in the project tree with the step that created it."""

    tracked: bool = True
    explanation: str = ''
    origin: Origin | None = None


@dataclass
class TreeView:
    """Which folders are open and which changes to mark when the tree is shown."""

    open_folders: set[str] | None
    changes: dict[str, RoadmapPath] = field(default_factory=dict)
    with_origin: bool = False

    def is_open(self, path: str) -> bool:
        """Return whether a folder shows its children."""
        return self.open_folders is None or path in self.open_folders


class ProjectTree:
    """Files and folders of a project while the roadmap steps are applied one by one."""

    def __init__(self) -> None:
        """Start with an empty project folder."""
        self.entries: dict[str, TreeEntry] = {}

    def apply(self, paths: list[RoadmapPath], origin: Origin) -> list[dict]:
        """Apply the paths of a step and return the part of the tree they touch."""
        for record in paths:
            if record.change != PathChange.REMOVED:
                self.add(record, origin)
        changes = {record.path: record for record in paths if record.path in self.entries}
        if not changes:
            return []
        open_folders = {folder for path in changes for folder in folders_above(path)}
        snippet = self.children('', TreeView(open_folders, changes))
        for path, record in changes.items():
            if record.change == PathChange.REMOVED:
                self.remove(path)
        return snippet

    def add(self, record: RoadmapPath, origin: Origin) -> None:
        """Add a path with the folders above it, keeping the entry of a changed path."""
        for folder in folders_above(record.path):
            self.entries.setdefault(folder, TreeEntry())
        if record.change == PathChange.NEW or record.path not in self.entries:
            self.entries[record.path] = TreeEntry(record.tracked, record.explanation, origin)

    def remove(self, path: str) -> None:
        """Remove a path and, for a folder, everything inside it."""
        if path.endswith('/'):
            doomed = [key for key in self.entries if key.startswith(path)]
        else:
            doomed = [path] if path in self.entries else []
        for key in doomed:
            del self.entries[key]

    def nodes(self) -> list[dict]:
        """Return the whole tree with all folders open and where each path came from."""
        return self.children('', TreeView(None, with_origin=True))

    def children(self, folder: str, view: TreeView) -> list[dict]:
        """Return the nodes directly inside a folder in display order."""
        paths = sorted((path for path in self.entries if parent_of(path) == folder), key=sort_key)
        return [self.node(path, view) for path in paths]

    def node(self, path: str, view: TreeView) -> dict:
        """Return a single node with its open children."""
        entry, change = self.entries[path], view.changes.get(path)
        node = {'name': name_of(path), 'path': path, 'folder': path.endswith('/')}
        node['tracked'] = self.is_tracked(path)
        if change:
            node['change'] = change.change
        explanation = change.explanation if change else entry.explanation
        if explanation:
            node['explanation'] = explanation
        if view.with_origin and entry.origin:
            node['phase'], node['step'] = entry.origin
        if node['folder'] and view.is_open(path):
            node['children'] = self.children(path, view)
        return node

    def is_tracked(self, path: str) -> bool:
        """Return whether neither the path nor a folder above it is left out of Git."""
        return all(self.entries[key].tracked for key in [*folders_above(path), path])


# Roadmap
def phase_queryset() -> QuerySet[RoadmapPhase]:
    """Return the phases with everything the roadmap needs in a fixed number of queries."""
    steps = RoadmapStep.objects.prefetch_related(
        Prefetch('conditions', RoadmapStepCondition.objects.select_related('block')),
        'codes',
        'paths',
        Prefetch('errors', ErrorMessage.objects.select_related('topic')),
        Prefetch('concepts', Concept.objects.select_related('subtopic__topic')),
    )
    return RoadmapPhase.objects.prefetch_related(
        Prefetch('conditions', RoadmapPhaseCondition.objects.select_related('block')),
        Prefetch('steps', steps),
    )


@dataclass
class Roadmap:
    """Phases, steps and finished project tree for a choice of building blocks."""

    blocks: list[str]
    phases: list[RoadmapPhase]
    tree: ProjectTree

    @classmethod
    def for_blocks(cls, blocks: list[RoadmapBlock]) -> Roadmap:
        """Build the roadmap with the matching phases and steps and a tree part per step."""
        slugs = {block.slug for block in blocks}
        roadmap = cls([block.slug for block in blocks], [], ProjectTree())
        for phase in phase_queryset():
            steps = [step for step in phase.steps.all() if step.applies_to(slugs)]
            if steps and phase.applies_to(slugs):
                roadmap.add_phase(phase, steps)
        return roadmap

    def add_phase(self, phase: RoadmapPhase, steps: list[RoadmapStep]) -> None:
        """Add a phase with its steps and apply their paths to the tree."""
        for step in steps:
            step.tree = self.tree.apply(list(step.paths.all()), (phase.slug, step.slug))
        phase.plan_steps = steps
        self.phases.append(phase)
