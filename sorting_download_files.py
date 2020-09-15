"""
/usr/local/bin/python3 <<'EOF' - "$@"
Команда для запуска в WORKFLOW
VERSION = "3.5"
"""

import os
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, List, Optional, Set, Type

HOME_DIR: Path = Path.home()
BASE_DIR: Path = HOME_DIR / os.environ.setdefault("TARGET_DIR", "Downloads")
APPLICATION_FOLDER: Path = Path("/Applications")
EXCLUDE_LIST: List[str] = [
    "$RECYCLE.BIN",
    ".DS_Store",
    ".localized",
    "1-Applications",
    "2-Archives",
    "3-Audios",
    "4-Torrents",
    "5-Videos",
    "6-Images",
    "7-Docs",
    "8-Others",
    "Icon\r",
    "Telegram Desktop",
]
STATUSES = {0: "OK", 1: "ERROR"}


# <editor-fold desc="Checking Mime Types">
@dataclass
class Magic:
    mime: bool = field(default=True)

    def from_file(self, file_path: Path) -> str:
        stdout_result = subprocess.run(
            ["file", "-b", "--mime-type", file_path.as_posix()], capture_output=True
        ).stdout.decode()
        return self._get_major_mimetype(stdout_result)

    def _get_major_mimetype(self, stdout: str) -> str:
        """Разделение полученного результат от команды `file` на основной тип и подтип. Возрвщаем основной тип.

        :param stdout: Результат выподнения команды `file`
        """
        major_type, subtype = stdout.split("/")
        return major_type


magic_type = Magic()


# </editor-fold>


# <editor-fold desc="Actions">
@dataclass
class Action(ABC):
    @abstractmethod
    def perform(self, file_path: Path) -> None:
        """Команда действия над файлом """
        raise NotImplementedError("Subclasses must implement")


@dataclass
class EmptyAction(Action):
    def perform(self, file_path: Path) -> None:
        pass


@dataclass
class TorrentAction(Action):
    TORRENT_PATH: Path = APPLICATION_FOLDER / "Transmission Remote GUI.app"

    def perform(self, file_path: Path) -> None:
        print(f"Perform Torrent Action: {file_path=}")
        status_code = subprocess.run(
            ["open", self.TORRENT_PATH, file_path], capture_output=True
        ).returncode
        status = STATUSES.get(status_code, status_code)
        print(f"{status=}")


# </editor-fold>


# <editor-fold desc="Mappers">
@dataclass
class TypeMapper(ABC):
    _factories: List["FiletypeFactory"] = field(init=False, default_factory=list)
    _registered: Set[str] = field(init=False, default_factory=set)

    def register(self, cls: Type["FiletypeFactory"]) -> Type["FiletypeFactory"]:
        """Регистрация фабрики продуктов

        :param cls: фабрика создания продукта
        """
        if not issubclass(cls, FiletypeFactory):
            raise TypeError("Можно регистрировать только субклассы от Factory")

        if cls.__name__ in self._registered:
            raise ValueError(f"Класс `{cls.__name__}` уже зарегистрирован")

        self._factories.append(cls())
        self._registered.add(cls.__name__)
        return cls

    def seek(self, file_path: Path) -> Optional["Product"]:
        matches: List["FiletypeFactory"] = [
            factory for factory in self._factories if factory.matches(file_path)
        ]

        if not matches:
            print(f"Не удается найти фабрику для элемента: `{file_path}`")
            return None

        if len(matches) > 1:
            # raise ValueError("Найдено более одной фабрики!!!", matches)
            print(f"Найдено более одной фабрики!!!", matches)
            matches = [max(matches, key=lambda pr: pr.priority)]

        product = matches[0]
        print(f"Найдена фабрика: `{product.__class__.__name__}`")
        return product.make_product(file_path)


type_mapper = TypeMapper()


# </editor-fold>


# <editor-fold desc="Factories">
@dataclass
class FiletypeFactory(ABC):
    extensions: ClassVar[List[str]]
    mime_type: ClassVar[str]
    priority: ClassVar[int]

    @abstractmethod
    def matches(self, file_path: Path) -> bool:
        raise NotImplementedError("Subclasses must implement")

    @abstractmethod
    def make_product(self, file_path: Path) -> "Product":
        raise NotImplementedError("Subclasses must implement")


@type_mapper.register
class TorrentFactory(FiletypeFactory):
    priority = 9
    extensions = [".torrent"]

    def matches(self, file_path) -> bool:
        return file_path.suffix.lower() in self.extensions

    def make_product(self, file_path) -> "Product":
        return Torrent(file_path)


@type_mapper.register
class ArchiveFactory(FiletypeFactory):
    priority = 9
    extensions = [
        ".dmg",
        ".zip",
        ".gz",
        ".tar",
        ".rpm",
        ".iso",
        ".rar",
        ".7z",
    ]

    def matches(self, file_path) -> bool:
        return file_path.suffix.lower() in self.extensions

    def make_product(self, file_path) -> "Product":
        return Archive(file_path)


@type_mapper.register
class VideoFactory(FiletypeFactory):
    priority = 9
    extensions = [".mp4", ".avi", ".wmv", ".flv", ".mpg"]
    mime_type = "video"

    def matches(self, file_path) -> bool:
        if file_path.is_dir():
            return False

        mime_type = magic_type.from_file(file_path)
        return mime_type == self.mime_type

    def make_product(self, file_path) -> "Product":
        return Video(file_path)


@type_mapper.register
class ImageFactory(FiletypeFactory):
    priority = 9
    extensions = [".gif", ".jpg", ".ico", ".icns", ".png", ".tiff", ".svg"]
    mime_type = "image"

    def matches(self, file_path) -> bool:
        if file_path.is_dir():
            return False

        mime_type = magic_type.from_file(file_path)
        return mime_type == self.mime_type

    def make_product(self, file_path) -> "Product":
        return Image(file_path)


@type_mapper.register
class AudioFactory(FiletypeFactory):
    priority = 9
    extensions = [".mp3", ".m4a", ".flac", ".alac"]
    mime_type = "audio"

    def matches(self, file_path) -> bool:
        if file_path.is_dir():
            return False

        mime_type = magic_type.from_file(file_path)
        return mime_type == self.mime_type

    def make_product(self, file_path) -> "Product":
        return Audio(file_path)


@type_mapper.register
class ApplicationFactory(FiletypeFactory):
    priority = 9
    extensions = [".app", ".exe"]

    def matches(self, file_path) -> bool:
        return file_path.suffix.lower() in self.extensions

    def make_product(self, file_path) -> "Product":
        return Application(file_path)


@type_mapper.register
class DocumentFactory(FiletypeFactory):
    priority = 9
    extensions = [".djvu", ".pdf", ".doc", ".xlsx", ".txt", ".epub", ".rtf", ".docx"]

    def matches(self, file_path) -> bool:
        return file_path.suffix.lower() in self.extensions

    def make_product(self, file_path) -> "Product":
        return Document(file_path)


@type_mapper.register
class OtherFactory(FiletypeFactory):
    priority = 1
    extensions = []
    mime_type = "text"

    def matches(self, file_path) -> bool:
        if file_path.is_dir():
            return False

        mime_type = magic_type.from_file(file_path)
        return mime_type == self.mime_type

    def make_product(self, file_path) -> "Product":
        return Other(file_path)


# </editor-fold>


# <editor-fold desc="Products">
@dataclass
class Product(ABC):
    file_path: Path
    dir_path: ClassVar[Path]
    action: ClassVar[Type["Action"]]

    def _check_exists_dir_path(self) -> None:
        """Проверка существования каталога продуктов и если его нет, то создать"""
        if not self.dir_path.exists():
            self.dir_path.mkdir(mode=0o777)

    def move(self):
        """Перемещение файла в каталог конкретного продукта"""
        destination = self.dir_path / self.file_path.name
        self._check_exists_dir_path()
        print(f"Move file {self.file_path=} to {destination=}")
        self.file_path = self.file_path.replace(destination)  # noqa
        print(f"New path {self.file_path}")

    def perform(self):
        """Выполнение основных действий с файлом для конкретного продукта
        - Перемещаем файл в новый каталог
        - Выполняем действие над ним (запуск, распаковка, монтирование and etc.)
        """
        self.move()
        self.action().perform(self.file_path)


@dataclass
class Application(Product):
    dir_path: Path = BASE_DIR / "1-Applications"
    action: Type["Action"] = EmptyAction


@dataclass
class Archive(Product):
    dir_path: Path = BASE_DIR / "2-Archives"
    action: Type["Action"] = EmptyAction


@dataclass
class Audio(Product):
    dir_path: Path = BASE_DIR / "3-Audios"
    action: Type["Action"] = EmptyAction


@dataclass
class Torrent(Product):
    dir_path: Path = BASE_DIR / "4-Torrents"
    action: Type["Action"] = TorrentAction


@dataclass
class Video(Product):
    dir_path: Path = BASE_DIR / "5-Videos"
    action: Type["Action"] = EmptyAction


@dataclass
class Image(Product):
    dir_path: Path = BASE_DIR / "6-Images"
    action: Type["Action"] = EmptyAction


@dataclass
class Document(Product):
    dir_path: Path = BASE_DIR / "7-Docs"
    action: Type["Action"] = EmptyAction


@dataclass
class Other(Product):
    dir_path: Path = BASE_DIR / "8-Others"
    action: Type["Action"] = EmptyAction


# </editor-fold>


def main():
    children = sorted(
        child for child in BASE_DIR.iterdir() if child.name not in EXCLUDE_LIST
    )

    [
        product.perform()
        for child in children
        if (product := type_mapper.seek(child)) is not None
    ]


if __name__ == "__main__":
    main()
