from setuptools import setup, find_packages

setup(
    name="fast_rub",
    version="1.0",
    author="seyyed mohamad hosein moosavi raja(01)",
    author_email="mohamadhosein159159@gmail.com",
    description="the library for rubika bots.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/OandONE/fast_rub",
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=["httpx==0.28.1","colorama==0.4.6"],
    license="MIT"
)
