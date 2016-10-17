import logging
import sys
import time

from watchdog.events import FileSystemEventHandler

from watchdog.observers import Observer

# the time a file must be left untouched before events are synced, in seconds.
CHANGE_WAIT_PERIOD = 30

class EventTimer:
    def __init__(self, event):
        self.event = event
        self.time = time.time()


class MyEventHandler(FileSystemEventHandler):

    def __init__(self):
        self.recent_events = dict()

    def on_any_event(self, event):
        self.recent_events[event.src_path] = EventTimer(event)
        # print(self.recent_events)

    # def on_moved(self, event):
    #     what = 'directory' if event.is_directory else 'file'
    #     logging.info("Moved %s: from %s to %s", what, event.src_path,
    #                  event.dest_path)
    #
    # def on_created(self, event):
    #     what = 'directory' if event.is_directory else 'file'
    #     logging.info("Created %s: %s", what, event.src_path)
    #
    # def on_deleted(self, event):
    #     what = 'directory' if event.is_directory else 'file'
    #     logging.info("Deleted %s: %s", what, event.src_path)
    #
    # def on_modified(self, event):
    #     what = 'directory' if event.is_directory else 'file'
    #     logging.info("Modified %s: %s", what, event.src_path)


def sync_changes(event_handler):
    print("\nSyncing changes")
    for path_changed, change in event_handler.recent_events.items():
        time_since_event = time.time() - change.time

        if time_since_event > CHANGE_WAIT_PERIOD:
            if change.event.event_type == "deleted":
                print("Deleting ", end='')
            elif change.event.event_type == "created":
                print("Creating ", end='')
            elif change.event.event_type == "modified":
                print("Updating ", end='')
            elif change.event.event_type == "moved":
                print("Moving ", end='')
            print(path_changed)

        print("Time since event: %0.1f seconds" % time_since_event)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    path = sys.argv[1] if len(sys.argv) > 1 else "C:\\Users\\Nic\\Documents\\Mine"
    event_handler = MyEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(10)
            sync_changes(event_handler)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
