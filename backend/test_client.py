# test_client.py
import requests
import cv2
import time


def test_api():
    # Test system info
    try:
        response = requests.get("http://localhost:8000/system-info")
        print("System Info:", response.json())
    except Exception as e:
        print(f"System info failed: {e}")
        return

    # Test with webcam
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Cannot access webcam")
        return

    print("Testing monitoring... Press 'q' to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Encode frame as JPEG
        _, buffer = cv2.imencode('.jpg', frame)

        # Send to API
        try:
            files = {'frame': ('frame.jpg', buffer.tobytes(), 'image/jpeg')}
            response = requests.post(
                "http://localhost:8000/monitor-student?user_id=test_student",
                files=files
            )

            if response.status_code == 200:
                result = response.json()
                print(f"Faces detected: {result['faces_detected']}, "
                      f"Alert level: {result['alert_level']}, "
                      f"Warnings: {result['warning_count']}")
            else:
                print(f"API Error: {response.status_code}")

        except Exception as e:
            print(f"Request failed: {e}")

        # Display frame
        cv2.imshow('QuizSecure Test', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(1)  # Send frame every second

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    test_api()