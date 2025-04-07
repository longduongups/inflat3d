import streamlit as st
import sqlite3
import matplotlib.pyplot as plt
import numpy as np

# Config
DB_NAME = "Data_IMU.db"

# Seuils
GOOD_POSTURE_THRESHOLD = 15
WARNING_THRESHOLD = 20

# Connexion à la base
def get_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'TER_%'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

# Lecture des données
def read_pitch_data(table_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"SELECT time, acc_x, acc_y, acc_z, imu_name FROM {table_name} ORDER BY time ASC")
    rows = cursor.fetchall()
    conn.close()

    data = {"Haut": [], "Bas": []}
    for time, acc_x, acc_y, acc_z, name in rows:
        if name in data:
            norm = np.linalg.norm([acc_x, acc_y, acc_z])
            acc = np.array([acc_x, acc_y, acc_z]) / norm
            data[name].append((time, acc))
    return data

# Calcul des écarts d’angle
def compute_delta_angle(data):
    times = []
    deltas = []
    for (t1, a1), (t2, a2) in zip(data["Haut"], data["Bas"]):
        dot = np.dot(a1, a2)
        angle = np.degrees(np.arccos(np.clip(dot, -1.0, 1.0)))
        times.append(t1)
        deltas.append(angle)
    return times, deltas

# Affichage graphique avec couleurs et légende
def plot_delta_angle(times, deltas):
    fig, ax = plt.subplots(figsize=(10, 5))
    good, warning, bad = 0, 0, 0

    for t, d in zip(times, deltas):
        if abs(d) <= GOOD_POSTURE_THRESHOLD:
            color = 'green'
            good += 1
        elif abs(d) <= WARNING_THRESHOLD:
            color = 'orange'
            warning += 1
        else:
            color = 'red'
            bad += 1
        ax.plot(t, d, marker='o', color=color)

    total = len(deltas)
    bad_pct = (bad / total) * 100 if total else 0

    # Légende
    ax.plot([], [], 'go', label='✅ Bonne posture (≤15°)')
    ax.plot([], [], 'orange', label='⚠️ À corriger (15–20°)')
    ax.plot([], [], 'ro', label='❌ Mauvaise posture (>20°)')

    ax.set_title("Écart d'angle entre capteurs")
    ax.set_xlabel("Temps (ms)")
    ax.set_ylabel("Angle (°)")
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)

    # Pourcentage
    st.markdown(f"### 📊 Pourcentage de mauvaise posture : **{bad_pct:.1f}%**")

# Interface Streamlit
st.title("📈 Visualisation des écarts IMU (Posture)")

tables = get_tables()
if not tables:
    st.warning("Aucune session enregistrée dans la base.")
else:
    selected_table = st.selectbox("Sélectionnez une session :", tables)
    data = read_pitch_data(selected_table)
    if st.button("Afficher le graphique"):
        times, deltas = compute_delta_angle(data)
        plot_delta_angle(times, deltas)
