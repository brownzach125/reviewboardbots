import yaml

if 'config' not in globals():
    # TODO this should be a command line param
    with open('config.yaml', 'r') as data_file:
        config = yaml.load(data_file)
