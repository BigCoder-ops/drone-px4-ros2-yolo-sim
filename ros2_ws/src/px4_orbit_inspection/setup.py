from glob import glob
import os
from setuptools import find_packages, setup

package_name = 'px4_orbit_inspection'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Abdellah TNOURJI',
    maintainer_email='abdellah.tnourji@um6p.ma',
    description='PX4 Orbit Inspection educational mission',
    license='Apache-2.0',
    entry_points={'console_scripts': [
        'orbit_controller = px4_orbit_inspection.orbit_controller:main',
        'mission_monitor = px4_orbit_inspection.mission_monitor:main',
    ]},
)