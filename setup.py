from setuptools import setup, find_packages

setup(
    name="fastrub",
    version="2.4.3",
    author="seyyed mohamad hosein moosavi raja(01)",
    author_email="mohamadhosein159159@gmail.com",
    description="the library for rubika bots.",
    long_description=open("README.md",encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/OandONE/fast_rub",
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        "httpx==0.28.1", # fast_rub - sending requests
        "httpx[http2]", # fast_rub - sending requests
        "aiofiles==24.1.0", # fast_rub - saveing files async
        "filetype", # fork pyrubi
        "mutagen", # fork pyrubi
        "pycryptodome", # fork pyrubi
        "tqdm", # fork pyrubi
        "urllib3", # fork pyrubi
        "websocket-client" # fork pyrubi
    ],
    license="MIT"
)
