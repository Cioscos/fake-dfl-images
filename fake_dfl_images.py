from argparse import ArgumentParser
from pathlib import Path
import os
import sys
import multiprocessing as mp

from tqdm import tqdm

from xlib.DFLIMG.DFLJPG import DFLJPG

IMG_EXTENSIONS = [
    '.jpg', '.JPG', '.jpeg', '.JPEG'
]

def is_image_file(filename):
    return any(filename.endswith(extension) for extension in IMG_EXTENSIONS)

def make_dataset(dir: str):
    files = []
    assert os.path.isdir(dir), '%s is not a valid directory' % dir

    for root, _, fnames in os.walk(dir):
        for fname in fnames:
            if is_image_file(fname):
                path = os.path.join(root, fname)
                files.append(Path(path))

    return files

def put_fake_data(file_path: Path):
    new_dfl_image = DFLJPG.load(file_path)
    if not new_dfl_image:
        raise Exception(f"Impossible to load image {file_path.name} at filepath: {file_path}")
    new_dfl_image.set_source_filename(file_path.name)
    new_dfl_image.save()

# Module multiprocessing is organized differently in Python 3.4+
try:
    # Python 3.4+
    if sys.platform.startswith('win'):
        import multiprocessing.popen_spawn_win32 as forking
    else:
        import multiprocessing.popen_fork as forking
except ImportError:
    pass

if sys.platform.startswith('win'):
    # First define a modified version of Popen.
    class _Popen(forking.Popen):
        def __init__(self, *args, **kw):
            if hasattr(sys, 'frozen'):
                # We have to set original _MEIPASS2 value from sys._MEIPASS
                # to get --onefile mode working.
                os.putenv('_MEIPASS2', sys._MEIPASS)
            try:
                super(_Popen, self).__init__(*args, **kw)
            finally:
                if hasattr(sys, 'frozen'):
                    # On some platforms (e.g. AIX) 'os.unsetenv()' is not
                    # available. In those cases we cannot delete the variable
                    # but only set it to the empty string. The bootloader
                    # can handle this case.
                    if hasattr(os, 'unsetenv'):
                        os.unsetenv('_MEIPASS2')
                    else:
                        os.putenv('_MEIPASS2', '')

    # Second override 'Popen' class with our modified version.
    forking.Popen = _Popen

def main():
    # manage input arguments
    parser = ArgumentParser()
    parser.add_argument('-i', '--input', type=str, dest='input', required=True, help='Folder where to search input images files')
    args = parser.parse_args()

    # create dataset from path
    input_set = make_dataset(args.input)

    with mp.Pool(processes=mp.cpu_count()) as p:
        list(tqdm(p.imap_unordered(put_fake_data, input_set),desc="Injecting fake data", total=len(input_set), ascii=True))

if __name__ == "__main__":
    mp.freeze_support()
    main()
    input('Press a key to continue . . .')
