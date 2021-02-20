from setuptools import setup

url = 'https://gitlab.com/rendaw/trezor-gpg-pinentry-tk'
GEN_version = '0.0.10'

try:
    with open('readme.md', 'r') as readme_source:
        readme = readme_source.read()
except FileNotFoundError:
    readme = ''

setup(
    name='trezor-gpg-pinentry-tk',
    version=GEN_version,
    author='rendaw',
    author_email='spoo@zarbosoft.com',
    url=url,
    download_url=url + '/tarball/v{}'.format(GEN_version),
    license='BSD',
    description='A pinentry for GPG with Trezor',
    long_description=readme,
    classifiers=[
        'License :: OSI Approved :: BSD License',
    ],
    install_requires=[],
    py_modules=['trezor_gpg_pinentry_tk'],
    entry_points={
        'console_scripts': [
            'trezor-gpg-pinentry-tk = trezor_gpg_pinentry_tk:main',
        ],
    },
)
