#!/usr/bin/env python
#coding:utf-8

import socket
import time
import rospy
import json
from sensor_msgs.msg import Imu
from sensor_msgs.msg import MagneticField

"""
Data received :
Axes are those defined by the physical sensor on the robot
{IMU1:{"time": t,
"accel_x": accel_x,
"accel_y": accel_y,
"accel_z": accel_z,
"mag_x": mag_x,
"mag_y": mag_y,
"mag_z": mag_z,
"gyro_x": gyro_x,
"gyro_y": gyro_y,
"gyro_z": gyro_z,
"temperature": temp},  
IMU2:{"time": t,
"accel_x": accel_x,
"accel_y": accel_y,
"accel_z": accel_z,
"mag_x": mag_x,
"mag_y": mag_y,
"mag_z": mag_z,
"gyro_x": gyro_x,
"gyro_y": gyro_y,
"gyro_z": gyro_z,
"temperature": temp}}
"""

class Imu_bridge:
    def __init__(self, host="192.168.2.2",port=14600):

        with open('calibrationIMU1.json') as f:
            self.calibrationFileIMU1 = json.load(f)

        with open('calibrationIMU2.json') as f:
            self.calibrationFileIMU2 = json.load(f)

        self.host = host 
        self.port = port 
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection()

        self.pub_imu1 = rospy.Publisher('/BlueRov2/imu/imu1', Imu, queue_size=10)
        self.pub_imu2 = rospy.Publisher('/BlueRov2/imu/imu2', Imu, queue_size=10)
        self.pub_imu1_mag = rospy.Publisher('/BlueRov2/imu/mag1', MagneticField, queue_size=10)
        self.pub_imu2_mag = rospy.Publisher('/BlueRov2/imu/mag2', MagneticField, queue_size=10)

        self.IMU1_accX = 0        
        self.IMU1_accY = 0
        self.IMU1_accZ = 0
        self.IMU2_accX = 0
        self.IMU2_accY = 0
        self.IMU2_accZ = 0
        self.w = 0.1

    #connection to the serveur
    def connection(self):
        try:
            self.socket.connect((self.host, self.port))
        except ConnectionRefusedError:
            print("Server not started")
        except:
            print("CONNECTION FAILED")

    def send(self, data):
        data = data.encode("utf8")
        self.socket.send(data)

    def recv(self):
        b_data =  self.socket.recv(1024) #1024 characters
        s_data = b_data.decode("utf8")
        return json.loads(s_data)      

    def publish(self,data):
        msg_imu1, msg_mag1, msg_imu2, msg_mag2 = self._create_msg(data)
        self.pub_imu1.publish(msg_imu1)
        self.pub_imu2.publish(msg_imu2)
        self.pub_imu1_mag.publish(msg_mag1)
        self.pub_imu2_mag.publish(msg_mag2)

    def _create_msg(self,data):
        """
        Messages published with ROS have axis from the robot frame : x forward, y ?, z up or down
        """
    #----IMU 1 calibrate---
        msg1 = Imu()
        msg1_magfield = MagneticField()   
        msg1.header.stamp = rospy.Time.now()
        msg1.header.frame_id = '/base_link'
        msg1_magfield.header.stamp = rospy.Time.now()
        msg1_magfield.header.frame_id = '/base_link'

        #For calibration and normalisation of linear_acceleration and magnetometer
        #Calibrating file are multiplied by 1e3, need to multiply raw acceleration and magnetometer by 1e3 for concordance

        msg1.linear_acceleration.x = -data["IMU1"]["accel_y"]-self.calibrationFileIMU1['acc_off_x']
        msg1.linear_acceleration.y = -data["IMU1"]["accel_z"]-self.calibrationFileIMU1['acc_off_y']
        msg1.linear_acceleration.z =  data["IMU1"]["accel_x"]-self.calibrationFileIMU1['acc_off_z']

        msg1.linear_acceleration_covariance = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        
        msg1.angular_velocity.x = -data["IMU1"]["gyro_y"]-self.calibrationFileIMU1['gyr_off_x']
        msg1.angular_velocity.y = -data["IMU1"]["gyro_z"]-self.calibrationFileIMU1['gyr_off_y']
        msg1.angular_velocity.z =  data["IMU1"]["gyro_x"]-self.calibrationFileIMU1['gyr_off_z']
        msg1.angular_velocity_covariance = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        
        msg1.orientation.w = 0
        msg1.orientation.x = 0
        msg1.orientation.y = 0
        msg1.orientation.z = 0
        msg1.orientation_covariance = [0, 0, 0, 0, 0, 0, 0, 0, 0]
       
        msg1_magfield.magnetic_field.x = (-data["IMU1"]["mag_y"]*1e3-self.calibrationFileIMU1['magn_off_x']) / self.calibrationFileIMU1['magn_scale_x']
        msg1_magfield.magnetic_field.y = (-data["IMU1"]["mag_z"]*1e3-self.calibrationFileIMU1['magn_off_y']) / self.calibrationFileIMU1['magn_scale_y']
        msg1_magfield.magnetic_field.z = ( data["IMU1"]["mag_x"]*1e3-self.calibrationFileIMU1['magn_off_z']) / self.calibrationFileIMU1['magn_scale_z']
        

    #----IMU 2 calibrate---
        msg2 = Imu()
        msg2_magfield = MagneticField()   
     
        msg2.header.stamp = rospy.Time.now()
        msg2.header.frame_id = '/base_link'
        msg2_magfield.header.stamp = rospy.Time.now()
        msg2_magfield.header.frame_id = '/base_link'

        msg2.linear_acceleration.x = data["IMU2"]["accel_y"]-self.calibrationFileIMU2['acc_off_x']
        msg2.linear_acceleration.y = data["IMU2"]["accel_z"]-self.calibrationFileIMU2['acc_off_y']
        msg2.linear_acceleration.z = data["IMU2"]["accel_x"]-self.calibrationFileIMU2['acc_off_z']
        msg2.linear_acceleration_covariance = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        
        msg2.angular_velocity.x = data["IMU2"]["gyro_y"]-self.calibrationFileIMU2['gyr_off_x']
        msg2.angular_velocity.y = data["IMU2"]["gyro_z"]-self.calibrationFileIMU2['gyr_off_y']
        msg2.angular_velocity.z = data["IMU2"]["gyro_x"]-self.calibrationFileIMU2['gyr_off_z']
        msg2.angular_velocity_covariance = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        
        msg2.orientation.w = 0
        msg2.orientation.x = 0
        msg2.orientation.y = 0
        msg2.orientation.z = 0
        msg2.orientation_covariance = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        msg2_magfield.magnetic_field.x = (data["IMU2"]["mag_y"]*1e3-self.calibrationFileIMU2['magn_off_x']) / self.calibrationFileIMU2['magn_scale_x']
        msg2_magfield.magnetic_field.y = (data["IMU2"]["mag_z"]*1e3-self.calibrationFileIMU2['magn_off_y']) / self.calibrationFileIMU2['magn_scale_y']
        msg2_magfield.magnetic_field.z = (data["IMU2"]["mag_x"]*1e3-self.calibrationFileIMU2['magn_off_z']) / self.calibrationFileIMU2['magn_scale_z']

        return msg1, msg1_magfield, msg2, msg2_magfield 
    
    def main(self):
        while True:
            self.send("?")
            data_rcv = self.recv()
            self.publish(data_rcv)
            time.sleep(0.01)

if __name__=="__main__":
    rospy.init_node('additional_IMU', anonymous=True)
    bridge = Imu_bridge()
    bridge.main()
    bridge.socket.close()
