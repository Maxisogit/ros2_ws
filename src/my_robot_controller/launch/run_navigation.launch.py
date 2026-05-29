#!/usr/bin/env python3

import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_my_robot = get_package_share_directory("my_robot_controller")
    pkg_turtlebot3_nav2 = get_package_share_directory("turtlebot3_navigation2")

    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    map_dir = os.path.join(
        pkg_my_robot,
        "maps",
        "map",
        "my_map.yaml"
    )

    params_file = os.path.join(
        pkg_turtlebot3_nav2,
        "param",
        "humble",
        "burger.yaml"
    )

    gazebo_world = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                pkg_my_robot,
                "launch",
                "Task1_world.launch.py"
            )
        )
    )

    navigation_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                pkg_turtlebot3_nav2,
                "launch",
                "navigation2.launch.py"
            )
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "map": map_dir,
            "params_file": params_file,
        }.items()
    )

    goal_pose_publisher = Node(
        package="my_robot_controller",
        executable="navigation",
        name="navigation"
    )

    return LaunchDescription([
        gazebo_world,
        navigation_node,
        goal_pose_publisher
    ])