"""JSON profile persistence."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Optional

from config_tool.models.profile import ConfigurationProfile
from config_tool.paths import get_app_data_dir


class ProfileNotFoundError(KeyError):
    """Raised when a profile id or name is not found."""


class ProfileStore:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or (get_app_data_dir() / "profiles.json")
        self._active_profile_id: Optional[str] = None
        self._profiles: dict[str, ConfigurationProfile] = {}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self._profiles = {}
            self._active_profile_id = None
            return
        with self.path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        self._active_profile_id = data.get("active_profile_id")
        self._profiles = {}
        for item in data.get("profiles", []):
            profile = ConfigurationProfile.from_dict(item)
            self._profiles[profile.id] = profile

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "active_profile_id": self._active_profile_id,
            "profiles": [p.to_dict() for p in self._profiles.values()],
        }
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)

    def list_profiles(self) -> list[ConfigurationProfile]:
        return sorted(self._profiles.values(), key=lambda p: p.name.lower())

    def get(self, profile_id: str) -> ConfigurationProfile:
        if profile_id not in self._profiles:
            raise ProfileNotFoundError(profile_id)
        return self._profiles[profile_id]

    def get_by_name(self, name: str) -> ConfigurationProfile:
        for profile in self._profiles.values():
            if profile.name == name:
                return profile
        raise ProfileNotFoundError(name)

    def add(self, profile: ConfigurationProfile) -> ConfigurationProfile:
        profile.validate()
        for existing in self._profiles.values():
            if existing.name == profile.name and existing.id != profile.id:
                raise ValueError(f"Profile name already exists: {profile.name}")
        self._profiles[profile.id] = profile
        if self._active_profile_id is None:
            self._active_profile_id = profile.id
        self.save()
        return profile

    def update(self, profile: ConfigurationProfile) -> ConfigurationProfile:
        if profile.id not in self._profiles:
            raise ProfileNotFoundError(profile.id)
        profile.validate()
        for existing in self._profiles.values():
            if existing.name == profile.name and existing.id != profile.id:
                raise ValueError(f"Profile name already exists: {profile.name}")
        self._profiles[profile.id] = profile
        self.save()
        return profile

    def delete(self, profile_id: str) -> None:
        if profile_id not in self._profiles:
            raise ProfileNotFoundError(profile_id)
        del self._profiles[profile_id]
        if self._active_profile_id == profile_id:
            remaining = list(self._profiles.keys())
            self._active_profile_id = remaining[0] if remaining else None
        self.save()

    def set_active(self, profile_id: str) -> ConfigurationProfile:
        if profile_id not in self._profiles:
            raise ProfileNotFoundError(profile_id)
        self._active_profile_id = profile_id
        self.save()
        return self._profiles[profile_id]

    def get_active(self) -> Optional[ConfigurationProfile]:
        if self._active_profile_id is None:
            return None
        return self._profiles.get(self._active_profile_id)

    def import_profile(self, file_path: Path) -> ConfigurationProfile:
        with file_path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        data["id"] = str(uuid.uuid4())
        profile = ConfigurationProfile.from_dict(data)
        return self.add(profile)

    def export_profile(self, profile_id: str, file_path: Path) -> None:
        profile = self.get(profile_id)
        export_data = profile.to_dict()
        with file_path.open("w", encoding="utf-8") as fh:
            json.dump(export_data, fh, indent=2)
