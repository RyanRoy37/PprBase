"""Atomic local storage for work-in-progress papers."""

from __future__ import annotations

import json
import os
import hashlib
import shutil
import tempfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from core.format_loader import FormatError, validate_format
from core.state_manager import PaperState


class DraftError(Exception):
    """A draft could not be saved or opened."""


class DraftStore:
    def __init__(self, directory: str) -> None:
        self.directory = Path(directory)

    def save(self, fmt: dict, state: PaperState, draft_id: str | None = None) -> str:
        """Save a draft using an atomic replace, returning its stable ID."""
        validate_format(fmt)
        draft_id = draft_id or uuid4().hex
        if not draft_id.isalnum():
            raise DraftError("That draft name is invalid.")
        saved_state = json.loads(state.to_json())
        saved_format = deepcopy(fmt)
        assets_dir = self.directory / "assets" / draft_id
        template_path = saved_format.get("docx_template")
        if template_path:
            source_template = Path(template_path)
            if not source_template.is_file():
                raise DraftError(f"The Word template is missing: {source_template}")
            try:
                assets_dir.mkdir(parents=True, exist_ok=True)
                stored_template = assets_dir / "paper_template.docx"
                if source_template.resolve() != stored_template.resolve():
                    shutil.copy2(source_template, stored_template)
                saved_format["docx_template"] = str(stored_template)
            except OSError as exc:
                raise DraftError(f"Couldn't copy the Word template into the draft: {exc}") from exc
        for questions in saved_state["sections"].values():
            for question in questions.values():
                source_path = question.get("image_path")
                if not source_path:
                    continue
                source = Path(source_path)
                if not source.is_file():
                    continue
                try:
                    assets_dir.mkdir(parents=True, exist_ok=True)
                    if source.parent.resolve() == assets_dir.resolve():
                        continue
                    digest = hashlib.sha256(str(source.resolve()).encode("utf-8")).hexdigest()[:16]
                    target = assets_dir / f"{digest}{source.suffix.lower()}"
                    if source.resolve() != target.resolve():
                        shutil.copy2(source, target)
                    question["image_path"] = str(target)
                except OSError:
                    # Save the question text even if this attachment cannot be copied.
                    pass
        payload = {
            "version": 1,
            "draft_id": draft_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "format": saved_format,
            "state": saved_state,
        }
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            fd, temp_path = tempfile.mkstemp(prefix=".draft_", suffix=".json", dir=self.directory)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as file:
                    json.dump(payload, file, ensure_ascii=False, indent=2)
                    file.flush()
                    os.fsync(file.fileno())
                os.replace(temp_path, self.directory / f"{draft_id}.json")
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        except OSError as exc:
            raise DraftError(f"Couldn't save your draft: {exc}") from exc
        return draft_id

    def load(self, draft_id: str) -> tuple[dict, PaperState]:
        if not draft_id.isalnum():
            raise DraftError("That draft name is invalid.")
        try:
            with (self.directory / f"{draft_id}.json").open(encoding="utf-8") as file:
                payload = json.load(file)
            fmt = payload["format"]
            validate_format(fmt)
            state = PaperState.from_json(json.dumps(payload["state"]))
            if state.format_id != fmt["format_id"]:
                raise ValueError("the draft and its format do not match")
            template_path = fmt.get("docx_template")
            if template_path and not Path(template_path).is_file():
                stored_template = self.directory / "assets" / draft_id / "paper_template.docx"
                if stored_template.is_file():
                    fmt["docx_template"] = str(stored_template)
            for questions in state.get_all().values():
                for question in questions.values():
                    image_path = question.get("image_path")
                    if image_path and not Path(image_path).is_file():
                        moved_image = self.directory / "assets" / draft_id / Path(image_path).name
                        if moved_image.is_file():
                            question["image_path"] = str(moved_image)
            return fmt, state
        except (OSError, ValueError, KeyError, TypeError, FormatError) as exc:
            raise DraftError(f"Couldn't open that draft: {exc}") from exc

    def list_drafts(self) -> list[dict]:
        if not self.directory.is_dir():
            return []
        drafts = []
        for path in self.directory.glob("*.json"):
            try:
                with path.open(encoding="utf-8") as file:
                    payload = json.load(file)
                fmt = payload["format"]
                validate_format(fmt)
                drafts.append({
                    "draft_id": path.stem,
                    "display_name": fmt["display_name"],
                    "updated_at": payload.get("updated_at", ""),
                })
            except (OSError, ValueError, KeyError, TypeError, FormatError):
                continue
        return sorted(drafts, key=lambda item: item["updated_at"], reverse=True)
