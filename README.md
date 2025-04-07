# 🧠 Inflat3D – Suivi intelligent de la posture

Ce projet a été développé dans le cadre du module projet à l'**UPSSITECH Toulouse**, pour la surveillance de posture en temps réel à l’aide de **capteurs IMU**.

---

## 🎯 Objectif

Détecter et corriger les mauvaises postures du dos à l’aide de deux capteurs inertiels placés sur le haut et le bas du dos.  
Le système calcule l’écart d’angle entre les capteurs pour alerter l’utilisateur en cas de désalignement prolongé.

---

## ⚙️ Fonctionnement

### 🧹 Composants utilisés :
- **Arduino Nano 33 BLE** et **Nano 33 IoT** (avec IMU intégré)
- **Batteries LiPo 3.7V**
- **Connexion Bluetooth Low Energy (BLE)**
- **Capteurs IMU** (accéléromètre et gyroscope)

### ⟳ Schéma global :
1. Deux capteurs IMU sur le haut et bas du dos
2. Envoi des données en Bluetooth vers un PC
3. Traitement en temps réel via une **IHM Python (Tkinter + Matplotlib)**
4. Données enregistrées dans une base **SQLite**
5. **Visualisation différée** des sessions via une application **web (Streamlit)**

---

## 💥 Interface IHM (temps réel)

- `▶️ Start` : Démarrer la collecte et affichage des données
- `🎯 Calibrer` : Enregistrer la posture de référence (bonne posture)
- `⏹️ Stop` : Arrêter la collecte et l'enregistrement
- ✅ Affichage couleur en fonction de l’écart d’angle (vert, orange, rouge)
- 🔊 Alerte sonore en cas de mauvaise posture prolongée

---

## 🌐 Application Web (visualisation)

Développée avec **Streamlit**, elle permet :
- De charger une session enregistrée
- D’afficher l’évolution de l’angle entre capteurs
- De visualiser les moments de mauvaise posture (code couleur)
- D’obtenir un pourcentage de mauvaise posture

---

## 🛆 Installation

### Pré-requis :
- Python ≥ 3.9
- Modules : `bleak`, `matplotlib`, `streamlit`, `numpy`, `Pillow`

### Installation des dépendances :

```bash
pip install -r requirements.txt
```

---

## 📁 Fichiers clés

- `main1.py` → Interface IHM (Tkinter)
- `app.py` → Application Streamlit
- `Data_IMU.db` → Base de données SQLite des sessions
- `logo_upssitech.png` → Logo de l’école

---

## 📌 Licence

Ce projet est open source – à des fins éducatives uniquement.
