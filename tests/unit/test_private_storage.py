import pytest
from backend.storage.private import ensure_private_file


def test_private_storage_permissions_and_symlink_rejection(tmp_path):
    data = tmp_path / 'private' / 'history.sqlite'
    ensure_private_file(data)
    assert data.exists()
    assert data.stat().st_mode & 0o777 == 0o600
    assert data.parent.stat().st_mode & 0o777 == 0o700
    link = data.parent / 'link.sqlite'
    link.symlink_to(data)
    with pytest.raises(ValueError):
        ensure_private_file(link)
