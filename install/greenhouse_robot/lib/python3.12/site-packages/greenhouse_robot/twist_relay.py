#!/usr/bin/env python3
"""Relay: subscribes Twist from Nav2, publishes TwistStamped for diff_drive."""
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from geometry_msgs.msg import Twist, TwistStamped

class TwistRelay(Node):
    def __init__(self):
        super().__init__('twist_relay')
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.pub = self.create_publisher(TwistStamped, '/cmd_vel', qos)
        self.sub = self.create_subscription(Twist, '/cmd_vel_nav', self.cb, 10)

    def cb(self, msg):
        out = TwistStamped()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = 'base_link'
        out.twist = msg
        self.pub.publish(out)

def main():
    rclpy.init()
    rclpy.spin(TwistRelay())

if __name__ == '__main__':
    main()
