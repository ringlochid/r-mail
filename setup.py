from setuptools import setup, find_packages

setup(
    name='r-mail',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'Jinja2',
        'rich',
        'python-dotenv',
        'cryptography',
        'beautifulsoup4',
        'markdown',
    ],
    entry_points={
        'console_scripts': [
            'r-mail = rmail.cli:cli',
        ],
    },
)
