from setuptools import setup, find_packages


setup(
    name='alfred-collector',
    version='0.1.dev',
    license='ISC',
    description='Collects results from alfred workers',
    url='https://github.com/alfredhq/alfred-collector',
    author='Alfred Developers',
    author_email='team@alfredhq.com',
    packages=find_packages(),
    install_requires=[
        'Markdown',
        'PyYAML',
        'alfred-db',
        'msgpack-python',
        'pyzmq',
    ],
    entry_points={
        'console_scripts': [
            'alfred-collector = alfred_collector.__main__:main',
        ],
    },
)
