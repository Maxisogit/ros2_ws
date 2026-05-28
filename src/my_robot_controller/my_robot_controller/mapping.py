#!/usr/bin/env python3

import math
import random
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry


class TurtlebotMappingNode(Node):
    def __init__(self):
        super().__init__("mapping_node")

        self.get_logger().info("Mapping node with no-hit random exploration started.")

        self.cmd_pub = self.create_publisher(Twist, "/cmd_vel", 10)

        self.scan_sub = self.create_subscription(
            LaserScan,
            "/scan",
            self.scan_callback,
            10
        )

        self.odom_sub = self.create_subscription(
            Odometry,
            "/odom",
            self.odom_callback,
            10
        )

        # Это не таймер остановки.
        # Он просто запускает control_loop каждые 0.1 секунды.
        self.timer = self.create_timer(0.1, self.control_loop)

        self.last_scan = None
        self.current_yaw = None

        # Current velocities
        self.current_linear = 0.0
        self.current_angular = 0.0

        # Target velocities
        self.target_linear = 0.0
        self.target_angular = 0.0

        # Скорости для картографирования
        self.max_forward_speed = 0.08
        self.min_forward_speed = 0.025
        self.max_turn_speed = 0.25

        # Плавность движения
        self.max_linear_accel = 0.08
        self.max_angular_accel = 0.45

        # Безопасные расстояния
        self.front_danger_distance = 0.35
        self.front_slow_distance = 0.80
        self.side_danger_distance = 0.25

        # Поиск свободного направления
        self.search_angle_deg = 120
        self.sector_width_deg = 12
        self.safe_distance = 0.75

        # Разворот, если робот упёрся в стену
        self.state = "EXPLORE"
        self.recovery_start_yaw = None
        self.recovery_direction = 1
        self.recovery_angle = math.radians(90)
        self.recovery_tolerance = math.radians(5)
        self.recovery_turn_speed = 0.18

        # Случайное исследование центра комнат
        self.random_explore_active = False
        self.random_explore_angle_deg = 0.0
        self.random_explore_end_time = 0.0
        self.next_random_explore_time = self.now_sec() + 5.0

        self.random_explore_min_interval = 4.0
        self.random_explore_max_interval = 8.0
        self.random_explore_duration = 1.6
        self.random_explore_max_angle_deg = 75

        # Сколько лучей в секторе должны НЕ видеть объект
        self.no_hit_ratio_required = 0.60

    def now_sec(self):
        return self.get_clock().now().nanoseconds / 1e9

    def scan_callback(self, scan: LaserScan):
        self.last_scan = scan

    def odom_callback(self, msg: Odometry):
        q = msg.pose.pose.orientation

        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)

        self.current_yaw = math.atan2(siny_cosp, cosy_cosp)

    def normalize_angle(self, angle):
        while angle > math.pi:
            angle -= 2.0 * math.pi
        while angle < -math.pi:
            angle += 2.0 * math.pi
        return angle

    def clamp(self, value, min_value, max_value):
        return max(min_value, min(value, max_value))

    def limit_change(self, current, target, max_change):
        if target > current + max_change:
            return current + max_change
        elif target < current - max_change:
            return current - max_change
        return target

    def get_sector_min(self, scan: LaserScan, center_deg: float, width_deg: float):
        center_rad = math.radians(center_deg)
        half_width_rad = math.radians(width_deg / 2.0)

        valid_ranges = []

        for i, distance in enumerate(scan.ranges):
            if math.isnan(distance):
                continue

            # Если луч ничего не увидел, считаем это максимальной дальностью
            if math.isinf(distance):
                distance = scan.range_max

            if distance < scan.range_min or distance > scan.range_max:
                continue

            angle = scan.angle_min + i * scan.angle_increment
            angle_diff = self.normalize_angle(angle - center_rad)

            if abs(angle_diff) <= half_width_rad:
                valid_ranges.append(distance)

        if not valid_ranges:
            return scan.range_max

        return min(valid_ranges)

    def sector_has_no_hits(self, scan: LaserScan, center_deg: float, width_deg: float):
        """
        True, если большинство лучей в секторе НЕ касаются объектов.
        То есть лучи уходят в пустоту: inf или почти range_max.
        """

        center_rad = math.radians(center_deg)
        half_width_rad = math.radians(width_deg / 2.0)

        total_rays = 0
        no_hit_rays = 0

        for i, distance in enumerate(scan.ranges):
            if math.isnan(distance):
                continue

            angle = scan.angle_min + i * scan.angle_increment
            angle_diff = self.normalize_angle(angle - center_rad)

            if abs(angle_diff) <= half_width_rad:
                total_rays += 1

                # Луч не коснулся стены/объекта
                if math.isinf(distance) or distance >= scan.range_max * 0.95:
                    no_hit_rays += 1

        if total_rays == 0:
            return False

        no_hit_ratio = no_hit_rays / total_rays

        return no_hit_ratio >= self.no_hit_ratio_required

    def choose_best_free_direction(self, scan: LaserScan):
        """
        Обычный режим:
        выбрать направление, где препятствие дальше всего.
        """

        best_score = -999.0
        best_angle = 0.0
        best_distance = 0.0

        start_angle = -self.search_angle_deg
        end_angle = self.search_angle_deg

        angle = start_angle

        while angle <= end_angle:
            distance = self.get_sector_min(
                scan,
                angle,
                self.sector_width_deg
            )

            # Немного предпочитаем движение вперёд
            forward_preference = 1.0 - abs(angle) / self.search_angle_deg

            score = distance + 0.25 * forward_preference

            if score > best_score:
                best_score = score
                best_angle = angle
                best_distance = distance

            angle += self.sector_width_deg

        return best_angle, best_distance

    def choose_random_no_hit_direction(self, scan: LaserScan):
        """
        Случайный режим:
        выбрать случайное направление только среди тех секторов,
        где лучи LiDAR не видят стену/объект.
        """

        candidates = []

        angle = -self.random_explore_max_angle_deg

        while angle <= self.random_explore_max_angle_deg:
            sector_clear = self.sector_has_no_hits(
                scan,
                angle,
                self.sector_width_deg
            )

            if sector_clear:
                # Чтобы робот реально заезжал в центр комнаты,
                # не выбираем почти прямое направление
                if abs(angle) >= 20:
                    candidates.append(angle)

            angle += self.sector_width_deg

        if not candidates:
            return None

        return random.choice(candidates)

    def start_random_exploration_if_possible(self, scan: LaserScan, front, left, right):
        now = self.now_sec()

        if now < self.next_random_explore_time:
            return

        # Не включаем случайное движение в туннеле/коридоре
        tunnel_like = (
            0.25 < left < 1.20 and
            0.25 < right < 1.20 and
            front > 0.80
        )

        if tunnel_like:
            self.next_random_explore_time = now + 3.0
            return

        # Не включаем случайное движение рядом со стенами
        if front < 0.90:
            self.next_random_explore_time = now + 2.0
            return

        if left < 0.45 or right < 0.45:
            self.next_random_explore_time = now + 2.0
            return

        random_angle = self.choose_random_no_hit_direction(scan)

        if random_angle is None:
            self.next_random_explore_time = now + 2.0
            return

        self.random_explore_active = True
        self.random_explore_angle_deg = random_angle
        self.random_explore_end_time = now + self.random_explore_duration

        self.next_random_explore_time = now + random.uniform(
            self.random_explore_min_interval,
            self.random_explore_max_interval
        )

        self.get_logger().info(
            f"Random no-hit exploration: direction {random_angle:.0f} degrees"
        )

    def start_recovery_turn(self, scan: LaserScan):
        left = self.get_sector_min(scan, 90, 60)
        right = self.get_sector_min(scan, -90, 60)

        if left > right:
            self.recovery_direction = 1
        else:
            self.recovery_direction = -1

        self.recovery_start_yaw = self.current_yaw
        self.state = "RECOVERY_TURN"

        self.get_logger().warn(
            f"Wall too close. Turning {math.degrees(self.recovery_angle):.0f} degrees."
        )

    def recovery_turn_control(self):
        if self.current_yaw is None or self.recovery_start_yaw is None:
            self.target_linear = 0.0
            self.target_angular = self.recovery_direction * self.recovery_turn_speed
            return

        turned_angle = self.normalize_angle(
            self.current_yaw - self.recovery_start_yaw
        )

        if abs(turned_angle) >= self.recovery_angle - self.recovery_tolerance:
            self.target_linear = 0.0
            self.target_angular = 0.0
            self.state = "EXPLORE"

            self.get_logger().info(
                "Recovery turn finished. Searching free space again."
            )
            return

        self.target_linear = 0.0
        self.target_angular = self.recovery_direction * self.recovery_turn_speed

    def explore_control(self):
        if self.last_scan is None:
            self.target_linear = 0.0
            self.target_angular = 0.0
            return

        scan = self.last_scan

        front = self.get_sector_min(scan, 0, 20)
        left = self.get_sector_min(scan, 90, 45)
        right = self.get_sector_min(scan, -90, 45)

        # Если робот почти упёрся в стену — разворот на фиксированный угол
        if front < self.front_danger_distance:
            self.random_explore_active = False
            self.start_recovery_turn(scan)
            return

        # Иногда пробуем выбрать направление, где лучи вообще не видят стену
        self.start_random_exploration_if_possible(scan, front, left, right)

        now = self.now_sec()

        # Основное направление — туда, где больше свободного места
        best_angle_deg, best_distance = self.choose_best_free_direction(scan)

        # Если активен случайный режим, используем выбранный no-hit сектор
        if self.random_explore_active:
            sector_still_clear = self.sector_has_no_hits(
                scan,
                self.random_explore_angle_deg,
                self.sector_width_deg
            )

            if now >= self.random_explore_end_time:
                self.random_explore_active = False

            elif not sector_still_clear:
                self.random_explore_active = False

            else:
                best_angle_deg = self.random_explore_angle_deg
                best_distance = scan.range_max

        best_angle_rad = math.radians(best_angle_deg)

        angular = 0.9 * best_angle_rad
        angular = self.clamp(
            angular,
            -self.max_turn_speed,
            self.max_turn_speed
        )

        # Чем сильнее поворот — тем медленнее движение
        turn_factor = 1.0 - min(abs(best_angle_deg) / 90.0, 1.0)

        # Чем ближе препятствие спереди — тем медленнее движение
        distance_factor = self.clamp(
            (front - self.front_danger_distance) /
            (self.front_slow_distance - self.front_danger_distance),
            0.0,
            1.0
        )

        linear = self.min_forward_speed + (
            self.max_forward_speed - self.min_forward_speed
        ) * distance_factor * (0.4 + 0.6 * turn_factor)

        # Защита от боковых стен
        if left < self.side_danger_distance:
            angular -= 0.08

        if right < self.side_danger_distance:
            angular += 0.08

        self.target_linear = linear
        self.target_angular = angular

        mode = "RANDOM_NO_HIT" if self.random_explore_active else "NORMAL"

        self.get_logger().info(
            f"mode={mode}, front={front:.2f}, left={left:.2f}, right={right:.2f}, "
            f"angle={best_angle_deg:.0f}, v={linear:.2f}, w={angular:.2f}",
            throttle_duration_sec=1.0
        )

    def control_loop(self):
        if self.state == "RECOVERY_TURN":
            self.recovery_turn_control()
        else:
            self.explore_control()

        dt = 0.1

        max_linear_change = self.max_linear_accel * dt
        max_angular_change = self.max_angular_accel * dt

        self.current_linear = self.limit_change(
            self.current_linear,
            self.target_linear,
            max_linear_change
        )

        self.current_angular = self.limit_change(
            self.current_angular,
            self.target_angular,
            max_angular_change
        )

        cmd = Twist()
        cmd.linear.x = self.current_linear
        cmd.angular.z = self.current_angular

        self.cmd_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)

    node = TurtlebotMappingNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    # Остановить робота при Ctrl + C
    stop_cmd = Twist()
    node.cmd_pub.publish(stop_cmd)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()