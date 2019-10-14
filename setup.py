from setuptools import setup, find_packages

with open('requirements.txt') as fp:
    install_requires = fp.read()

setup(
    name='remote_event_bundle',
    packages=find_packages(),
    version='1.4',
    description='Remote events support for applauncher',
    author='Alvaro Garcia Gomez',
    author_email='maxpowel@gmail.com',
    url='https://github.com/applauncher-team/remote_event_bundle',
    download_url='https://github.com/applauncher-team/remote_event_bundle/archive/master.zip',
    keywords=['applauncher', 'events', 'remote', 'redis', 'kafka', 'mqtt'],
    classifiers=['Topic :: Adaptive Technologies', 'Topic :: Software Development', 'Topic :: System',
                 'Topic :: Utilities'],
    install_requires=install_requires
)
