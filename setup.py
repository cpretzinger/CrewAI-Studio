from setuptools import setup, find_packages

setup(
    name="crewai-studio",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "crewai",
        "python-dotenv",
        "zep-python",
        "agentops",
    ],
)
