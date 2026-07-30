"""Profile business logic."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from config_tool.models.profile import ConfigurationProfile, create_profile
from config_tool.profiles.store import ProfileNotFoundError, ProfileStore


class ProfileService:
    def __init__(self, store: Optional[ProfileStore] = None) -> None:
        self.store = store or ProfileStore()

    def list_profiles(self) -> list[ConfigurationProfile]:
        return self.store.list_profiles()

    def get_active(self) -> Optional[ConfigurationProfile]:
        return self.store.get_active()

    def set_active_by_name(self, name: str) -> ConfigurationProfile:
        profile = self.store.get_by_name(name)
        return self.store.set_active(profile.id)

    def set_active(self, profile_id: str) -> ConfigurationProfile:
        return self.store.set_active(profile_id)

    def add(self, **kwargs) -> ConfigurationProfile:
        profile = create_profile(**kwargs)
        return self.store.add(profile)

    def update(self, profile: ConfigurationProfile) -> ConfigurationProfile:
        return self.store.update(profile)

    def delete(self, profile_id: str) -> None:
        self.store.delete(profile_id)

    def delete_by_name(self, name: str) -> None:
        profile = self.store.get_by_name(name)
        self.store.delete(profile.id)

    def import_profile(self, file_path: Path) -> ConfigurationProfile:
        return self.store.import_profile(file_path)

    def export_profile(self, name: str, file_path: Path) -> None:
        profile = self.store.get_by_name(name)
        self.store.export_profile(profile.id, file_path)

    def get_by_name(self, name: str) -> ConfigurationProfile:
        return self.store.get_by_name(name)
