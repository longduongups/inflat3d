import threading
import asyncio
from bleak import BleakClient
import struct
import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageTk
import winsound

# UUIDs des caractéristiques
SENSOR_CHARACTERISTIC_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"
DEVICE_MAC = {
    "Haut": "F0:CF:41:E5:1F:D5",
    "Bas": "4C:EB:D6:4D:3B:BA",
}

# Variables globales
stop_requested = False
monitor_angle = False
latest_acc = {"Haut": None, "Bas": None}
calibrated_angle = None
previous_posture_state = None

# Seuils selon recommandations médicales
GOOD_POSTURE_THRESHOLD = 15
WARNING_THRESHOLD = 20

# Base de données
date_hour_DBTable = datetime.now().strftime("TER_%Y%m%d_%H%M")
db_name = "Data_IMU.db"

def decode_sensor_data(data):
    if len(data) != 50:
        raise ValueError("La taille des données n'est pas correcte")
    acc_data = struct.unpack('<fff', data[:12])
    gyro_data = struct.unpack('<fff', data[12:24])
    timer = struct.unpack('<I', data[24:28])[0]
    orientation_data = struct.unpack('<fff', data[28:40])
    steps_data = struct.unpack('<I', data[40:44])[0]
    return acc_data, gyro_data, timer, orientation_data, steps_data

def connect_to_database(db_name):
    return sqlite3.connect(db_name)

def create_table(conn):
    cursor = conn.cursor()
    str_execute = f'''
    CREATE TABLE IF NOT EXISTS {date_hour_DBTable} (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        time REAL NOT NULL,
        imu_name TEXT NOT NULL,
        acc_x REAL, acc_y REAL, acc_z REAL,
        gyro_x REAL, gyro_y REAL, gyro_z REAL,
        heading REAL, pitch REAL, roll REAL,
        steps INTEGER, processed INTEGER,
        velocity_x REAL, velocity_y REAL, velocity_z REAL,
        position_x REAL, position_y REAL, position_z REAL
    )'''
    cursor.execute(str_execute)
    conn.commit()

def insert_sensor_data(conn, time, imu_name, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z, heading, pitch, roll, steps):
    cursor = conn.cursor()
    cursor.execute(f'''
        INSERT INTO {date_hour_DBTable}(
            time, imu_name, acc_x, acc_y, acc_z,
            gyro_x, gyro_y, gyro_z,
            heading, pitch, roll, steps, processed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (time, imu_name, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z, heading, pitch, roll, steps, 0))
    conn.commit()

async def read_characteristics(address, name):
    global stop_requested
    client = BleakClient(address)
    try:
        await client.connect()
        print(f"Connecté à {name}")
        conn = connect_to_database(db_name)
        create_table(conn)
        timer_offset = 0
        first_value = False

        while client.is_connected and not stop_requested:
            data_sensor = await client.read_gatt_char(SENSOR_CHARACTERISTIC_UUID)
            acc_data, gyro_data, timer, orientation_data, steps_data = decode_sensor_data(data_sensor)
            if not first_value:
                timer_offset = timer
                first_value = True

            time_val = timer - timer_offset
            insert_sensor_data(conn, time_val, name, *acc_data, *gyro_data, *orientation_data, steps_data)
            latest_acc[name] = np.array(acc_data) / np.linalg.norm(acc_data)
            await asyncio.sleep(0.05)

    except Exception as e:
        print(f"Erreur avec {name}: {e}")
    finally:
        await client.disconnect()

async def main():
    tasks = [read_characteristics(address, name) for name, address in DEVICE_MAC.items()]
    await asyncio.gather(*tasks)

def run():
    asyncio.run(main())

def start_measurement():
    global stop_requested
    stop_requested = False
    threading.Thread(target=run).start()

def stop_measurement():
    global stop_requested, monitor_angle
    stop_requested = True
    monitor_angle = False
    status_label.config(text="⏹️ Mesure arrêtée.")

def calibrate_angle():
    global calibrated_angle
    acc_haut = latest_acc.get("Haut")
    acc_bas = latest_acc.get("Bas")
    if acc_haut is not None and acc_bas is not None:
        dot = np.dot(acc_haut, acc_bas)
        calibrated_angle = np.degrees(np.arccos(np.clip(dot, -1.0, 1.0)))
        messagebox.showinfo("Calibration", f"✅ Calibration faite : angle de référence = {calibrated_angle:.1f}°")
        global monitor_angle
        monitor_angle = True
    else:
        messagebox.showwarning("Calibration", "Capteurs non disponibles pour calibration.")

fig, ax = None, None
plt.ion()
def init_posture_plot():
    global fig, ax
    fig, ax = plt.subplots(figsize=(4, 6)) 
    plt.pause(0.01)
    ax.set_xlim(-2, 2)
    ax.set_ylim(-0.5, 3.5)
    ax.set_aspect('equal')
    ax.grid(True)
    ax.set_title("Simulation de posture")

def draw_vector_angle_dual(acc_haut, acc_bas):
    ax.clear()
    x0, y0 = 0, 0
    l = 1.0

    rad_bas = np.arctan2(acc_bas[0], acc_bas[2]) - np.radians(90)
    x1 = x0 + l * np.sin(rad_bas)
    y1 = y0 + l * np.cos(rad_bas)

    rad_haut = np.arctan2(acc_haut[0], acc_haut[2]) - np.radians(90)
    x2 = x1 + l * np.sin(rad_haut)
    y2 = y1 + l * np.cos(rad_haut)

    ax.plot([x0, x1], [y0, y1], 'bo-', label='Bas')
    ax.plot([x1, x2], [y1, y2], 'ro-', label='Haut')
    ax.set_xlim(-2, 2)
    ax.set_ylim(-0.5, 3.5)
    ax.set_aspect('equal')
    ax.grid(True)
    ax.legend()
    plt.draw()
    plt.pause(0.001)

def update_ui():
    global previous_posture_state
    if monitor_angle:
        acc_haut = latest_acc.get("Haut")
        acc_bas = latest_acc.get("Bas")
        if acc_haut is not None and acc_bas is not None:
            dot = np.dot(acc_haut, acc_bas)
            angle = np.degrees(np.arccos(np.clip(dot, -1.0, 1.0)))
            draw_vector_angle_dual(acc_haut, acc_bas)
            if calibrated_angle is not None:
                delta = angle - calibrated_angle
                angle_label.config(text=f"Angle actuel : {angle:.1f}° | ∆ depuis calibration : {delta:+.1f}°")
                if abs(delta) <= GOOD_POSTURE_THRESHOLD:
                    status_label.config(text="✅ Bonne posture", fg="green")
                    previous_posture_state = "good"
                elif abs(delta) <= WARNING_THRESHOLD:
                    status_label.config(text="⚠️ Posture à corriger", fg="orange")
                    if previous_posture_state != "warn":
                        winsound.Beep(800, 300)
                        previous_posture_state = "warn"
                else:
                    status_label.config(text="❌ Mauvaise posture", fg="red")
                    if previous_posture_state != "bad":
                        winsound.Beep(500, 500)
                        previous_posture_state = "bad"
            else:
                angle_label.config(text=f"Angle entre capteurs : {angle:.1f}°")
    root.after(500, update_ui)

# Interface utilisateur
root = tk.Tk()
root.title("Inflat3D - Contrôle de posture (UPSSITECH)")
root.geometry("700x650")  

tk.Label(root, text="🎓 Projet Inflat3D ", font=("Arial", 16, "bold")).pack(pady=5)

try:
    pil_image = Image.open("logo_upssitech.png")
    resized_image = pil_image.resize((342, 100))  
    logo = ImageTk.PhotoImage(resized_image)

    logo_label = tk.Label(root, image=logo)
    logo_label.image = logo  
    logo_label.pack(pady=5)
except Exception as e:
    print(f"Erreur chargement logo: {e}")

button_frame = tk.Frame(root)
button_frame.pack(pady=10)

tk.Button(button_frame, text="▶️ Start", width=25, command=start_measurement).grid(row=0, column=0, padx=5, pady=5)
tk.Button(button_frame, text="🎯 Calibrer angle", width=25, command=calibrate_angle).grid(row=1, column=0, padx=5, pady=5)
tk.Button(button_frame, text="⏹️ Stop", width=25, command=stop_measurement).grid(row=2, column=0, padx=5, pady=5)

angle_frame = tk.Frame(root)
angle_frame.pack(pady=10)

angle_label = tk.Label(angle_frame, text="Angle entre capteurs : -- °", font=("Arial", 14))
angle_label.pack(pady=5)

status_label = tk.Label(root, text="🕐 En attente de démarrage...", font=("Arial", 14, "bold"))
status_label.pack(pady=10)

monitor_angle = True
init_posture_plot()
update_ui()
root.mainloop()
