#!/usr/bin/env python3

import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav_msgs.msg import Odometry
from tier4_system_msgs.srv import ChangeOperationMode


class CarNavigationNode(Node):
    def __init__(self):
        super().__init__("navigation")
        self.get_logger().info("Mission planning started")

        # Publishers for initial and goal poses
        self.initial_pose_publisher = self.create_publisher(
            PoseWithCovarianceStamped,
            "/initialpose",
            10
        )

        self.goal_pose_publisher = self.create_publisher(
            PoseStamped,
            "/planning/mission_planning/goal",
            10
        )

        # Subscriber for vehicle position
        self.odom_listener = self.create_subscription(
            Odometry,
            "/localization/kinematic_state",
            self.odom_callback,
            10
        )

        # Service client for changing operation mode
        self.change_mode_srv = self.create_client(
            ChangeOperationMode,
            "/system/operation_mode/change_operation_mode"
        )
        self.change_mode_req = ChangeOperationMode.Request()

        # Current goal index
        self.current_goal_index = 0

        # Initialize pose and goals
        self.setup_initial_pose()
        self.setup_goals()

    def setup_initial_pose(self):
        initial_pose = PoseWithCovarianceStamped()
        initial_pose.header.frame_id = "map"
        initial_pose.pose.pose.position.x = 3636.64697265625
        initial_pose.pose.pose.position.y = 73598.015625
        initial_pose.pose.pose.position.z = 0.0
        initial_pose.pose.pose.orientation.x = 0.0
        initial_pose.pose.pose.orientation.y = 0.0
        initial_pose.pose.pose.orientation.z = 0.7502029596277497
        initial_pose.pose.pose.orientation.w = 0.6612076219809969

        time.sleep(10)
        self.initial_pose_publisher.publish(initial_pose)
        self.get_logger().info("Initial pose published")

    def setup_goals(self):
        self.goal_poses = [
            {'x': 3694.277099609375, 'y': 73737.375, 'xx': 0.0, 'yy': 0.0, 'zz': -0.5171265486828789, 'w': 0.8559089511433643},
            {'x': 3838.013916015625, 'y': 73754.984375, 'xx': 0.0, 'yy': 0.0, 'zz': 0.8572754619146257, 'w': 0.5148580215933956},
            {'x': 3717.553466796875, 'y': 73767.7890625, 'xx': 0.0, 'yy': 0.0, 'zz': -0.9677607020846777, 'w': 0.2518714424077723},
            {'x': 3902.525146484375, 'y': 73785.7265625, 'xx': 0.0, 'yy': 0.0, 'zz': 0.8659264856661136, 'w': 0.5001712920809568}
        ]
        self.publish_goal()

    def publish_goal(self):
        goal = self.goal_poses[self.current_goal_index]

        pose_msg = PoseStamped()
        pose_msg.header.frame_id = "map"
        pose_msg.pose.position.x = goal["x"]
        pose_msg.pose.position.y = goal["y"]
        pose_msg.pose.position.z = 0.0
        pose_msg.pose.orientation.x = goal["xx"]
        pose_msg.pose.orientation.y = goal["yy"]
        pose_msg.pose.orientation.z = goal["zz"]
        pose_msg.pose.orientation.w = goal["w"]

        self.goal_pose_publisher.publish(pose_msg)
        self.get_logger().info(f"Published goal: {self.current_goal_index}")

        time.sleep(5)
        self.send_request()

    def odom_callback(self, msg: Odometry):
        current_pose = msg.pose.pose
        goal_pose = self.goal_poses[self.current_goal_index]

        distance_to_goal = (
            (
                current_pose.position.x - goal_pose["x"]
            ) ** 2
            +
            (
                current_pose.position.y - goal_pose["y"]
            ) ** 2
        ) ** 0.5

        if distance_to_goal < 0.5:
            self.publish_next_goal()

    def publish_next_goal(self):
        if self.current_goal_index < len(self.goal_poses) - 1:
            self.current_goal_index += 1
            self.publish_goal()
        else:
            self.get_logger().info("All goals reached!")
            self.stop()

    def send_request(self):
        self.change_mode_req.mode = 2  # Enable autonomous mode
        self.change_mode_srv.call_async(self.change_mode_req)

    def stop(self):
        self.get_logger().info("Stopping the node")
        rclpy.shutdown()
        raise KeyboardInterrupt


def main(args=None):
    rclpy.init(args=args)
    node = CarNavigationNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()