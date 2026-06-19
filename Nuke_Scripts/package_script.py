import nuke
import os
import shutil
import glob
import re


IMAGE_EXTS = {
    '.exr', '.dpx', '.tif', '.tiff', '.jpg', '.jpeg', '.png',
    '.tga', '.bmp', '.sgi', '.pic', '.rla', '.rpf', '.cin',
    '.dng', '.psd', '.hdr', '.svg',
}

GEO_EXTS = {
    '.abc', '.fbx', '.obj', '.usd', '.usda', '.usdc', '.usdz',
    '.ply', '.stl',
}

SUBDIRS = ['IMAGES', 'GEO', 'CAMERAS', 'RENDERS', 'SOURCE_WORKING_FILES']

CAT_TO_DIRNAME = {
    'image': 'IMAGES',
    'geo': 'GEO',
    'camera': 'CAMERAS',
    'render': 'RENDERS',
}


def _normalize_path(path):
    if not path:
        return path
    path = path.replace('\\', '/')
    return path


def _file_exists(path):
    if not path:
        return False
    if os.path.isfile(path):
        return True
    try:
        return nuke.tcl('file exists', path) == '1'
    except Exception:
        return False


def _resolve_filename(node, knob):
    for attempt in range(2):
        try:
            resolved = nuke.filename(node, knob.name())
        except Exception:
            resolved = None
        if resolved:
            resolved = _normalize_path(resolved)
            if _file_exists(resolved):
                return resolved
        if attempt == 0:
            raw = knob.getValue()
            if raw:
                raw = _normalize_path(raw)
                if _file_exists(raw):
                    return raw
    return None


def _glob_sequence(resolved_dir, glob_pattern):
    full_glob = os.path.join(resolved_dir, glob_pattern) if resolved_dir else glob_pattern
    full_glob = _normalize_path(full_glob)
    matches = sorted(glob.glob(full_glob))
    if matches:
        return matches
    try:
        tcl_glob = nuke.tcl('glob', full_glob)
        if tcl_glob:
            return sorted(tcl_glob.split())
    except Exception:
        pass
    return []


def _get_category(node, ext, knob_name):
    node_class = node.Class()
    if 'Camera' in node_class:
        return 'camera'
    if 'Write' in node_class:
        return 'render'
    if ext in IMAGE_EXTS:
        return 'image'
    if ext in GEO_EXTS:
        return 'geo'
    image_knobs = {'file', 'input', 'src', 'texture', 'map', 'matte', 'filename'}
    return 'image' if knob_name.lower() in image_knobs else 'geo'


def _make_glob_pattern(path_pattern):
    pattern = path_pattern
    pattern = re.sub(
        r'%(\d*)d',
        lambda m: '?' * max(1, int(m.group(1))) if m.group(1) else '?',
        pattern,
    )
    pattern = pattern.replace('#', '?')
    pattern = pattern.replace('@', '?')
    return pattern


def _collect_file_references():
    refs = []
    for node in nuke.allNodes():
        for knob in node.allKnobs():
            if not isinstance(knob, nuke.File_Knob):
                continue
            val = knob.getValue()
            if not val or not val.strip():
                continue
            is_seq = '%' in val or '#' in val or '@' in val
            ext = os.path.splitext(val)[1].lower()
            cat = _get_category(node, ext, knob.name())
            refs.append((node, knob, val, cat, is_seq))
    return refs


def _copy_single_file(src_path, dest_dir, dirname, pkg_root, copied):
    if src_path in copied:
        return copied[src_path]
    basename = os.path.basename(src_path)
    dest = os.path.join(dest_dir, basename)
    try:
        os.makedirs(dest_dir, exist_ok=True)
        shutil.copy2(src_path, dest)
    except (shutil.Error, IOError, OSError) as e:
        print(f"Warning: could not copy {src_path} -> {dest}: {e}")
        return None
    abs_path = _normalize_path(os.path.join(dest_dir, basename))
    copied[src_path] = abs_path
    return abs_path


def _copy_sequence(node, knob, orig_val, dest_dir, dirname, pkg_root, copied):
    resolved = _resolve_filename(node, knob)
    if not resolved:
        print(f"Warning: could not resolve sequence path: {orig_val}")
        return None

    dirpath = os.path.dirname(resolved)
    pattern_basename = os.path.basename(orig_val)
    glob_pattern = _make_glob_pattern(pattern_basename)
    matches = _glob_sequence(dirpath, glob_pattern)
    if not matches:
        print(f"Warning: no files found matching {orig_val}")
        return None
    for src in matches:
        if src in copied:
            continue
        dst = os.path.join(dest_dir, os.path.basename(src))
        try:
            shutil.copy2(src, dst)
            copied[src] = _normalize_path(dst)
        except (shutil.Error, IOError, OSError) as e:
            print(f"Warning: could not copy {src} -> {dst}: {e}")
    return _normalize_path(os.path.join(dest_dir, pattern_basename))


def _pick_directory():
    for pkg in ('PySide6', 'PySide2'):
        try:
            mod = __import__(pkg, fromlist=['QtWidgets'])
            result = mod.QtWidgets.QFileDialog.getExistingDirectory(
                None, "Select package destination"
            )
            if result:
                return result
        except Exception:
            continue

    try:
        import tkinter
        from tkinter import filedialog
        tk_root = tkinter.Tk()
        tk_root.withdraw()
        tk_root.lift()
        result = filedialog.askdirectory(title="Select package destination")
        tk_root.destroy()
        if result:
            return result
    except Exception:
        pass

    result = nuke.getInput("Enter target directory path for package:")
    return result.strip() if result else None


def _resolve_package_root(target_dir, script_name):
    target_basename = os.path.basename(target_dir)
    is_publish = 'PUBLISH' in target_basename.upper()

    if is_publish:
        parent_directory = os.path.basename(os.path.dirname(target_dir))
        if not parent_directory:
            parent_directory = script_name
        version = 1
        while True:
            version_str = f"v{version:03d}"
            pkg_root = os.path.join(
                target_dir, f"{parent_directory}_publish_{version_str}"
            )
            if not os.path.exists(pkg_root):
                break
            version += 1
    else:
        pkg_root = os.path.join(target_dir, f"{script_name}_PKG")

    return _normalize_path(pkg_root)


def package_script():
    print("[package_script] Packaging started...")
    original_path = nuke.root().name()
    if original_path == 'Root':
        nuke.message("Please save your script before packaging.")
        return

    script_name = os.path.splitext(os.path.basename(original_path))[0]

    confirm = nuke.ask("Save current script and run package process?")
    print(f"[package_script] confirm returned: {confirm!r}")
    if confirm is not True:
        print("[package_script] Aborted by user.")
        return

    try:
        nuke.scriptSave()
    except Exception as e:
        nuke.message(f"Could not save script: {e}")
        return

    target_dir = _pick_directory()
    if not target_dir:
        return

    pkg_root = _resolve_package_root(target_dir, script_name)

    cat_to_dirpath = {}
    for cat, dirname in CAT_TO_DIRNAME.items():
        cat_to_dirpath[cat] = _normalize_path(os.path.join(pkg_root, dirname))
    for dirname in SUBDIRS:
        os.makedirs(os.path.join(pkg_root, dirname), exist_ok=True)

    refs = _collect_file_references()
    if not refs:
        nuke.message("No file references found in the script.")
        return

    copied = {}
    to_update = []

    for node, knob, orig_val, cat, is_seq in refs:
        dest_dir = cat_to_dirpath[cat]
        dirname = CAT_TO_DIRNAME[cat]

        if is_seq:
            new_val = _copy_sequence(
                node, knob, orig_val, dest_dir, dirname, pkg_root, copied
            )
        else:
            resolved = _resolve_filename(node, knob)
            if resolved:
                new_val = _copy_single_file(resolved, dest_dir, dirname, pkg_root, copied)
            else:
                print(f"Warning: file not found: {orig_val} (node: {node.name()})")
                new_val = None

        if new_val is None and cat == 'render':
            basename = os.path.basename(orig_val)
            new_val = _normalize_path(os.path.join(dest_dir, basename))

        if new_val is not None:
            to_update.append((knob, orig_val, new_val))

    if not to_update:
        nuke.message(
            "No files could be copied.\n\n"
            "Check the Script Editor output for warnings.\n"
            "Common causes: network paths (//server/share), missing files, "
            "or unresolved TCL expressions."
        )
        return

    pkg_folder_name = os.path.basename(pkg_root)
    new_script_path = _normalize_path(os.path.join(pkg_root, f"{pkg_folder_name}.nk"))
    used_export = False

    try:
        for knob, orig, new in to_update:
            knob.setValue(new)

        if hasattr(nuke, 'scriptExport'):
            try:
                nuke.scriptExport(new_script_path)
                used_export = True
            except Exception as e:
                print(f"Warning: scriptExport failed: {e}")

        if not used_export:
            nuke.scriptSaveAs(new_script_path, overwrite=-1)
    finally:
        for knob, orig, new in to_update:
            knob.setValue(orig)

        if not used_export:
            try:
                nuke.scriptOpen(original_path)
            except Exception as e:
                print(f"Warning: could not reopen original script: {e}")

    nuke.message(
        f"Package created at:\n{pkg_root}\n\n"
        f"Copied {len(to_update)} file reference(s).\n"
        f"The scene has been restored to its original state."
    )


if __name__ == "__main__":
    package_script()
