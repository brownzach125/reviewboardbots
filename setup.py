from setuptools import setup

setup(name='reviewboardbots',
        version='0.1',
        description='The best ever review bot system',
        author='Zach and Tim',
        packages=['reviewboardbots'],
        install_requires=[
            'RBTools',
            'sh',
            'tinydb', 'yaml',
        ],
        )


