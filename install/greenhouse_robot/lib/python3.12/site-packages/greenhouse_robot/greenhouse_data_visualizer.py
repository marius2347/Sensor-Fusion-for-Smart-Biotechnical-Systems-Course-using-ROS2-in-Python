#!/usr/bin/env python3
"""Publishes real greenhouse sensor data as colored markers in RViz."""
import csv
import os
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from std_msgs.msg import ColorRGBA
from ament_index_python.packages import get_package_share_directory


class GreenhouseDataVisualizer(Node):
    def __init__(self):
        super().__init__('greenhouse_data_visualizer')
        self.publisher_ = self.create_publisher(MarkerArray, '/greenhouse_zones', 10)
        self.timer = self.create_timer(2.0, self.publish_markers)

        # Load CSV
        pkg_share = get_package_share_directory('greenhouse_robot')
        csv_path = os.path.join(pkg_share, 'config', 'processed_sensor_data.csv')
        self.zones = []
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.zones.append(row)
        self.get_logger().info(f'Loaded {len(self.zones)} greenhouse zones from real Kaggle data')

    def humidity_to_color(self, humidity):
        """Color based on humidity: RED = too low (<50%), YELLOW = moderate (50-65%), GREEN = good (>65%)"""
        h = float(humidity)
        color = ColorRGBA()
        color.a = 0.7  # semi-transparent
        if h < 50.0:
            # Critical - RED
            color.r, color.g, color.b = 1.0, 0.0, 0.0
        elif h < 65.0:
            # Warning - YELLOW
            color.r, color.g, color.b = 1.0, 1.0, 0.0
        else:
            # Good - GREEN
            color.r, color.g, color.b = 0.0, 1.0, 0.0
        return color

    def publish_markers(self):
        marker_array = MarkerArray()
        for i, zone in enumerate(self.zones):
            x = float(zone['X'])
            y = float(zone['Y'])
            humidity = float(zone['Humidity'])
            temp = float(zone['Temperature'])
            co2 = float(zone['CO2'])
            name = zone['Zone']

            # Cylinder marker (colored by humidity)
            cylinder = Marker()
            cylinder.header.frame_id = 'map'
            cylinder.header.stamp = self.get_clock().now().to_msg()
            cylinder.ns = 'greenhouse_zones'
            cylinder.id = i * 2
            cylinder.type = Marker.CYLINDER
            cylinder.action = Marker.ADD
            cylinder.pose.position.x = x
            cylinder.pose.position.y = y
            cylinder.pose.position.z = 0.5  # half height
            cylinder.scale.x = 0.6  # diameter
            cylinder.scale.y = 0.6
            cylinder.scale.z = 1.0  # height
            cylinder.color = self.humidity_to_color(humidity)
            cylinder.lifetime.sec = 5
            marker_array.markers.append(cylinder)

            # Text marker (shows data)
            text = Marker()
            text.header.frame_id = 'map'
            text.header.stamp = self.get_clock().now().to_msg()
            text.ns = 'greenhouse_labels'
            text.id = i * 2 + 1
            text.type = Marker.TEXT_VIEW_FACING
            text.action = Marker.ADD
            text.pose.position.x = x
            text.pose.position.y = y
            text.pose.position.z = 1.3  # above the cylinder
            text.scale.z = 0.25  # text height
            text.color = ColorRGBA(r=1.0, g=1.0, b=1.0, a=1.0)
            text.text = f'{name}\nT:{temp:.1f}°C H:{humidity:.1f}%\nCO2:{co2:.0f}ppm'
            text.lifetime.sec = 5
            marker_array.markers.append(text)

        self.publisher_.publish(marker_array)


def main(args=None):
    rclpy.init(args=args)
    node = GreenhouseDataVisualizer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
