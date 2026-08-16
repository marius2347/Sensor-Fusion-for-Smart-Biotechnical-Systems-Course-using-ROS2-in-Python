from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'greenhouse_robot'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*')),
        (os.path.join('share', package_name, 'resource'), glob('resource/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='marius',
    maintainer_email='mariusc0023@gmail.com',
    description='Autonomous Greenhouse Robot for Mapping and Inspection',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'twist_relay = greenhouse_robot.twist_relay:main',
            'compass_to_imu = greenhouse_robot.compass_to_imu:main',
            'greenhouse_data_visualizer = greenhouse_robot.greenhouse_data_visualizer:main',],
    },
)
