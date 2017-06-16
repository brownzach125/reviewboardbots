import yaml

if 'config' not in globals():
    with open('config.yaml', 'r') as data_file:
        config = yaml.load(data_file)
