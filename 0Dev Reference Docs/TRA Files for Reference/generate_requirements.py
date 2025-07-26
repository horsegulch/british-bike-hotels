import subprocess
import os

venv_python = r"C:\Users\unwan\Documents\Ride Archive\venv\Scripts\python.exe"
output_file = r"C:\Users\unwan\Documents\Ride Archive\requirements.txt"

try:
    result = subprocess.run([venv_python, "-m", "pip", "freeze"], capture_output=True, text=True, check=True)
    with open(output_file, "w") as f:
        f.write(result.stdout)
    print("requirements.txt generated successfully.")
except subprocess.CalledProcessError as e:
    print(f"Error generating requirements.txt: {e}")
    print(f"Stderr: {e.stderr}")
except FileNotFoundError:
    print(f"Error: Python executable not found at {venv_python}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
