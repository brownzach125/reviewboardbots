import yaml

if 'config' not in globals():
    # TODO this should be a command line param
    with open('config.yaml', 'r') as data_file:
        config = yaml.load(data_file)
        # In the config file bots are a list for ease of use, but here we want a dictionary.
        config['bots'] = {bot['name']: bot for bot in config['bots']}
