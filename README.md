# TurtleBot3 Mapping and Autonomous Navigation

ROS2 Humble project for TurtleBot3 mapping and autonomous navigation in a custom Gazebo world.

## Dependencies

This repository contains only the custom package `my_robot_controller`.

TurtleBot3 packages are required to run the tasks. They can be installed from ROS packages:

```bash
sudo apt update
sudo apt install ros-humble-turtlebot3-gazebo ros-humble-turtlebot3-navigation2 ros-humble-turtlebot3-description
```

Alternatively, TurtleBot3 can be cloned into the workspace but it should not be committed to this repository:

```bash
cd ~/ws
git clone -b humble https://github.com/ROBOTIS-GIT/turtlebot3.git src/turtlebot3
```

Check that TurtleBot3 packages are available:

```bash
source /opt/ros/humble/setup.bash
ros2 pkg prefix turtlebot3_gazebo
ros2 pkg prefix turtlebot3_navigation2
```

## Build

Run inside Docker:

```bash
cd ~/ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select my_robot_controller
source ~/ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
```

## Task 1: Mapping

Launch mapping:

```bash
ros2 launch my_robot_controller start_mapping.launch.py
```

Custom world:

```text
src/my_robot_controller/worlds/Task1.world
```

Map files used in the project:

```text
src/my_robot_controller/maps/map/my_map.yaml
src/my_robot_controller/maps/map/my_map.pgm
```

## Task 2: Autonomous Navigation

Launch autonomous navigation:

```bash
ros2 launch my_robot_controller run_navigation.launch.py
```

This launch file starts:

* Gazebo with the custom world
* Navigation2 with the saved map
* Mission script with predefined goals

Main Task 2 files:

```text
src/my_robot_controller/my_robot_controller/navigation.py
src/my_robot_controller/launch/run_navigation.launch.py
src/my_robot_controller/worlds/Task1.world
src/my_robot_controller/maps/map/my_map.yaml
src/my_robot_controller/maps/map/my_map.pgm
```

## Notes

Do not commit generated folders or external TurtleBot3 source packages:

```text
build/
install/
log/
src/turtlebot3/
src/turtlebot3_simulations/
```


