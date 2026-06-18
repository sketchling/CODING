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


def _get_default_category(ext, knob_name):
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
    for node in nuke.allNodes('all'):
        for knob in node.allKnobs():
            if not isinstance(knob, nuke.File_Knob):
                continue
            val = knob.getValue()
            if not val or not val.strip():
                continue
            is_seq = '%' in val or '#' in val or '@' in val
            ext = os.path.splitext(val)[1].lower()
            cat = _get_default_category(ext, knob.name())
            refs.append((node, knob, val, cat, is_seq))
    return refs


def _copy_single_file(src_path, dest_dir, cat, copied):
    if not os.path.isfile(src_path):
        return None
    basename = os.path.basename(src_path)
    dest = os.path.join(dest_dir, basename)
    if src_path not in copied:
        try:
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(src_path, dest)
            copied[src_path] = os.path.join(cat, basename)
        except (shutil.Error, IOError, OSError) as e:
            print(f"Warning: could not copy {src_path} -> {dest}: {e}")
            return None
    return os.path.join(cat, basename)


def _copy_sequence(orig_val, cat, geo_dir, img_dir, copied):
    dirname = os.path.dirname(orig_val)
    basename = os.path.basename(orig_val)
    glob_pattern = _make_glob_pattern(basename)
    full_glob = os.path.join(dirname, glob_pattern) if dirname else glob_pattern
    matches = sorted(glob.glob(full_glob))
    if not matches:
        print(f"Warning: no files found matching {full_glob}")
        return None
    target_dir = geo_dir if cat == 'geo' else img_dir
    for src in matches:
        dst = os.path.join(target_dir, os.path.basename(src))
        if src not in copied:
            try:
                shutil.copy2(src, dst)
                copied[src] = os.path.join(cat, os.path.basename(src))
            except (shutil.Error, IOError, OSError) as e:
                print(f"Warning: could not copy {src} -> {dst}: {e}")
    return os.path.join(cat, basename)


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


def package_script():
    print("[package_script] Packaging started...")
    original_path = nuke.root().name()
    if original_path == 'Root':
        nuke.message("Please save your script before packaging.")
        return

    script_name = os.path.splitext(os.path.basename(original_path))[0]

    target_dir = _pick_directory()
    if not target_dir:
        return

    pkg_root = os.path.join(target_dir, f"{script_name}_PKG")
    geo_dir = os.path.join(pkg_root, "geo")
    img_dir = os.path.join(pkg_root, "image")
    for d in (pkg_root, geo_dir, img_dir):
        os.makedirs(d, exist_ok=True)

    refs = _collect_file_references()
    if not refs:
        nuke.message("No file references found in the script.")
        return

    copied = {}
    to_update = []

    for node, knob, orig_val, cat, is_seq in refs:
        if is_seq:
            new_val = _copy_sequence(
                orig_val, cat, geo_dir, img_dir, copied
            )
        else:
            try:
                resolved = nuke.filename(node, knob.name())
            except Exception:
                resolved = None
            if not resolved or not os.path.isfile(resolved):
                continue
            target_dir = geo_dir if cat == 'geo' else img_dir
            new_val = _copy_single_file(resolved, target_dir, cat, copied)

        if new_val is not None:
            to_update.append((knob, orig_val, new_val))

    if not to_update:
        nuke.message("No files could be copied.")
        return

    for knob, orig, new in to_update:
        knob.setValue(new)

    new_script_path = os.path.join(pkg_root, f"{script_name}.nk")

    try:
        nuke.scriptExport(new_script_path)
    except AttributeError:
        nuke.scriptSaveAs(new_script_path, overwrite=-1)
        for knob, orig, new in to_update:
            knob.setValue(orig)
        nuke.scriptSaveAs(original_path, overwrite=-1)
        nuke.message(
            f"Package created at:\n{pkg_root}\n\n"
            f"Copied {len(to_update)} file reference(s).\n"
            f"The scene has been restored to its original state."
        )
        return

    for knob, orig, new in to_update:
        knob.setValue(orig)

    nuke.message(
        f"Package created at:\n{pkg_root}\n\n"
        f"Copied {len(to_update)} file reference(s).\n"
        f"The scene has been restored to its original state."
    )


if __name__ == "__main__":
    package_script()
