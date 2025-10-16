import os
import getpass
from service import EncryptedStoreService


def prompt_path():
    path = input("Enter encrypted file path: ").strip()
    return path or "secrets.enc"


def prompt_master_password():
    return getpass.getpass("Enter master password: ")


def main():
    path = prompt_path()
    master_password = prompt_master_password()
    store = EncryptedStoreService(path, master_password)
    try:
        store.load()
    except Exception as e:
        print(f"Failed to load store: {e}")
        return

    print("Commands: list | get <key> | put <key> <value> | lock | exit")
    while True:
        cmd = input("> ").strip()
        if cmd == "exit":
            break
        elif cmd == "list":
            keys = store.list_keys()
            print("Stored keys:", ", ".join(keys))
        elif cmd.startswith("get "):
            _, key = cmd.split(" ", 1)
            value = store.get(key)
            if value is not None:
                print(f"{key} = {value}")
            else:
                print(f"No value for key '{key}'")
        elif cmd.startswith("put "):
            try:
                _, key, value = cmd.split(" ", 2)
                store.put(key, value)
                print(f"Stored {key}")
            except ValueError:
                print("Usage: put <key> <value>")
        elif cmd == "lock":
            store.lock()
            print("Store saved and locked.")
            break
        else:
            print("Unknown command.")


if __name__ == "__main__":
    main()
