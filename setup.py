from setuptools import setup
import os

setup(name='reviewboardbots',
        version='0.1',
        description='The best ever review bot system',
        author='Zach and Tim',
        install_requires=[
            'RBTools',
            'sh',
            'tinydb', 'pyyaml',
        ],
        )

os.mkdir('botfood_folder')
