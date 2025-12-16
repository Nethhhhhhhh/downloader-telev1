import os
import shutil

def check_ffmpeg():
    print("--- Diagnostic Start ---")
    
    # Check PATH
    path_bin = shutil.which("ffmpeg")
    print(f"1. shutil.which('ffmpeg'): {path_bin}")
    
    # Check WinGet
    base_path = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
    found_winget = None
    if os.path.exists(base_path):
        print(f"2. WinGet dir exists: {base_path}")
        for root, dirs, files in os.walk(base_path):
            if "ffmpeg.exe" in files:
                found_winget = os.path.join(root, "ffmpeg.exe")
                print(f"   Found in WinGet: {found_winget}")
                break
    else:
        print(f"2. WinGet dir NOT found: {base_path}")

    if found_winget:
        print(f"   dirname to use: {os.path.dirname(found_winget)}")

    print("--- Diagnostic End ---")

if __name__ == "__main__":
    check_ffmpeg()
