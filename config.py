import json
import os

CONFIG_FOLDER = ".cache"
CONFIG_FILE = f'{CONFIG_FOLDER}/config.json'

def save_configurations(config):
    """
    Save configurations to a JSON file.
    """
    if not os.path.exists(CONFIG_FOLDER):
        os.makedirs(CONFIG_FOLDER)

    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file)

def load_configurations():
    """
    Load configurations from a JSON file.
    If the file doesn't exist or there's an error, return an empty dictionary.
    """
    try:
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}