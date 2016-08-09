from setuptools import setup

setup(
    name='docker-getrun',
    version='0.0.1',
    py_modules=['getrun'],
    description='Compose docker run command for running container',
    author='Roman Komkov',
    author_email='roman@komkov.co',
    url='https://github.com/decayofmind/docker-getrun/',
    download_url = 'https://github.com/decayofmind/docker-getrun/tarball/0.0.1',
    keywords=['docker'],
    entry_points='''
        [console_scripts]
        getrun=getrun:main
    '''
)
