"""
Data Storage class
"""
import os
import logging
import json
import shutil

from pathlib import Path
from typing import Dict, List, Optional, Union


logger = logging.getLogger(__name__)


class Storage:
    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path

    def move_file(self, old_path: Path, new_path: Path) -> None:
        Path(new_path.parent).mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_path.resolve()), str(new_path.resolve()))

    def list_files(self, suffix: Path) -> List[str]:
        full_path = self.base_path / suffix
        p = full_path.glob("**/*")
        files = [f for f in p if f.is_file()]
        files.sort(key=os.path.getmtime)
        return [os.path.basename(f) for f in files]

    def delete_files(self, suffix: Path) -> None:
        full_path = self.base_path / suffix
        logger.debug("Deleting files from %s", full_path)
        p = full_path.glob("**/*")
        files = [f for f in p if f.is_file()]
        for f in files:
            os.remove(f)

    @staticmethod
    def save_bytes(full_path: Path, content: bytes) -> bool:
        logger.debug("Saving bytes to %s", full_path)
        try:
            with open(full_path, mode="wb") as f:
                f.write(content)
            return True
        except (IOError, IndexError) as e:
            logger.error("Failed to save bytes to %s", full_path)
            logger.exception(e)
        return False

    @staticmethod
    def save_json(full_path: Path, content: Dict) -> bool:
        logger.debug("Saving json to %s", full_path)
        try:
            with open(full_path, mode="w") as f:
                json.dump(content, f)
            return True
        except (IOError, IndexError) as e:
            logger.error("Failed to save json to %s", full_path)
            logger.exception(e)
        return False

    @staticmethod
    def save_str(full_path: Path, content: str) -> bool:
        logger.debug("Saving string to %s", full_path)
        try:
            with open(full_path, mode="w") as f:
                f.write(content)
            return True
        except (IOError, IndexError) as e:
            logger.error("Failed to save string to %s", full_path)
            logger.exception(e)
        return False

    def save(self, suffix: Path, content: Union[bytes, str, int, dict]) -> bool:
        self.base_path.mkdir(parents=True, exist_ok=True)
        full_path = self.base_path / suffix

        result = False
        if isinstance(content, bytes):
            result = Storage.save_bytes(full_path, content)
        elif isinstance(content, dict):
            result = Storage.save_json(full_path, content)
        elif isinstance(content, (int, str)):
            result = Storage.save_str(full_path, str(content))
        else:
            logger.error(
                "Type (%s) is not supported for saving. Retry with a valid type",
                type(content),
            )
        return result

    def read_bytes(self, suffix: Path) -> Optional[bytes]:
        full_path = self.base_path / suffix

        try:
            with open(full_path, mode="rb") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("Path %s not found", full_path)
        except (IOError, IndexError) as e:
            logger.error("Failed to read bytes from %s", full_path)
            logger.exception(e)
        return None

    def read_json(self, suffix: Path) -> Optional[Dict]:
        full_path = self.base_path / suffix

        try:
            with open(full_path, mode="r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Path %s not found", full_path)
        except (IOError, IndexError) as e:
            logger.error("Failed to read json from %s", full_path)
            logger.exception(e)
        return None

    def read_string(self, suffix: Path) -> Optional[str]:
        full_path = self.base_path / suffix

        try:
            with open(full_path, mode="r") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("Path %s not found", full_path)
        except (IOError, IndexError) as e:
            logger.error("Failed to read string from %s", full_path)
            logger.exception(e)
        return None
