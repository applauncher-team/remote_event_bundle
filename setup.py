from setuptools import setup

with open('requirements.txt') as fp:
    install_requires = fp.read()

setup(
    name='remote_event_bundle',
    packages=['remote_event_bundle'],
    version='0.2',
    description='Remote events support for applauncher',
    author='Alvaro Garcia Gomez',
    author_email='maxpowel@gmail.com',
    url='https://github.com/applauncher-team/remote_event_bundle',
    download_url='https://github.com/applauncher-team/remote_event_bundle/archive/master.zip',
    keywords=['applauncher', 'events', 'remote'],
    classifiers=['Topic :: Adaptive Technologies', 'Topic :: Software Development', 'Topic :: System',
                 'Topic :: Utilities'],
    install_requires=install_requires
)
