"""
Alert functions for 3D print failure detection.

Currently a placeholder — replace send_alert() with your preferred
notification method (Telegram, email, push notification, etc.).
"""

import cv2
import os
from datetime import datetime


def send_alert(
    failure_type: str,
    confidence: float,
    frame,
    save_dir: str = "alerts",
    save_frames: bool = True,
):
    """
    Send alert when a print failure is detected.

    Args:
        failure_type: Class name of the detected failure (e.g. "spaghetti")
        confidence: Detection confidence score (0.0 - 1.0)
        frame: OpenCV frame (numpy array) at the time of detection
        save_dir: Directory to save alert frames
        save_frames: Whether to save the frame to disk
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[ALERT] {timestamp} | Detected: {failure_type} | Confidence: {confidence:.2f}")

    # Save the frame as evidence
    if save_frames and frame is not None:
        os.makedirs(save_dir, exist_ok=True)
        filename = f"{failure_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(save_dir, filename)
        cv2.imwrite(filepath, frame)
        print(f"[ALERT] Frame saved: {filepath}")


def send_telegram_alert(
    failure_type: str,
    confidence: float,
    frame,
    bot_token: str,
    chat_id: str,
    save_dir: str = "alerts",
):
    """
    Send alert via Telegram Bot API.

    TODO: Implement this function. Example flow:
    1. Save frame to disk
    2. Send text message with detection details
    3. Send photo with the annotated frame

    Args:
        failure_type: Class name of the detected failure
        confidence: Detection confidence score
        frame: OpenCV frame at the time of detection
        bot_token: Telegram Bot API token
        chat_id: Telegram chat ID to send messages to
        save_dir: Directory to save alert frames
    """
    # ---------------------------------------------------------
    # Placeholder implementation
    # Uncomment and configure when ready to use Telegram alerts
    #
    # import requests
    #
    # # Save frame
    # os.makedirs(save_dir, exist_ok=True)
    # filename = f"{failure_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    # filepath = os.path.join(save_dir, filename)
    # cv2.imwrite(filepath, frame)
    #
    # # Send text alert
    # message = (
    #     f"🚨 *Print Failure Detected!*\n\n"
    #     f"Type: `{failure_type}`\n"
    #     f"Confidence: `{confidence:.1%}`\n"
    #     f"Time: `{datetime.now().strftime('%H:%M:%S')}`"
    # )
    # requests.post(
    #     f"https://api.telegram.org/bot{bot_token}/sendMessage",
    #     data={
    #         "chat_id": chat_id,
    #         "text": message,
    #         "parse_mode": "Markdown",
    #     },
    # )
    #
    # # Send photo
    # with open(filepath, "rb") as photo:
    #     requests.post(
    #         f"https://api.telegram.org/bot{bot_token}/sendPhoto",
    #         data={"chat_id": chat_id, "caption": f"{failure_type} ({confidence:.0%})"},
    #         files={"photo": photo},
    #     )
    # ---------------------------------------------------------

    print(f"[TELEGRAM] Alert not sent — Telegram integration not configured.")
    # Fall back to console alert
    send_alert(failure_type, confidence, frame, save_dir)
