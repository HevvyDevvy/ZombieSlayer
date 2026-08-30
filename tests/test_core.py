import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.allowlist import AllowList
from core.settings_store import SettingsStore, DEFAULT_SETTINGS


def test_allowlist_add_valid_ip():
    al = AllowList()
    assert al.add("192.168.1.10") is True
    assert al.contains("192.168.1.10")


def test_allowlist_rejects_invalid_ip():
    al = AllowList()
    assert al.add("not-an-ip") is False
    assert not al.contains("not-an-ip")


def test_allowlist_remove():
    al = AllowList(["10.0.0.1"])
    al.remove("10.0.0.1")
    assert not al.contains("10.0.0.1")


def test_settings_defaults(tmp_path):
    store = SettingsStore(path=tmp_path / "settings.json")
    assert store.all_options == DEFAULT_SETTINGS["options"]


def test_settings_persist(tmp_path):
    path = tmp_path / "settings.json"
    store = SettingsStore(path=path)
    store.set_option("logging", False)
    store.save()

    store2 = SettingsStore(path=path)
    assert store2.get_option("logging") is False
