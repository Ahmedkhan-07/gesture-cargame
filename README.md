# 🚗 Hand Gesture Car Racing Game

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Pygame-2.x-green?logo=pygame" />
  <img src="https://img.shields.io/badge/MediaPipe-Hands-orange" />
  <img src="https://img.shields.io/badge/OpenCV-4.x-red?logo=opencv" />
  <img src="https://img.shields.io/badge/License-MIT-lightgrey" />
</p>

<p align="center">
  A real-time hand-gesture-controlled car racing game built with Python.<br/>
  Use your webcam — no keyboard, no controller, just your hand.
</p>

---

## ✨ Features

- 🖐️ **Gesture Control** — Move your hand left, centre, or right in front of the webcam to switch lanes
- 🎮 **3-Lane Racing** — Dodge oncoming enemy cars across 3 lanes
- ❤️ **Lives System** — 3 lives before game over; one collision per enemy car
- 💥 **Particle Explosions** — Collision bursts with physics-based particles
- 🌀 **Speed Lines** — Dynamic motion blur that intensifies as speed increases
- 🏎️ **Smooth Lane Switching** — Player car slides to target lane with interpolation
- 📈 **Progressive Difficulty** — Enemy speed and spawn rate increase with your score
- 🎨 **Detailed Car Graphics** — Styled player and colour-coded enemy cars with headlights, tail lights, and windows
- 📷 **Live Camera Preview** — Embedded webcam feed so you can see your hand position at all times
- 🔄 **Scrolling Road** — Animated dashed lane markers and centre line give a sense of speed

---

## 📸 Demo

> *Plug in your webcam, run the script, and race with your hand!*

| Gameplay | Camera View |
|----------|-------------|
| Scrolling road, particle FX, lives HUD | Live hand-tracking overlay embedded in game window |

---

## 🛠️ Requirements

| Package | Version | Purpose |
|---------|---------|---------|
| Python | 3.8+ | Runtime |
| `pygame` | 2.x | Game window & rendering |
| `mediapipe` | 0.10+ | Hand landmark detection |
| `opencv-python` | 4.x | Webcam capture & image processing |
| `numpy` | any | Surface array operations |

---

## ⚙️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/hand-gesture-car-game.git
cd hand-gesture-car-game
```

### 2. (Recommended) Create a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install pygame mediapipe opencv-python numpy
```

### 4. Run the game
```bash
python car_game_enhanced.py
```

> **Note:** A working webcam is required. On first launch, your OS may prompt you to grant camera permissions.

---

## 🎮 How to Play

| Action | Gesture |
|--------|---------|
| **Lane Left** | Move your open hand to the **left third** of the camera frame |
| **Lane Centre** | Hold your hand in the **middle** of the frame |
| **Lane Right** | Move your open hand to the **right third** of the frame |
| **Restart** | After Game Over, show your hand in front of the camera |
| **Quit** | Press `Esc` or close the window |

**Tips:**
- Keep your hand clearly visible and well-lit for best tracking accuracy
- The embedded camera preview (top-right corner) shows exactly what the model sees
- Avoid fast, jerky movements — the lane smoothing will handle small wobbles

---

## 🗂️ Project Structure

```
hand-gesture-car-game/
│
├── car_game_enhanced.py   # Main game file
└── README.md              # This file
```

---

## 🔧 Configuration

You can tweak the following constants near the top of `car_game_enhanced.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `WIN_W / WIN_H` | `800 / 600` | Game window resolution |
| `FPS` | `60` | Target frame rate |
| `CAM_SKIP` | `2` | Process camera every N frames (higher = better FPS, slightly laggier control) |
| `MAX_ENEMIES` | `12` | Maximum simultaneous enemy cars |
| `MAX_SPEED` | `18.0` | Speed cap for enemy cars |
| `LANE_COUNT` | `3` | Number of lanes |

---

## 🐛 Known Issues & Troubleshooting

| Problem | Fix |
|---------|-----|
| Black screen / no camera feed | Ensure no other app is using the webcam; try changing `cv2.VideoCapture(0)` to `(1)` |
| Hand not detected | Improve lighting; keep your hand fully visible and within frame |
| Low FPS | Increase `CAM_SKIP`; close other applications; reduce `WIN_W / WIN_H` |
| `ModuleNotFoundError` | Double-check all packages are installed in the active Python environment |

---

## 🚀 Roadmap

- [ ] Sound effects and background music
- [ ] Power-ups (shield, slow-motion, score multiplier)
- [ ] High-score leaderboard with local persistence
- [ ] Two-player split-screen mode
- [ ] Additional gesture controls (fist = brake / speed boost)
- [ ] Difficulty presets (Easy / Normal / Hard)

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- [MediaPipe](https://mediapipe.dev/) by Google — hand landmark detection
- [Pygame](https://www.pygame.org/) — game framework
- [OpenCV](https://opencv.org/) — computer vision & webcam interface

---

<p align="center">Made with ❤️ and Python</p>
