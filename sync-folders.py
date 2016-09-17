import ctypes
import os
import shutil
import stat
import sys
import time
import traceback

LOG_DIR_PATH = "C:\\Users\\Nic\\Documents\\Mine\\Coding\\file-copier\\logs\\"


# copies the contents of root_src_dir to root_dst_dir
# files will only be overridden if they are more recently modified
# files in root_dst_dir that aren't in root_src_dir will be deleted
def sync_folders(root_src_dir, root_dst_dir, log_only=False, force_delete=False, print_actions=False, log_visits=False):
    logger = Logger(LOG_DIR_PATH, force_delete=force_delete, print_actions=print_actions, log_visits=log_visits)
    try:
        logger.log("** Syncing %s with %s... **" % (root_src_dir, root_dst_dir))
        logger.log("** Merging folders... **")
        merge_folders(root_src_dir, root_dst_dir, logger, log_only, force_delete)
        logger.log("** Cleaning up destination folder... **")
        delete_nonexistent_files(root_src_dir, root_dst_dir, logger, log_only, force_delete)
    except:
        error_occurred(logger)
        raise
    finally:
        print("Closing logger...")
        logger.close()


# copies the contents of root_src_dir to root_dst_dir
# files will only be overridden if they are more recently modified
def merge_folders(root_src_dir, root_dst_dir, logger, log_only, force_delete):
    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
        logger.log("Comparing folders {}...".format(src_dir.replace(root_src_dir, "")), visit=True)

        logger.log("Checking folder {} exists...".format(dst_dir), visit=True)
        if not os.path.exists(dst_dir):
            logger.log("Creating folder %s" % dst_dir)
            if not log_only:
                os.makedirs(dst_dir)

        for file in files:
            logger.log("Looking for file {}...".format(file), visit=True)
            src_file = os.path.join(src_dir, file)
            dst_file = os.path.join(dst_dir, file)

            if os.path.exists(dst_file):
                src_modified_time = os.stat(src_file).st_mtime
                dst_modified_time = os.stat(dst_file).st_mtime
                # replace file if it's older
                if dst_modified_time < src_modified_time:
                    logger.log("Overwriting %s with %s " % (dst_file, src_file))
                    if not log_only:
                        remove_file(dst_file, force_delete)
                        shutil.copy2(src_file, dst_dir)
            else:
                logger.log("Copying file %s to \n\t%s" % (src_file, dst_dir))
                if not log_only:
                    shutil.copy2(src_file, dst_dir)


# delete files and folders in root_dst_dir that aren't in root_src_dir
def delete_nonexistent_files(root_src_dir, root_dst_dir, logger, log_only, force_delete):
    for dst_dir, dirs, files in os.walk(root_dst_dir):
        logger.log("Checking folder {}...".format(dst_dir.replace(root_src_dir, "")), visit=True)

        src_dir = dst_dir.replace(root_dst_dir, root_src_dir, 1)

        for file in files:
            logger.log("Checking file {}...".format(file), visit=True)

            src_file = os.path.join(src_dir, file)
            dst_file = os.path.join(dst_dir, file)

            if not os.path.exists(src_file):
                logger.log("Removing file " + dst_file)
                if not log_only:
                    remove_file(dst_file, force_delete)

        if not os.path.exists(src_dir):
            logger.log("Removing folder and contents " + dst_dir)
            if not log_only:
                shutil.rmtree(dst_dir, onerror=remove_readonly if force_delete else None)


def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    for root, dirs, files in os.walk(path):
        for file_name in files:
            full_path = os.path.join(root, file_name)
            os.chmod(full_path, stat.S_IWRITE)
    func(path)


def remove_file(path, force_delete):
    try:
        os.remove(path)
    except PermissionError:
        if force_delete:
            os.chmod(path, stat.S_IWRITE)
            os.remove(path)
        else:
            raise


def error_occurred(logger):
    logger.log_error()
    message_box = ctypes.windll.user32.MessageBoxW(
        0,
        logger.error_message(),
        "Folder sync error",
        0x5)
    if message_box == 4:
        # retry clicked
        sync_folders(source_directory, destination_directory, logger, force_delete=True)


class Logger:
    def __init__(self, log_dir_path, print_actions=False, force_delete=False, log_visits=False):
        self.print_actions = print_actions
        self.force_delete = force_delete
        self.log_visits = log_visits

        self.most_recent_action = None

        time_str = time.strftime('%H.%M-%d-%b-%Y')
        self.log_file_name = "log-" + time_str + ".txt"
        self.error_file_name = "error-" + time_str + ".txt"

        if force_delete:
            self.log_file_name = self.log_file_name.replace(".txt", "-forced.txt")
            self.error_file_name = self.log_file_name.replace(".txt", "-forced.txt")

        self.log_dir_path = log_dir_path
        self.log_file = open(log_dir_path + self.log_file_name, "w")
        self.error_file = None

    def log(self, message, visit=False):
        if not visit:
            self.most_recent_action = message
        if not visit or self.log_visits:
            self.log_file.write(message + "\n\n")
            if self.print_actions:
                print(message)

    def log_error(self):
        self.error_file = self.error_file or open(self.log_dir_path + self.error_file_name, "w")
        self.error_file.write(traceback.format_exc())
        self.error_file.write("\nError while completing action%s:\n%s" %
                              (" (forced mode)" if self.force_delete else "",
                               self.most_recent_action))

    def error_message(self):
        force_instructions = "" if self.force_delete else "Press retry to rerun in forced mode."
        return "There was an error when syncing folder %s with %s. %s See error.txt for more details. \n\n" \
               "Error encountered while {}".format(source_directory, destination_directory, force_instructions,
                                                   self.most_recent_action.replace(source_directory, "")
                                           .replace(destination_directory, ""))

    def close(self):
        self.log_file.close()
        if self.error_file:
            self.error_file.close()


# Sample usage via cmd
# "C:\Program Files\Python33\python.exe" "C:\Users\Nic\Documents\Mine\Coding\file-copier\sync-folders.py" "C:\Users\Nic\Documents\Mine" "C:\Users\Nic\Google Drive\Mine" log force
# arguments expected: src_dir dst_dir [log] [force] [actions]
# log is optional. If present, no actions will be taken: only a log will be produced
# force is optional. If present, the program will make an attempt to delete or overwrite read-only files if found
# actions is optional. If present, the program will print its actions to standard output as it goes
#
if len(sys.argv) in (range(3, 7)):
    source_directory = sys.argv[1]
    if os.path.exists(source_directory):
        destination_directory = sys.argv[2]
        optional_args = sys.argv[3:]

        sync_folders(source_directory, destination_directory,
                     log_only='log' in optional_args,
                     force_delete='force' in optional_args,
                     print_actions='actions' in optional_args,
                     log_visits='log_visits' in optional_args or "visits" in optional_args
                     )

    else:
        raise NotADirectoryError(source_directory)
else:
    raise SyntaxError("Must have 2 arguments: an existing source directory and the desired destination directory. 2 "
                      "flags are optional.")
