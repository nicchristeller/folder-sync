import subprocess
import sys
import os
import shutil
import traceback
import ctypes
import stat
import time

LOG_ONLY = False
FORCE_REMOVE = False
SHOW_ACTIONS = False
LOG_DIR_PATH = "C:\\Users\\Nic\\Documents\\Mine\\Coding\\file-copier\\logs\\"
time_str = time.strftime('%H.%M-%d-%b-%Y')
LOG_FILE_NAME = "log-" + time_str + ".txt"
ERROR_FILE_NAME = "error-" + time_str + ".txt"

most_recent_action = ""


# copies the contents of root_src_dir to root_dst_dir
# files will only be overridden if they are more recently modified
# files in root_dst_dir that aren't in root_src_dir will be deleted
def sync_folders(root_src_dir, root_dst_dir):
    time_str = time.strftime('%H.%M-%d-%b-%Y')
    LOG_FILE_NAME = "log-" + time_str + ".txt"
    ERROR_FILE_NAME = "error-" + time_str + ".txt"
    if FORCE_REMOVE:
        LOG_FILE_NAME = LOG_FILE_NAME.replace(".txt", "-forced.txt")
        ERROR_FILE_NAME = ERROR_FILE_NAME.replace(".txt", "-forced.txt")
    merge_folders(root_src_dir, root_dst_dir)
    delete_nonexistent_files(root_src_dir, root_dst_dir)


# copies the contents of root_src_dir to root_dst_dir
# files will only be overridden if they are more recently modified
def merge_folders(root_src_dir, root_dst_dir):
    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)

        if not os.path.exists(dst_dir):
            log("Creating folder %s" % dst_dir)
            if not LOG_ONLY:
                os.makedirs(dst_dir)

        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)

            if os.path.exists(dst_file):
                src_modified_time = os.stat(src_file).st_mtime
                dst_modified_time = os.stat(dst_file).st_mtime
                # replace file if it's older
                if dst_modified_time < src_modified_time:
                    log("Overwriting %s with %s " % (dst_file, src_file))
                    if not LOG_ONLY:
                        remove_file(dst_file)
                        shutil.copy2(src_file, dst_dir)
            else:
                log("Copying file %s to \n\t%s" % (src_file, dst_dir))
                if not LOG_ONLY:
                    shutil.copy2(src_file, dst_dir)


# delete files and folders in root_dst_dir that aren't in root_src_dir
def delete_nonexistent_files(root_src_dir, root_dst_dir):
    for dst_dir, dirs, files in os.walk(root_dst_dir):
        src_dir = dst_dir.replace(root_dst_dir, root_src_dir, 1)

        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)

            if not os.path.exists(src_file):
                log("Removing file " + dst_file)
                if not LOG_ONLY:
                    remove_file(dst_file)

        if not os.path.exists(src_dir):
            log("Removing folder and contents " + dst_dir)
            if not LOG_ONLY:
                shutil.rmtree(dst_dir, onerror=remove_readonly if FORCE_REMOVE else None)


def log(message):
    global most_recent_action
    most_recent_action = message
    LOG_FILE.write(message + "\n\n")
    if SHOW_ACTIONS:
        print(message)


def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    for root, dirs, files in os.walk(path):
        for file_name in files:
            full_path = os.path.join(root, file_name)
            os.chmod(full_path, stat.S_IWRITE)
    func(path)


def remove_file(path):
    try:
        os.remove(path)
    except PermissionError:
        if FORCE_REMOVE:
            os.chmod(path, stat.S_IWRITE)
            os.remove(path)
        else:
            raise


def error_dialog():
    # add instructions to retry in forced mode if not currently in forced mode
    force_instructions = "" if FORCE_REMOVE else "Press retry to rerun in forced mode."
    print("\n\nFORCED MODE:", FORCE_REMOVE)
    message_box = ctypes.windll.user32.MessageBoxW(
                    0,
                    "There was an error when syncing folder %s with %s. %s See error.txt for more details. \n\nError encountered while %s"
                    % (sys.argv[1], sys.argv[2], force_instructions, most_recent_action.replace(sys.argv[1], "").replace(sys.argv[2], "")),
                    "Folder sync error",
                    0x5)
    if message_box == 4:
        # retry clicked
        global FORCE_REMOVE
        FORCE_REMOVE = True
        sync_folders(sys.argv[1], sys.argv[2])

# Sample usage via cmd
# "C:\Program Files\Python33\python.exe" "C:\Users\Nic\Documents\Mine\Coding\file-copier\sync-folders.py" "C:\Users\Nic\Documents\Mine" "C:\Users\Nic\Google Drive\Mine" log force
# arguments expected: src_dir dst_dir [log] [force] [actions]
# log is optional. If present, no actions will be taken: only a log will be produced
# force is optional. If present, the program will make an attempt to delete read-only files if found
# actions is optional. If present, the program will print its actions to standard output as it goes
#
print("\n\nCommand line arguments:\n", sys.argv)
if len(sys.argv) in (range(3, 7)):
    source_directory = sys.argv[1]
    if os.path.exists(source_directory):
        destination_directory = sys.argv[2]
        optional_args = sys.argv[3:]
        if 'log' in optional_args:
            LOG_ONLY = True
        if 'force' in optional_args:
            FORCE_REMOVE = True
        if 'actions' in optional_args:
            SHOW_ACTIONS = True
        with open(LOG_DIR_PATH + LOG_FILE_NAME, 'w') as LOG_FILE:
            try:
                sync_folders(source_directory, destination_directory)
                print("Done!")
            except:
                with open(LOG_DIR_PATH + ERROR_FILE_NAME, 'w') as ERROR_FILE:
                    ERROR_FILE.write(traceback.format_exc())
                    ERROR_FILE.write("\nError while completing action%s:\n%s" %
                                     (" (forced mode)" if FORCE_REMOVE else "",
                                      most_recent_action))
                error_dialog()
                raise
    else:
        raise NotADirectoryError(source_directory)
else:
    raise SyntaxError("Must have 2 arguments: an existing source directory and the desired destination directory. 2" +
                      "flags are optional.")
