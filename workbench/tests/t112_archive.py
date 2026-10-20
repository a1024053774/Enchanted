"""Extract frozen Git fixtures with their controlled internal links unchanged."""
import io
import os
from pathlib import PurePosixPath
import posixpath
import tarfile


def extract_baseline(archive, destination):
    """Preserve Git links; reject escape, link-parent writes, cycles and special files."""
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        members = {}
        for member in tar.getmembers():
            path = PurePosixPath(member.name)
            if (path.is_absolute() or not path.parts or path.parts[0] != 'workbench'
                    or '..' in path.parts or '\0' in member.name or path in members
                    or not (member.isdir() or member.isfile() or member.issym() or member.islnk())):
                raise ValueError('unsafe_archive_member: ' + member.name)
            members[path] = member
        for path in members:
            for parent in path.parents:
                if parent in members and not members[parent].isdir():
                    raise ValueError('archive_parent_not_directory: ' + str(parent))

        def target(path, seen=()):
            if path in seen:
                raise ValueError('archive_link_cycle: ' + str(path))
            member = members.get(path)
            if member is None:
                raise ValueError('archive_link_target_missing: ' + str(path))
            if not (member.issym() or member.islnk()):
                return path
            link = PurePosixPath(member.linkname)
            if link.is_absolute() or '\0' in member.linkname:
                raise ValueError('unsafe_archive_link: ' + member.name)
            relative = path.parent / link if member.issym() else link
            resolved = PurePosixPath(posixpath.normpath(str(relative)))
            if not resolved.parts or resolved.parts[0] != 'workbench' or '..' in resolved.parts:
                raise ValueError('archive_link_escape: ' + member.name)
            return target(resolved, (*seen, path))

        # Validate the full graph before writing anything. No extraction can
        # traverse a symlink parent, even when a later tar member replaces it.
        resolved = {}
        for path, member in members.items():
            if member.issym() or member.islnk():
                resolved[path] = target(path)
                if member.islnk() and not members[resolved[path]].isfile():
                    raise ValueError('archive_hardlink_not_file: ' + member.name)
        if destination.exists() or destination.is_symlink():
            raise ValueError('archive_destination_exists')
        destination.mkdir(parents=True)
        for path, member in members.items():
            output = destination / str(path)
            if member.isdir():
                output.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(tar.extractfile(member).read())
                output.chmod(member.mode & 0o777)
        for path, member in members.items():
            output = destination / str(path)
            if member.issym():
                output.parent.mkdir(parents=True, exist_ok=True)
                output.symlink_to(member.linkname)
            elif member.islnk():
                output.parent.mkdir(parents=True, exist_ok=True)
                os.link(destination / str(resolved[path]), output)

