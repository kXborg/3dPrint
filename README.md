# 🖨️ 3D Printing & Makerspace

Welcome to my central repository for all things related to 3D printing. This repo houses my 3D models, G-codes, datasets, and my custom AI-based print failure detection system built for the Creality Ender-3 V2 Neo. 

![creality-ender3-v2-neo-printing](https://github.com/user-attachments/assets/bf54734f-5be2-4bbd-81dc-47c57aaba90c)

## 📂 Repository Contents

- **`Models/`**: My collection of 3D models and generated G-code files.
- **`src/` & `utils/`**: Source code for my real-time YOLO-based **Print Failure Detection System**.
---

## 🛑 Print Failure Detection System

One of the core projects in this repository is a real-time 3D print failure detection system using AI (YOLO). Point a webcam at your printer, and the system continuously watches for common FDM printing defects and can automatically pause or kill the print before things get worse.

*Built for the Creality Ender-3 V2 Neo, but works with any FDM printer + webcam setup.*

### What It Detects

| Defect | Description | Severity |
|--------|-------------|----------|
| 🍝 **Spaghetti** | Print detaches from bed and extrudes into a tangled mess | 🔴 Critical — auto-stops printer |
| 🧵 **Stringing** | Thin filament wisps between travel moves | 🟡 Cosmetic — logs alert |
| 🔵 **Zits** | Small blobs/bumps on the print surface | 🟢 Minor — logs alert |

## 📝 Read the Blog Series

I documented the entire process of building the failure monitoring system in a series of blog posts. Check them out for a deep dive into the development, training, and deployment:

- [Building a 3D Print Failure Detection System](https://www.orbital.net.in/blog/ender-3-v2-neo-print-failure-detection)
- [Monitoring and Auto-Stopping Failed Prints](https://www.orbital.net.in/blog/ender-3-v2-neo-print-failure-detection-monitoring)
- [All 3D Printing Posts](https://www.orbital.net.in/blog?category=3D%20Printing)
