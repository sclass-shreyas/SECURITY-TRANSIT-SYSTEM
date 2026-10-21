"""Hardware compatibility and OpenVINO acceleration verification script.

Checks for:
1. Python environment and installed libraries (PyTorch, Ultralytics, OpenVINO)
2. Available OpenVINO compute devices (Intel Iris Xe GPU, CPU, etc.)
3. Device capabilities (FP16 support, full device names)
4. Model export and inference benchmark (PyTorch vs OpenVINO on Intel GPU)
"""

from __future__ import annotations

import sys
import time
import numpy as np


def print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def check_python_environment() -> None:
    print_header("1. PYTHON & CORE PACKAGES")
    print(f"Python Version: {sys.version.split()[0]} ({sys.executable})")

    packages = ["torch", "ultralytics", "cv2", "openvino"]
    for pkg in packages:
        try:
            mod = __import__(pkg)
            version = getattr(mod, "__version__", "installed")
            print(f"  [OK] {pkg:<12} : {version}")
        except ImportError:
            print(f"  [MISSING] {pkg:<8} : NOT INSTALLED")


def check_openvino_devices() -> tuple[list[str], str | None]:
    print_header("2. OPENVINO HARDWARE DEVICE DETECTION")
    try:
        from openvino.runtime import Core
    except ImportError:
        print("  [ERROR] OpenVINO is not installed.")
        print("  Run: pip install openvino\n")
        return [], None

    core = Core()
    devices = core.available_devices
    print(f"Available OpenVINO Devices: {devices}")

    intel_gpu_target = None
    for dev in devices:
        full_name = core.get_property(dev, "FULL_DEVICE_NAME")
        print(f"  -> Device '{dev}': {full_name}")
        if "GPU" in dev:
            intel_gpu_target = dev

    if intel_gpu_target:
        print(f"\n  [SUCCESS] Found Intel Graphics device: '{intel_gpu_target}'")
        print("  Your Intel Iris Xe graphics can accelerate YOLO inference!")
    else:
        print("\n  [INFO] No Intel GPU device detected by OpenVINO. Fallback is CPU.")

    return devices, intel_gpu_target


def benchmark_model(intel_gpu_target: str | None) -> None:
    print_header("3. YOLO11n OPENVINO INFERENCE BENCHMARK")
    try:
        from ultralytics import YOLO
    except ImportError:
        print("  [ERROR] Ultralytics is not installed. Run: pip install ultralytics")
        return

    from pathlib import Path
    model_name = "yolo11n.pt"
    ov_dir = Path("yolo11n_openvino_model")

    print(f"Checking base model '{model_name}'...")
    try:
        model = YOLO(model_name)
    except Exception as e:
        print(f"  Failed to load {model_name}: {e}")
        return

    if not ov_dir.exists():
        print(f"Exporting {model_name} to OpenVINO FP16 format (this happens once)...")
        try:
            model.export(format="openvino", half=True)
            print(f"  [OK] Export completed to '{ov_dir}/'")
        except Exception as e:
            print(f"  [FAILED] Export failed: {e}")
            return
    else:
        print(f"  [OK] Found existing OpenVINO model in '{ov_dir}/'")

    # Load OpenVINO model
    ov_model = YOLO(str(ov_dir), task="detect")
    dummy_frame = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

    # Benchmark CPU
    print("\nBenchmarking OpenVINO on CPU (warmup + 20 frames)...")
    _ = ov_model.predict(dummy_frame, device="CPU", verbose=False)
    t0 = time.perf_counter()
    iters = 20
    for _ in range(iters):
        _ = ov_model.predict(dummy_frame, device="CPU", verbose=False)
    cpu_fps = iters / (time.perf_counter() - t0)
    print(f"  OpenVINO CPU FPS : {cpu_fps:.1f} FPS")

    # Benchmark Intel GPU if present
    if intel_gpu_target:
        print(f"\nBenchmarking OpenVINO on Intel GPU ({intel_gpu_target}) (warmup + 20 frames)...")
        try:
            _ = ov_model.predict(dummy_frame, device=intel_gpu_target, verbose=False)
            t0 = time.perf_counter()
            for _ in range(iters):
                _ = ov_model.predict(dummy_frame, device=intel_gpu_target, verbose=False)
            gpu_fps = iters / (time.perf_counter() - t0)
            print(f"  OpenVINO GPU FPS : {gpu_fps:.1f} FPS")
            speedup = gpu_fps / cpu_fps if cpu_fps > 0 else 1.0
            print(f"  Intel Iris Xe Speedup: {speedup:.2f}x vs CPU")
        except Exception as e:
            print(f"  [GPU Error]: {e}")
            print("  Note: If GPU initialization fails, Intel Graphics driver update may be needed.")


if __name__ == "__main__":
    check_python_environment()
    devices, gpu_target = check_openvino_devices()
    if "openvino" in sys.modules or gpu_target or devices:
        benchmark_model(gpu_target)
    else:
        print("\nPlease install OpenVINO first:")
        print("  pip install openvino\n")
