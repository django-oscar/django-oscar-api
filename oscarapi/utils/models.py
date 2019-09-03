from contextlib import contextmanager

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


@contextmanager
def fake_autocreated(many_to_many_manager):
    "Do not give a shit about any intermediate models, just update the relation"
    with patch.object(many_to_many_manager.through._meta, "auto_created", True):
        yield many_to_many_manager
