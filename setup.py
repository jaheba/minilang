from setuptools import setup

setup(
    name="minilang",
    packages=['minilang', 'rpin'],
    version="0.0.1",
    author="Jasper Schulz",
    author_email="jasper.b.schulz@gmail.com",
    install_requires=['ply', 'click'],
)