# Copyright 2022 Alvaro Bartolome, alvarobartt @ GitHub
# See LICENSE for details.

import datetime
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import wandb

from wandbfsspec.core import WandbBaseFileSystem

MAX_PATH_LENGTH_WITHOUT_FILE_PATH = 3
MAX_ARTIFACT_LENGTH_WITHOUT_FILE_PATH = 5

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

__all__ = ["WandbFileSystem", "WandbArtifactStore"]


class WandbFileSystem(WandbBaseFileSystem):
    protocol = "wandbfs"  # type: ignore

    @classmethod
    def split_path(
        self, path: str
    ) -> Tuple[str, Union[str, None], Union[str, None], Union[str, None]]:
        path = self._strip_protocol(path=path)
        path = path.lstrip("/")
        if "/" not in path:
            return (path, None, None, None)
        path = path.split("/")  # type: ignore
        if len(path) > MAX_PATH_LENGTH_WITHOUT_FILE_PATH:
            return (  # type: ignore
                *path[:MAX_PATH_LENGTH_WITHOUT_FILE_PATH],
                "/".join(path[MAX_PATH_LENGTH_WITHOUT_FILE_PATH:]),
            )
        path += [None] * (MAX_PATH_LENGTH_WITHOUT_FILE_PATH - len(path))  # type: ignore
        return (*path, None)  # type: ignore

    @staticmethod
    def __ls_files(
        _files: List[Any],
        base_path: Union[str, Path],
        file_path: Union[str, Path] = Path("./"),
        detail: bool = False,
    ) -> Union[List[str], List[Dict[str, Any]]]:
        file_path = Path(file_path) if isinstance(file_path, str) else file_path
        files: Union[List[str], List[Dict[str, Any]]] = list()  # type: ignore
        for _file in _files:
            filename = Path(_file.name)
            if file_path not in filename.parents:
                continue
            filename_strip = Path(_file.name.replace(f"{file_path}/", ""))
            if filename_strip.is_dir() or len(filename_strip.parents) > 1:
                filename_strip = filename_strip.parent.as_posix().split("/")[0]  # type: ignore
                path = f"{base_path}/{filename_strip}"
                if any(f["name"] == path for f in files) if detail else path in files:  # type: ignore
                    continue
                files.append(
                    {  # type: ignore
                        "name": path,
                        "type": "directory",
                        "size": 0,
                    }
                    if detail
                    else path
                )
                continue
            files.append(
                {  # type: ignore
                    "name": f"{base_path}/{filename.name}",
                    "type": "file",
                    "size": _file.size,
                }
                if detail
                else f"{base_path}/{filename.name}"
            )
        return files

    @staticmethod
    def __ls_projects_or_runs(
        _files: List[Any], detail: bool = False
    ) -> Union[List[str], List[Dict[str, Any]]]:
        files = []
        for _file in _files:
            files.append(
                {
                    "name": _file.name,
                    "type": "directory",
                    "size": 0,
                }
                if detail
                else _file.name
            )
        return files

    def ls(
        self, path: str, detail: bool = False
    ) -> Union[List[str], List[Dict[str, Any]]]:
        entity, project, run_id, file_path = self.split_path(path=path)
        if entity and project and run_id:
            _files = self.api.run(f"{entity}/{project}/{run_id}").files()  # type: ignore
            base_path = f"{entity}/{project}/{run_id}"
            return self.__ls_files(
                _files=_files,
                base_path=f"{base_path}/{file_path}" if file_path else base_path,
                file_path=file_path if file_path else Path("./"),
                detail=detail,
            )
        elif entity and project:
            _files = self.api.runs(f"{entity}/{project}")
            base_path = f"{entity}/{project}"
            return self.__ls_projects_or_runs(_files=_files, detail=detail)
        elif entity:
            _files = self.api.projects(entity=entity)  # type: ignore
            base_path = entity
            return self.__ls_projects_or_runs(_files=_files, detail=detail)
        raise ValueError("You need to at least provide an `entity` value!")

    def modified(self, path: str) -> datetime.datetime:
        """Return the modified timestamp of a file as a datetime.datetime"""
        entity, project, run_id, file_path = self.split_path(path=path)
        if not file_path:
            raise ValueError(
                "`file_path` can't be None, make sure the `path` is valid!"
            )
        _file = self.api.run(f"{entity}/{project}/{run_id}").file(name=file_path)  # type: ignore
        if not _file:
            raise FileNotFoundError(
                f"`file` at {file_path} for {entity}/{project}/{run_id} couldn't be"
                " found or doesn't exist!"
            )
        return datetime.datetime.fromisoformat(_file.updated_at)

    def url(self, path: str) -> str:
        entity, project, run_id, file_path = self.split_path(path=path)
        _file = self.api.run(f"{entity}/{project}/{run_id}").file(name=file_path)  # type: ignore
        if not _file:
            raise FileNotFoundError(
                f"`file` at {file_path} for {entity}/{project}/{run_id} couldn't be"
                " found or doesn't exist!"
            )
        return str(_file.direct_url)

    def put_file(self, lpath: str, rpath: str, **kwargs: Dict[str, Any]) -> None:
        lpath_ext = os.path.splitext(lpath)[1]
        if lpath_ext == "":
            raise ValueError("`lpath` must be a file path with extension!")
        rpath_ext = os.path.splitext(rpath)[1]
        if rpath_ext != "" and rpath_ext != lpath_ext:
            raise ValueError(
                "`lpath` and `rpath` extensions must match if those are file paths!"
            )
        lpath = os.path.abspath(lpath)
        _lpath = lpath
        entity, project, run_id, file_path = self.split_path(path=rpath)
        if rpath_ext != "":
            _lpath = os.path.abspath(file_path)  # type: ignore
            os.makedirs(os.path.dirname(_lpath), exist_ok=True)
            os.replace(lpath, _lpath)
        run = self.api.run(f"{entity}/{project}/{run_id}")  # type: ignore
        run.upload_file(path=_lpath, root=".")

    def get_file(
        self, rpath: str, lpath: str, overwrite: bool = False, **kwargs: Dict[str, Any]
    ) -> None:
        if os.path.splitext(rpath)[1] == "":
            raise ValueError("`rpath` must be a file path with extension!")
        entity, project, run_id, file_path = self.split_path(path=rpath)
        file = self.api.run(f"{entity}/{project}/{run_id}").file(name=file_path)  # type: ignore
        _lpath = lpath
        if os.path.splitext(lpath)[1] != "":
            lpath = os.path.dirname(lpath)
        file.download(root=lpath, replace=overwrite)
        src_path = os.path.abspath(f"{lpath}/{rpath.split('/')[-1]}")
        tgt_path = os.path.abspath(_lpath)
        if src_path != tgt_path and not os.path.isdir(tgt_path):
            os.rename(src_path, tgt_path)

    def rm_file(self, path: str) -> None:
        entity, project, run_id, file_path = self.split_path(path=path)
        file = self.api.run(f"{entity}/{project}/{run_id}").file(name=file_path)  # type: ignore
        file.delete()

    def cp_file(self, path1: str, path2: str, **kwargs: Dict[str, Any]) -> None:
        path1_ext = os.path.splitext(path1)[1]
        if path1_ext == "":
            raise ValueError(f"Path {path1} must be a file path with extension!")
        path2_ext = os.path.splitext(path2)[1]
        if path2_ext == "":
            raise ValueError(f"Path {path1} must be a file path with extension!")
        if path1_ext != path2_ext:
            raise ValueError("Path extensions must be the same for both parameters!")
        with tempfile.TemporaryDirectory() as f:
            self.get_file(lpath=f, rpath=path1, overwrite=True)
            _, _, _, file_path = self.split_path(path=path1)
            self.put_file(lpath=f"{f}/{file_path}", rpath=path2)


class WandbArtifactStore(WandbBaseFileSystem):
    protocol = "wandbas"  # type: ignore

    @classmethod
    def split_path(
        self, path: str
    ) -> Tuple[
        str,
        Union[str, None],
        Union[str, None],
        Union[str, None],
        Union[str, None],
        Union[str, None],
    ]:
        path = self._strip_protocol(path=path)
        path = path.lstrip("/")
        if "/" not in path:
            return (path, *[None] * MAX_ARTIFACT_LENGTH_WITHOUT_FILE_PATH)  # type: ignore
        path = path.split("/")  # type: ignore
        if len(path) > MAX_ARTIFACT_LENGTH_WITHOUT_FILE_PATH:
            return (  # type: ignore
                *path[:MAX_ARTIFACT_LENGTH_WITHOUT_FILE_PATH],
                "/".join(path[MAX_ARTIFACT_LENGTH_WITHOUT_FILE_PATH:]),
            )
        path += [None] * (MAX_ARTIFACT_LENGTH_WITHOUT_FILE_PATH - len(path))  # type: ignore
        return (*path, None)  # type: ignore

    def ls(
        self, path: str, detail: bool = False
    ) -> Union[List[str], List[Dict[str, Any]]]:
        (
            entity,
            project,
            artifact_type,
            artifact_name,
            artifact_version,
            _,
        ) = self.split_path(path=path)
        if entity and project and artifact_type and artifact_name and artifact_version:
            return [
                f"{entity}/{project}/{artifact_type}/{artifact_name}/{artifact_version}/{f.name}"
                if not detail
                else {
                    "name": f"{entity}/{project}/{artifact_type}/{artifact_name}/{artifact_version}/{f.name}",
                    "type": "file",
                    "size": f.size,
                }
                for f in self.api.artifact(  # type: ignore
                    name=f"{entity}/{project}/{artifact_name}:{artifact_version}",
                    type=artifact_type,
                ).files()
            ]
        elif entity and project and artifact_type and artifact_name:
            return [
                f"{entity}/{project}/{artifact_type}/{artifact_name}/{v.name.split(':')[1]}"
                if not detail
                else {
                    "name": f"{entity}/{project}/{artifact_type}/{artifact_name}/{v.name.split(':')[1]}",
                    "type": "directory",
                    "size": 0,
                }
                for v in self.api.artifact_versions(  # type: ignore
                    name=f"{entity}/{project}/{artifact_name}", type_name=artifact_type
                )
            ]
        elif entity and project and artifact_type:
            return [
                f"{entity}/{project}/{artifact_type}/{c.name}"
                if not detail
                else {
                    "name": f"{entity}/{project}/{artifact_type}/{c.name}",
                    "type": "directory",
                    "size": 0,
                }
                for c in self.api.artifact_type(  # type: ignore
                    project=f"{entity}/{project}", type_name=artifact_type
                ).collections()
            ]
        elif entity and project:
            return [
                f"{entity}/{project}/{a.name}"
                if not detail
                else {
                    "name": f"{entity}/{project}/{a.name}",
                    "type": "directory",
                    "size": 0,
                }
                for a in self.api.artifact_types(project=f"{entity}/{project}")  # type: ignore
            ]
        elif entity:
            return [
                f"{entity}/{p.name}"
                if not detail
                else {
                    "name": f"{entity}/{p.name}",
                    "type": "directory",
                    "size": 0,
                }
                for p in self.api.projects(entity=entity)  # type: ignore
            ]
        raise ValueError("You need to at least provide an `entity` value!")

    def created(self, path: str) -> datetime.datetime:
        """Return the created timestamp of a file as a datetime.datetime"""
        (
            entity,
            project,
            artifact_type,
            artifact_name,
            artifact_version,
            _,
        ) = self.split_path(path=path)
        artifact = self.api.artifact(  # type: ignore
            name=f"{entity}/{project}/{artifact_name}:{artifact_version}",
            type=artifact_type,
        )
        if not artifact:
            raise ValueError("`artifact` is None, make sure that it exists!")
        return datetime.datetime.fromisoformat(artifact.created_at)

    def modified(self, path: str) -> datetime.datetime:
        """Return the modified timestamp of a file as a datetime.datetime"""
        (
            entity,
            project,
            artifact_type,
            artifact_name,
            artifact_version,
            _,
        ) = self.split_path(path=path)
        artifact = self.api.artifact(  # type: ignore
            name=f"{entity}/{project}/{artifact_name}:{artifact_version}",
            type=artifact_type,
        )
        if not artifact:
            raise ValueError("`artifact` is None, make sure that it exists!")
        return datetime.datetime.fromisoformat(artifact.updated_at)

    def url(self, path: str) -> str:
        (
            entity,
            project,
            artifact_type,
            artifact_name,
            artifact_version,
            file_path,
        ) = self.split_path(path=path)
        artifact = self.api.artifact(  # type: ignore
            name=f"{entity}/{project}/{artifact_name}:{artifact_version}",
            type=artifact_type,
        )
        manifest = artifact._load_manifest()
        digest = manifest.entries[file_path].digest
        digest_id = wandb.util.b64_to_hex_id(digest)
        return f"https://api.wandb.ai/artifactsV2/gcp-us/{artifact.entity}/{artifact.id}/{digest_id}"

    def get_file(
        self, lpath: str, rpath: str, overwrite: bool = False, **kwargs: Dict[str, Any]
    ) -> None:
        (
            entity,
            project,
            artifact_type,
            artifact_name,
            artifact_version,
            file_path,
        ) = self.split_path(path=rpath)
        artifact = self.api.artifact(  # type: ignore
            name=f"{entity}/{project}/{artifact_name}:{artifact_version}",
            type=artifact_type,
        )
        path = artifact.get_path(name=file_path)
        if os.path.exists(lpath) and not overwrite:
            return
        path.download(root=lpath)

    def rm_file(self, path: str, force_rm: bool = False) -> None:
        (
            entity,
            project,
            artifact_type,
            artifact_name,
            artifact_version,
            file_path,
        ) = self.split_path(path=path)
        if not file_path:
            if not force_rm:
                logging.info(
                    "In order to remove an artifact, you'll need to pass"
                    " `force_rm=True`."
                )
                return
            artifact = self.api.artifact(  # type: ignore
                name=f"{entity}/{project}/{artifact_name}:{artifact_version}",
                type=artifact_type,
            )
            artifact.delete(delete_aliases=True)
            return
        logging.info(
            "W&B just lets you remove complete artifact versions not artifact files."
        )
