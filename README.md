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
# Task 3: Autoware Ego Vehicle Autonomous Navigation

For Task 3 with Autoware, if TurtleBot3 packages are present in the workspace, create COLCON_IGNORE files before building:
```
touch src/turtlebot3/COLCON_IGNORE
touch src/turtlebot3_simulations/COLCON_IGNORE
```
This prevents TurtleBot3 packages from being built in the Autoware Docker environment.

For Task 1 and Task 2, remove these files before building or running TurtleBot tasks:
```
rm -f src/turtlebot3/COLCON_IGNORE
rm -f src/turtlebot3_simulations/COLCON_IGNORE
```
## Description

Task 3 uses Autoware to navigate an Ego vehicle autonomously in the sample planning map. The custom ROS2 node publishes the initial pose, sends multiple goal poses, monitors the current vehicle position, and switches to the next goal when the current one is reached.

## Required files

The following files are used for Task 3:

```text
src/my_robot_controller/my_robot_controller/aw_navigation.py
src/my_robot_controller/launch/car_nav.launch.py
src/my_robot_controller/setup.py
```

The executable entry point in `setup.py` is:

```python
"av_nav = my_robot_controller.aw_navigation:main"
```

## Requirements

Task 3 requires the Autoware Docker image and the Autoware planning map.

The Docker image used for this task is:

```text
mohsen_aw:full
```

The map must be stored on the host machine at:

```text
~/autoware_map/sample-map-planning/
```

The map folder should contain files such as:

```text
lanelet2_map.osm
map_config.yaml
map_projector_info.yaml
pointcloud_map.pcd
```

The map is not included in this repository.

## Start the Autoware Docker container

From the host Ubuntu system, allow Docker to use the display:

```bash
xhost +local:docker
xhost +local:root
```

Start the Autoware container:

```bash
docker run -it --rm --privileged \
--name autoware_mohsen \
--env=DISPLAY=$DISPLAY \
--env=QT_X11_NO_MITSHM=1 \
--env=LIBGL_ALWAYS_SOFTWARE=1 \
--env=LIBGL_DRI3_DISABLE=1 \
-v /tmp/.X11-unix:/tmp/.X11-unix \
-v $HOME/ros2_ws:/ros2_ws \
-v $HOME/autoware_map:/autoware_map \
--workdir /ros2_ws \
mohsen_aw:full bash
```

## Prepare the environment inside Docker

Inside the Docker container, create or check `/ros2_ws/setup.bash`:

```bash
cat > /ros2_ws/setup.bash << 'EOF'
#!/bin/bash
source /opt/ros/humble/setup.bash
source /autoware/install/setup.bash
source /ros2_ws/install/setup.bash
```
## Notes

Do not commit generated folders, Docker image files, Autoware map files, or local build-control files:

```text
build/
install/
log/
~/autoware_map/
mohsen_aw.tar
COLCON_IGNORE
```



