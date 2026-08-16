import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/marius/greenhouse_robot_ws/install/greenhouse_robot'
