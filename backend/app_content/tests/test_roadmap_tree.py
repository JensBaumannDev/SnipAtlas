from app_content.models import RoadmapPath
from app_content.roadmap import ProjectTree

ORIGIN = ('backend-anlegen', 'projekt')


def record(
    path: str, change: str = 'new', explanation: str = '', tracked: bool = True
) -> RoadmapPath:
    return RoadmapPath(path=path, change=change, explanation_de=explanation, tracked=tracked)


def node(path: str, **extra: object) -> dict:
    name = path.rstrip('/').rpartition('/')[2]
    return {'name': name, 'path': path, 'folder': path.endswith('/'), 'tracked': True} | extra


def tree_with(*paths: str) -> ProjectTree:
    tree = ProjectTree()
    tree.apply([record(path, explanation=f'Über {path}') for path in paths], ('vorher', 'start'))
    return tree


# Adding
def test_new_tree_is_empty() -> None:
    assert ProjectTree().nodes() == []


def test_new_file_in_project_folder_is_shown_as_new() -> None:
    snippet = ProjectTree().apply(
        [record('README.md', explanation='Beschreibt das Projekt.')], ORIGIN
    )
    assert snippet == [node('README.md', change='new', explanation='Beschreibt das Projekt.')]


def test_new_file_opens_its_folders_that_are_created_on_the_way() -> None:
    snippet = ProjectTree().apply([record('backend/core/settings.py')], ORIGIN)
    settings = node('backend/core/settings.py', change='new')
    core = node('backend/core/', children=[settings])
    assert snippet == [node('backend/', children=[core])]


def test_open_folder_shows_all_its_children_and_others_stay_closed() -> None:
    tree = tree_with('backend/manage.py', 'backend/core/settings.py', 'frontend/', 'README.md')
    snippet = tree.apply([record('backend/.env', explanation='Geheimnisse.')], ORIGIN)
    backend = [
        node('backend/core/'),
        node('backend/.env', change='new', explanation='Geheimnisse.'),
        node('backend/manage.py', explanation='Über backend/manage.py'),
    ]
    assert snippet == [
        node('backend/', children=backend),
        node('frontend/', explanation='Über frontend/'),
        node('README.md', explanation='Über README.md'),
    ]


def test_folders_come_first_then_files_by_name_ignoring_case() -> None:
    tree = ProjectTree()
    paths = ['b.txt', 'Zeta/', 'README.md', '.env', 'alpha/', '.github/', 'a.txt']
    snippet = tree.apply([record(path) for path in paths], ORIGIN)
    assert [item['path'] for item in snippet] == [
        '.github/',
        'alpha/',
        'Zeta/',
        '.env',
        'a.txt',
        'b.txt',
        'README.md',
    ]


def test_new_folder_without_new_children_stays_closed() -> None:
    snippet = ProjectTree().apply([record('backend/', explanation='Alles für Django.')], ORIGIN)
    assert snippet == [node('backend/', change='new', explanation='Alles für Django.')]


def test_new_folder_with_new_child_is_open() -> None:
    paths = [record('backend/', explanation='Django.'), record('backend/manage.py')]
    snippet = ProjectTree().apply(paths, ORIGIN)
    manage = node('backend/manage.py', change='new')
    assert snippet == [node('backend/', change='new', explanation='Django.', children=[manage])]


def test_step_without_paths_has_empty_snippet() -> None:
    assert tree_with('README.md').apply([], ORIGIN) == []


# Changing
def test_changed_file_shows_the_explanation_of_the_step() -> None:
    tree = tree_with('README.md')
    snippet = tree.apply([record('README.md', 'changed', 'Jetzt mit Anleitung.')], ORIGIN)
    assert snippet == [node('README.md', change='changed', explanation='Jetzt mit Anleitung.')]


def test_changed_file_keeps_its_origin_and_first_explanation() -> None:
    tree = tree_with('README.md')
    tree.apply([record('README.md', 'changed', 'Jetzt mit Anleitung.')], ORIGIN)
    expected = node('README.md', explanation='Über README.md', phase='vorher', step='start')
    assert tree.nodes() == [expected]


def test_changed_file_that_was_never_added_is_created() -> None:
    tree = ProjectTree()
    tree.apply([record('.gitignore', 'changed', 'Ignoriert .env.')], ORIGIN)
    assert tree.nodes() == [
        node('.gitignore', explanation='Ignoriert .env.', phase=ORIGIN[0], step=ORIGIN[1])
    ]


def test_new_again_replaces_origin_and_explanation() -> None:
    tree = tree_with('README.md')
    tree.apply([record('README.md', 'new', 'Neu geschrieben.')], ORIGIN)
    expected = node('README.md', explanation='Neu geschrieben.', phase=ORIGIN[0], step=ORIGIN[1])
    assert tree.nodes() == [expected]


# Removing
def test_removed_file_is_shown_once_then_gone() -> None:
    tree = tree_with('backend/tests.py', 'backend/manage.py')
    snippet = tree.apply([record('backend/tests.py', 'removed', 'Wird ein Ordner.')], ORIGIN)
    removed = node('backend/tests.py', change='removed', explanation='Wird ein Ordner.')
    manage = node('backend/manage.py', explanation='Über backend/manage.py')
    assert snippet == [node('backend/', children=[manage, removed])]
    assert [item['path'] for item in tree.nodes()[0]['children']] == ['backend/manage.py']


def test_removed_folder_removes_everything_inside() -> None:
    tree = tree_with('build/app.js', 'build/css/app.css', 'buildscript.sh')
    tree.apply([record('build/', 'removed')], ORIGIN)
    assert [item['path'] for item in tree.nodes()] == ['buildscript.sh']


def test_removing_unknown_path_changes_nothing() -> None:
    tree = tree_with('README.md')
    assert tree.apply([record('old.txt', 'removed')], ORIGIN) == []
    assert [item['path'] for item in tree.nodes()] == ['README.md']


def test_file_replaced_by_folder_in_one_step() -> None:
    tree = tree_with('backend/tests.py')
    changes = [record('backend/tests.py', 'removed'), record('backend/tests/__init__.py')]
    snippet = tree.apply(changes, ORIGIN)
    init = node('backend/tests/__init__.py', change='new')
    assert snippet[0]['children'] == [
        node('backend/tests/', children=[init]),
        node('backend/tests.py', change='removed'),
    ]
    assert [item['path'] for item in tree.nodes()[0]['children']] == ['backend/tests/']


# Git
def test_untracked_folder_and_everything_inside_are_untracked() -> None:
    tree = ProjectTree()
    tree.apply([record('backend/.venv/', tracked=False), record('backend/.venv/lib/x.py')], ORIGIN)
    venv = tree.nodes()[0]['children'][0]
    assert venv['tracked'] is False
    assert venv['children'][0]['tracked'] is False
    assert venv['children'][0]['children'][0]['tracked'] is False
    assert tree.nodes()[0]['tracked'] is True


def test_untracked_file_next_to_tracked_files() -> None:
    tree = ProjectTree()
    tree.apply([record('.env', tracked=False), record('.env.example')], ORIGIN)
    assert [(item['path'], item['tracked']) for item in tree.nodes()] == [
        ('.env', False),
        ('.env.example', True),
    ]


# Whole tree
def test_whole_tree_has_all_folders_open_with_origin() -> None:
    tree = ProjectTree()
    tree.apply([record('backend/', explanation='Django.')], ('backend-anlegen', 'ordner'))
    tree.apply([record('backend/core/settings.py', explanation='Einstellungen.')], ORIGIN)
    settings = node(
        'backend/core/settings.py', explanation='Einstellungen.', phase=ORIGIN[0], step=ORIGIN[1]
    )
    core = node('backend/core/', children=[settings])
    backend = node(
        'backend/', explanation='Django.', phase='backend-anlegen', step='ordner', children=[core]
    )
    assert tree.nodes() == [backend]


def test_whole_tree_shows_empty_open_folder() -> None:
    tree = ProjectTree()
    tree.apply([record('logs/')], ORIGIN)
    assert tree.nodes() == [node('logs/', phase=ORIGIN[0], step=ORIGIN[1], children=[])]


def test_snippet_has_no_origin() -> None:
    snippet = ProjectTree().apply([record('README.md')], ORIGIN)
    assert 'phase' not in snippet[0]
    assert 'step' not in snippet[0]
