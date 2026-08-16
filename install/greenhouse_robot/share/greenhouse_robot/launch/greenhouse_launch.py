#!/usr/bin/env python3
"""
Master launch file for the Autonomous Greenhouse Robot.
Phase 6: Webots + Robot + EKF + SLAM + Nav2 + RViz2
"""
import os
import launch
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler, ExecuteProcess, TimerAction
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from webots_ros2_driver.webots_launcher import WebotsLauncher
from webots_ros2_driver.webots_controller import WebotsController
from webots_ros2_driver.wait_for_controller_connection import WaitForControllerConnection

def generate_launch_description():
    package_dir = get_package_share_directory('greenhouse_robot')
    use_sim_time = LaunchConfiguration('use_sim_time', default=True)

    world_file = os.path.join(package_dir, 'worlds', 'greenhouse.wbt')
    urdf_file = os.path.join(package_dir, 'resource', 'greenhouse_turtlebot.urdf')
    ros2_control_params = os.path.join(package_dir, 'resource', 'ros2control.yml')
    ekf_config = os.path.join(package_dir, 'config', 'ekf.yaml')
    slam_config = os.path.join(package_dir, 'config', 'slam_toolbox.yaml')
    nav2_config = os.path.join(package_dir, 'config', 'nav2_params.yaml')
    rviz_config = os.path.join(package_dir, 'rviz', 'greenhouse.rviz')

    # ==================== WEBOTS ====================
    webots = WebotsLauncher(world=world_file, mode='realtime', ros2_supervisor=True)

    robot_state_publisher = Node(
        package='robot_state_publisher', executable='robot_state_publisher', output='screen',
        parameters=[{
            'robot_description': '<robot name=""><link name=""/></robot>',
            'use_sim_time': use_sim_time,
        }],
    )

    footprint_publisher = Node(
        package='tf2_ros', executable='static_transform_publisher', output='screen',
        arguments=['--x', '0', '--y', '0', '--z', '0',
                   '--roll', '0', '--pitch', '0', '--yaw', '0',
                   '--frame-id', 'base_link', '--child-frame-id', 'base_footprint'],
        parameters=[{'use_sim_time': use_sim_time}],
    )

    camera_tf_publisher = Node(
        package='tf2_ros', executable='static_transform_publisher', output='screen',
        arguments=['--x', '0.05', '--y', '0', '--z', '0.04',
                   '--roll', '0', '--pitch', '0', '--yaw', '0',
                   '--frame-id', 'base_link', '--child-frame-id', 'camera_link'],
        parameters=[{'use_sim_time': use_sim_time}],
    )

    lidar_tf_publisher = Node(
        package='tf2_ros', executable='static_transform_publisher', output='screen',
        arguments=['--x', '-0.032', '--y', '0', '--z', '0.172',
                   '--roll', '0', '--pitch', '0', '--yaw', '0',
                   '--frame-id', 'base_link', '--child-frame-id', 'LDS-01'],
        parameters=[{'use_sim_time': use_sim_time}],
    )

    # ==================== ROBOT DRIVER ====================
    turtlebot_driver = WebotsController(
        robot_name='TurtleBot3Burger',
        parameters=[
            {'robot_description': urdf_file,
             'use_sim_time': use_sim_time,
             'set_robot_state_publisher': True},
            ros2_control_params
        ],
        remappings=[
            ('/diffdrive_controller/cmd_vel', '/cmd_vel'),
            ('/diffdrive_controller/odom', '/odom'),
        ],
        respawn=True
    )

    controller_manager_timeout = ['--controller-manager-timeout', '50']

    diffdrive_controller_spawner = Node(
        package='controller_manager', executable='spawner', output='screen',
        arguments=['diffdrive_controller'] + controller_manager_timeout,
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager', executable='spawner', output='screen',
        arguments=['joint_state_broadcaster'] + controller_manager_timeout,
    )

    # ==================== EKF (Phase 3) ====================
    ekf_node = Node(
        package='robot_localization', executable='ekf_node',
        name='ekf_filter_node', output='screen',
        parameters=[ekf_config],
    )

    # ==================== SLAM (Phase 4) ====================
    slam_node = Node(
        package='slam_toolbox', executable='async_slam_toolbox_node',
        name='slam_toolbox', output='screen',
        parameters=[slam_config],
    )

    activate_slam = ExecuteProcess(
        cmd=['bash', '-c',
             'sleep 15 && '
             'echo "=== Waiting for SLAM to be ready... ===" && '
             'for i in $(seq 1 30); do '
             '  /opt/ros/jazzy/bin/ros2 lifecycle set /slam_toolbox configure 2>/dev/null && break; '
             '  echo "  Retry configure $i/30..."; sleep 2; '
             'done && '
             'sleep 2 && '
             'for i in $(seq 1 30); do '
             '  /opt/ros/jazzy/bin/ros2 lifecycle set /slam_toolbox activate 2>/dev/null && break; '
             '  echo "  Retry activate $i/30..."; sleep 2; '
             'done && '
             'echo "=== SLAM ACTIVATED ==="'],
        output='screen',
    )

    # ==================== NAV2 (Phase 6) ====================
    twist_relay_node = Node(
        package='greenhouse_robot', executable='twist_relay',
        name='twist_relay', output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    compass_to_imu_node = Node(
        package='greenhouse_robot', executable='compass_to_imu',
        name='compass_to_imu', output='screen',
        parameters=[{'use_sim_time': use_sim_time}],

    )

    greenhouse_data_visualizer_node = Node(
        package='greenhouse_robot', executable='greenhouse_data_visualizer',
        name='greenhouse_data_visualizer', output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )
    controller_server = Node(
        package='nav2_controller', executable='controller_server',
        name='controller_server', output='screen',
        parameters=[nav2_config],
        remappings=[('/cmd_vel', '/cmd_vel_nav')],
    )

    planner_server = Node(
        package='nav2_planner', executable='planner_server',
        name='planner_server', output='screen',
        parameters=[nav2_config],
    )

    smoother_server = Node(
        package='nav2_smoother', executable='smoother_server',
        name='smoother_server', output='screen',
        parameters=[nav2_config],
    )

    behavior_server = Node(
        package='nav2_behaviors', executable='behavior_server',
        name='behavior_server', output='screen',
        parameters=[nav2_config],
        remappings=[('/cmd_vel', '/cmd_vel_nav')],
    )

    bt_navigator = Node(
        package='nav2_bt_navigator', executable='bt_navigator',
        name='bt_navigator', output='screen',
        parameters=[nav2_config],
    )

    waypoint_follower = Node(
        package='nav2_waypoint_follower', executable='waypoint_follower',
        name='waypoint_follower', output='screen',
        parameters=[nav2_config],
    )

    nav2_lifecycle_manager = Node(
        package='nav2_lifecycle_manager', executable='lifecycle_manager',
        name='lifecycle_manager_navigation', output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'autostart': True,
            'bond_timeout': 0.0,
            'node_names': [
                'controller_server',
                'planner_server',
                'smoother_server',
                'behavior_server',
                'bt_navigator',
                'waypoint_follower',
            ],
        }],
    )

    # Delay Nav2 until SLAM is ready (25s)
    nav2_delayed = TimerAction(
        period=25.0,
        actions=[
            twist_relay_node,
            compass_to_imu_node,
            greenhouse_data_visualizer_node,
            controller_server,
            planner_server,
            smoother_server,
            behavior_server,
            bt_navigator,
            waypoint_follower,
            nav2_lifecycle_manager,
        ],
    )

    # ==================== RVIZ2 ====================
    rviz_node = Node(
        package='rviz2', executable='rviz2', name='rviz2', output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
    )

    # ==================== SEQUENCING ====================
    waiting_nodes = WaitForControllerConnection(
        target_driver=turtlebot_driver,
        nodes_to_start=[
            diffdrive_controller_spawner,
            joint_state_broadcaster_spawner,
            ekf_node,
            slam_node,
            activate_slam,
            rviz_node,
            nav2_delayed,
        ]
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        webots, webots._supervisor,
        robot_state_publisher, footprint_publisher, camera_tf_publisher, lidar_tf_publisher,
        turtlebot_driver, waiting_nodes,
        RegisterEventHandler(event_handler=OnProcessExit(
            target_action=webots,
            on_exit=[launch.actions.EmitEvent(event=Shutdown())],
        )),
    ])
