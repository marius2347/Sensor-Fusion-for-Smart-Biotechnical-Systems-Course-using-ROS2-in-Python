#!/usr/bin/env python3
"""Reads Webots Compass device and publishes as sensor_msgs/Imu (yaw only) for EKF fusion."""
import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Quaternion, Vector3Stamped


def euler_to_quaternion(roll, pitch, yaw):
    """Convert euler angles to quaternion."""
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)
    q = Quaternion()
    q.w = cr * cp * cy + sr * sp * sy
    q.x = sr * cp * cy - cr * sp * sy
    q.y = cr * sp * cy + sr * cp * sy
    q.z = cr * cp * sy - sr * sp * cy
    return q


class CompassToImu(Node):
    def __init__(self):
        super().__init__('compass_to_imu')
        self.publisher_ = self.create_publisher(Imu, '/compass/imu', 10)
        self.subscription = self.create_subscription(
            Vector3Stamped,
            '/compass/values/north_vector',
            self.compass_callback,
            10
        )
        self.get_logger().info('Compass→IMU node started: /compass/values/north_vector → /compass/imu')

    def compass_callback(self, msg):
        # Webots compass north_vector: unit vector pointing to north in robot frame
        north_x = msg.vector.x
        north_y = msg.vector.y
        # Calculate heading (yaw) from north vector
        yaw = math.atan2(north_y, north_x)

        imu_msg = Imu()
        imu_msg.header.stamp = msg.header.stamp if msg.header.stamp.sec > 0 else self.get_clock().now().to_msg()
        imu_msg.header.frame_id = 'base_link'
        imu_msg.orientation = euler_to_quaternion(0.0, 0.0, yaw)
        # Only yaw is valid (roll/pitch = -1 means unknown)
        imu_msg.orientation_covariance = [
            -1.0, 0.0, 0.0,
            0.0, -1.0, 0.0,
            0.0, 0.0, 0.01
        ]
        imu_msg.angular_velocity_covariance = [-1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        imu_msg.linear_acceleration_covariance = [-1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.publisher_.publish(imu_msg)


def main(args=None):
    rclpy.init(args=args)
    node = CompassToImu()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
