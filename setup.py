from setuptools import setup, find_packages

setup(
    name="fastrub",
    version="2.6.8",
    author="seyyed mohamad hosein moosavi raja(01)",
    author_email="mohamadhosein159159@gmail.com",
    description="The fastest library for writing Rubika messenger bots both synchronously and asynchronously ⚡",
    long_description=open("README.md",encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/OandONE/fast_rub",
    packages=find_packages(),
    python_requires='>=3.10',
    install_requires=[
        "httpx[http2]==0.28.1", # fast_rub - NetWork
        "aiohttp==3.8.3" , # fast_rub - Network(Upload Streem file)
        "aiofiles==24.1.0", # fast_rub - saveing files async
        "filetype", # fork pyrubi
        "mutagen", # fork pyrubi
        "pycryptodome", # fork pyrubi
        "tqdm", # fork pyrubi
        "websocket-client" # fork pyrubi
    ],
    license="MIT"
)