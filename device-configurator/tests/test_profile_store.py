"""Tests for profile store."""

import json
from pathlib import Path

import pytest

from config_tool.models.profile import create_profile
from config_tool.profiles.store import ProfileNotFoundError, ProfileStore


@pytest.fixture
def store_path(tmp_path: Path) -> Path:
    return tmp_path / "profiles.json"


@pytest.fixture
def store(store_path: Path) -> ProfileStore:
    return ProfileStore(path=store_path)


def test_add_and_list(store: ProfileStore):
    p = create_profile(name="Test", APPEUI="0000000000000001", APPKEY="2B7E151628AED2A6ABF7158809CF4F3C")
    store.add(p)
    profiles = store.list_profiles()
    assert len(profiles) == 1
    assert profiles[0].name == "Test"


def test_persistence(store: ProfileStore, store_path: Path):
    p = create_profile(name="Persist", APPEUI="0000000000000001", APPKEY="2B7E151628AED2A6ABF7158809CF4F3C")
    store.add(p)
    store2 = ProfileStore(path=store_path)
    assert store2.get_by_name("Persist").APPEUI == "0000000000000001"


def test_set_active(store: ProfileStore):
    p1 = create_profile(name="A", APPEUI="0000000000000001", APPKEY="2B7E151628AED2A6ABF7158809CF4F3C")
    p2 = create_profile(name="B", APPEUI="0000000000000002", APPKEY="2B7E151628AED2A6ABF7158809CF4F3C")
    store.add(p1)
    store.add(p2)
    store.set_active(p2.id)
    assert store.get_active().name == "B"


def test_import_export(store: ProfileStore, tmp_path: Path):
    p = create_profile(name="ExportMe", APPEUI="0000000000000001", APPKEY="2B7E151628AED2A6ABF7158809CF4F3C")
    store.add(p)
    export_path = tmp_path / "export.json"
    store.export_profile(p.id, export_path)
    data = json.loads(export_path.read_text())
    assert data["name"] == "ExportMe"
    imported = store.import_profile(export_path)
    assert imported.name == "ExportMe"
    assert imported.id != p.id


def test_delete(store: ProfileStore):
    p = create_profile(name="Del", APPEUI="0000000000000001", APPKEY="2B7E151628AED2A6ABF7158809CF4F3C")
    store.add(p)
    store.delete(p.id)
    with pytest.raises(ProfileNotFoundError):
        store.get(p.id)
