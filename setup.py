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

bot_food_folder = 'botfood_folder'
if not os.path.isdir(bot_food_folder):  # if folder does not exist,
    os.mkdir(bot_food_folder)           # create it
