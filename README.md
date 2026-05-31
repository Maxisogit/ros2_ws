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

# Task 4: AV Validation with Scenario Simulator V2

## Description

Task 4 uses Autoware Scenario Simulator V2 to validate the behavior of an Ego vehicle in an interactive traffic scenario.

The scenario includes:

* Ego vehicle controlled by Autoware
* two NPC vehicles
* four-way intersection interaction
* parameterized scenario using `ScenarioModifiers`
* batch simulation for domain analysis

## Required files

The scenario YAML files are stored outside the repository in the Autoware map folder:

```text
~/autoware_map/scenarios/
```

The final scenario file for the repository should be copied to:

```text
scenario/Task4.yaml
```

Main Task 4 files used during testing:

```text
~/autoware_map/scenarios/Task4.yaml
~/autoware_map/scenarios/Task4_base_passed.yaml
~/autoware_map/scenarios/Task4_domain_100.yaml
~/autoware_map/scenarios/Task4_domain_100_all_step4.yaml
~/autoware_map/scenarios/Task4_batch_A.yaml
~/autoware_map/scenarios/Task4_batch_B.yaml
~/autoware_map/scenarios/Task4_batch_C.yaml
~/autoware_map/scenarios/Task4_batch_D.yaml
~/autoware_map/scenarios/Task4_mutated.yaml
```

File usage:

```text
Task4_base_passed.yaml
```

Base scenario with Ego vehicle and two NPC vehicles.

```text
Task4.yaml
```

Stable parameterized scenario used as the main Task 4 submission file.

```text
Task4_domain_100.yaml
```

Domain-analysis scenario with 100 parameter combinations.

```text
Task4_batch_A.yaml
Task4_batch_B.yaml
Task4_batch_C.yaml
Task4_batch_D.yaml
```

Separated batch files used for additional batch testing.

## Map

The map must be stored on the host machine at:

```text
~/autoware_map/task4_map/
```

The map folder should contain files such as:

```text
lanelet2_map.osm
lanelet2_map_provider.osm.yaml
map.map_publisher.yaml
pointcloud_map.pcd
global_map_center.pcd.yaml
```

The scenario expects the Lanelet2 map inside Docker at:

```text
/autoware_map/task4_map/lanelet2_map.osm
```

The YAML scenario contains this map path:

```yaml
RoadNetwork:
  LogicFile:
    filepath: /autoware_map/task4_map/lanelet2_map.osm
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

If the container is already running:

```bash
docker exec -it autoware_mohsen bash
```

## Prepare the environment inside Docker

Inside the Docker container:

```bash
cd /ros2_ws
source /opt/ros/humble/setup.bash
source /autoware/install/setup.bash
```

Some CUDA/TensorRT warnings may appear during sourcing. They did not prevent the scenario from running.

## Clean old processes before running

Before starting a new simulation, stop old Autoware and simulator processes:

```bash
pkill -f scenario_test_runner
pkill -f openscenario
pkill -f rviz2
pkill -f component_container
pkill -f autoware
pkill -f simple_sensor_simulator
pkill -f traffic_simulator
```

Check that no old processes are still running:

```bash
ps aux | grep -E "scenario_test_runner|openscenario|rviz2|component_container|autoware|traffic_simulator"
```

Only the `grep` process should remain.

## Copy final scenario to the repository

Create the repository scenario folder and copy the final Task 4 YAML file:

```bash
mkdir -p /ros2_ws/scenario
cp /autoware_map/scenarios/Task4.yaml /ros2_ws/scenario/Task4.yaml
```

## Run the base scenario

```bash
rm -rf /autoware_map/scenario_results
mkdir -p /autoware_map/scenario_results

ros2 launch scenario_test_runner scenario_test_runner.launch.py \
architecture_type:=awf/universe \
record:=false \
scenario:=/autoware_map/scenarios/Task4_base_passed.yaml \
sensor_model:=sample_sensor_kit \
vehicle_model:=sample_vehicle \
output_directory:=/autoware_map/scenario_results \
global_real_time_factor:=1.0 \
global_timeout:=600 \
initialize_duration:=120 \
launch_rviz:=false \
use_sim_time:=true 2>&1 | tee /autoware_map/scenario_results/task4_base.log
```

## Run the stable parameterized scenario

```bash
rm -rf /autoware_map/final_check_9
mkdir -p /autoware_map/final_check_9

ros2 launch scenario_test_runner scenario_test_runner.launch.py \
architecture_type:=awf/universe \
record:=false \
scenario:=/autoware_map/scenarios/Task4.yaml \
sensor_model:=sample_sensor_kit \
vehicle_model:=sample_vehicle \
output_directory:=/autoware_map/final_check_9 \
global_real_time_factor:=1.0 \
global_timeout:=600 \
initialize_duration:=120 \
launch_rviz:=false \
use_sim_time:=true 2>&1 | tee /autoware_map/final_check_9/task4_final_check_9.log
```

## Run the 100-scenario domain analysis

```bash
rm -rf /autoware_map/results_domain_100
mkdir -p /autoware_map/results_domain_100

ros2 launch scenario_test_runner scenario_test_runner.launch.py \
architecture_type:=awf/universe \
record:=false \
scenario:=/autoware_map/scenarios/Task4_domain_100.yaml \
sensor_model:=sample_sensor_kit \
vehicle_model:=sample_vehicle \
output_directory:=/autoware_map/results_domain_100 \
global_real_time_factor:=1.0 \
global_timeout:=600 \
initialize_duration:=120 \
launch_rviz:=false \
use_sim_time:=true 2>&1 | tee /autoware_map/results_domain_100/task4_domain_100.log
```

## Run separated batch files

Example for Batch A:

```bash
rm -rf /autoware_map/results_A
mkdir -p /autoware_map/results_A

ros2 launch scenario_test_runner scenario_test_runner.launch.py \
architecture_type:=awf/universe \
record:=false \
scenario:=/autoware_map/scenarios/Task4_batch_A.yaml \
sensor_model:=sample_sensor_kit \
vehicle_model:=sample_vehicle \
output_directory:=/autoware_map/results_A \
global_real_time_factor:=1.0 \
global_timeout:=600 \
initialize_duration:=120 \
launch_rviz:=false \
use_sim_time:=true 2>&1 | tee /autoware_map/results_A/task4_batch_A.log
```

For other batches, replace `A` with `B`, `C`, or `D`.

## Check results

Check the JUnit result file:

```bash
grep -n "testsuites\|testsuite\|failure\|error\|testcase" \
/autoware_map/results_domain_100/scenario_test_runner/result.junit.xml
```

Count generated OpenSCENARIO files:

```bash
find /autoware_map/results_domain_100 -name "*.xosc" | wc -l
```

Search important log messages:

```bash
grep -ni "Passed\|SimulationFailure\|AutowareError\|EMERGENCY\|PLANNING\|INITIALIZING\|duplicated\|Collision\|collision\|Failure\|Error" \
/autoware_map/results_domain_100/task4_domain_100.log | tail -150
```

## Notes

For stable batch simulation, use:

```text
global_real_time_factor:=1.0
```

Higher values caused unstable behavior during batch runs.

Use:

```text
launch_rviz:=false
```

for batch simulations to reduce load and avoid duplicated RViz/node issues.

Do not commit generated simulation result folders unless required:

```text
~/autoware_map/results_domain_100/
~/autoware_map/results_A/
~/autoware_map/results_B/
~/autoware_map/scenario_results/
```

The map folder should also not be committed:

```text
~/autoware_map/task4_map/
```
