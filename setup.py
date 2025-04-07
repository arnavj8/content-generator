from setuptools import find_packages, setup
from typing import List

HYPEN_E_DOT = '-e .'

def get_requirements(file_path: str) -> List[str]:
    requirements = []
    with open(file_path, 'r') as file_obj:
        requirements = file_obj.readlines()
        requirements = [req.strip() for req in requirements]  # Use strip() to remove leading/trailing whitespace and newline characters

        if HYPEN_E_DOT in requirements:
            requirements.remove(HYPEN_E_DOT)
        
    print(f"Final requirements list: {requirements}")  # Add this for debugging
    
    return requirements


setup(
    name='src',
    packages=find_packages(),
    version='0.1.0',
    description='This Project aim to generate high quality content(blog,meme,image,video) on user text.',
    author='Gaurav Kumar Chaurasiya',
    license='',
    install_requires=get_requirements('requirements.txt')
)