from setuptools import setup, find_packages

setup(
    name='r-mail',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        'Jinja2',
        'rich',
        'python-dotenv',
        'cryptography',
        'beautifulsoup4',
        'markdown',
        'python-frontmatter',
        'aiosmtpd',            # Needed for the local debug server
        'PyYAML'               # Core YAML parser
    ],
    entry_points={
        'console_scripts': [
            'r-mail = rmail.cli:cli',
        ],
    },
)
