# test_installation.py
import sys
import os


def test_installation():
    print("=" * 60)
    print("QUIZSECURE INSTALLATION TEST")
    print("=" * 60)

    # Basic Python info
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print("-" * 50)

    # Test PyTorch
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__}")
        print(f"✅ CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"✅ CUDA version: {torch.version.cuda}")
            print(f"✅ GPU device: {torch.cuda.get_device_name(0)}")
    except ImportError as e:
        print(f"❌ PyTorch failed: {e}")

    # Test OpenCV
    try:
        import cv2
        print(f"✅ OpenCV {cv2.__version__}")
    except ImportError as e:
        print(f"❌ OpenCV failed: {e}")

    # Test MediaPipe
    try:
        import mediapipe as mp
        print(f"✅ MediaPipe {mp.__version__}")
    except ImportError as e:
        print(f"❌ MediaPipe failed: {e}")

    # Test ptgaze - multiple import methods
    print("-" * 50)
    print("Testing ptgaze imports:")

    # Method 1: Direct import
    try:
        from ptgaze import GazeEstimator
        print("✅ ptgaze.GazeEstimator imported successfully")

        # Try to initialize
        gaze_estimator = GazeEstimator()
        print("✅ GazeEstimator initialized successfully")
        ptgaze_working = True

    except ImportError as e:
        print(f"❌ ptgaze.GazeEstimator failed: {e}")
        ptgaze_working = False
    except Exception as e:
        print(f"❌ GazeEstimator initialization failed: {e}")
        ptgaze_working = False

    # Method 2: Check what's available in ptgaze
    try:
        import ptgaze
        print(f"ptgaze location: {ptgaze.__file__}")
        print(f"ptgaze contents: {dir(ptgaze)}")
    except Exception as e:
        print(f"❌ ptgaze module inspection failed: {e}")

    # Method 3: Try alternative imports
    if not ptgaze_working:
        try:
            from ptgaze.gaze_estimator import GazeEstimator
            print("✅ Direct ptgaze.gaze_estimator import works!")
            ptgaze_working = True
        except ImportError:
            print("❌ Direct ptgaze.gaze_estimator import failed")

        try:
            import ptgaze.main
            print("✅ ptgaze.main module found")
        except ImportError:
            print("❌ ptgaze.main not found")

    # Test webcam access
    print("-" * 50)
    print("Testing webcam access:")
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"✅ Webcam accessible - frame shape: {frame.shape}")
            else:
                print("❌ Cannot read frame from webcam")
            cap.release()
        else:
            print("❌ Cannot open webcam")
    except Exception as e:
        print(f"❌ Webcam test failed: {e}")

    # Virtual environment check
    print("-" * 50)
    print("Virtual Environment Check:")
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Running in virtual environment")
    else:
        print("⚠️  Not running in virtual environment")

    # Check for multiple venv folders
    current_dir = os.getcwd()
    venv_folders = [d for d in os.listdir(current_dir) if d.startswith('.venv') and os.path.isdir(d)]
    for folder in venv_folders:
        print(f"✅ Found virtual environment folder: {folder}")

    # Summary
    print("=" * 50)
    print("INSTALLATION SUMMARY:")
    print("=" * 50)

    if ptgaze_working:
        print("🎉 ALL SYSTEMS GO! QuizSecure backend ready to develop!")
        print("\nNext steps:")
        print("1. Create your FastAPI backend")
        print("2. Implement gaze monitoring endpoints")
        print("3. Build your frontend integration")
    else:
        print("🚨 PTGAZE ISSUES DETECTED")
        print("\nTo fix:")
        print("1. Try: pip uninstall ptgaze -y")
        print("2. Then: pip install ptgaze --no-cache-dir")
        print("3. Or install from source: pip install -e .")
        print("4. Alternative: pip install gaze-tracking")


if __name__ == "__main__":
    test_installation()