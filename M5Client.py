import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, StringVar, OptionMenu, Toplevel
import requests
import serial
import serial.tools.list_ports
import os
import threading

data_directory = os.path.join(os.getenv('APPDATA'), 'm5client_data')
os.makedirs(data_directory, exist_ok=True)

required_files = {
    "cathack.png": "https://github.com/Teapot321/M5Client/raw/main/Background/cathack.png",
    "bruce.png": "https://github.com/Teapot321/M5Client/raw/main/Background/bruce.png",
    "nemo.png": "https://github.com/Teapot321/M5Client/raw/main/Background/nemo.png",
    "m5launcher.png": "https://github.com/Teapot321/M5Client/raw/main/Background/m5launcher.png",
    "marauder.png": "https://github.com/Teapot321/M5Client/raw/main/Background/marauder.png",
    "esptool.exe": "https://github.com/Teapot321/M5Client/raw/refs/heads/main/esptool.exe"
}

def check_and_download_files():
    for filename, url in required_files.items():
        file_path = os.path.join(data_directory, filename)
        if not os.path.exists(file_path):
            download_file(url, file_path)

def download_file(url, file_path):
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print(f"Файл {file_path} загружен.")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить {file_path}: {e}")

def install_requirements():
    required_packages = [
        "requests",
        "pyserial",
        "tkinterdnd2",
    ]
    for package in required_packages:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def install_esptool():
    esptool_path = os.path.join(data_directory, 'esptool.exe')
    if not os.path.exists(esptool_path):
        def download_esptool():
            try:
                download_file(required_files["esptool.exe"], esptool_path)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось установить esptool: {e}")
        threading.Thread(target=download_esptool).start()

def download_driver(driver_url, driver_name):
    driver_path = os.path.join(data_directory, driver_name)
    block_buttons()
    loading_window = Toplevel(root)
    loading_window.title("M5Client | v2.4")
    loading_window.geometry("300x100")
    loading_window.configure(bg="#050403")
    loading_label = tk.Label(loading_window, text="Скачивание драйвера...", bg="#050403", fg="#ffffff", font=("Arial", 14))
    loading_label.pack(pady=20)
    root.update()

    def download():
        try:
            response = requests.get(driver_url)
            with open(driver_path, 'wb') as f:
                f.write(response.content)
            subprocess.run(driver_path, check=True)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось установить драйвер: {e}")
        finally:
            loading_window.destroy()
            unblock_buttons()

    threading.Thread(target=download).start()

def open_driver_menu():
    driver_menu_window = Toplevel(root)
    driver_menu_window.title("M5Client | v2.4")
    driver_menu_window.geometry("300x200")
    driver_menu_window.configure(bg="#050403")
    label = tk.Label(driver_menu_window, text="Drivers:", bg="#050403", fg="#ffffff", font=("Arial", 12))
    label.pack(pady=10)

    ch9102_button = tk.Button(driver_menu_window, text="CH9102", command=lambda: download_driver(
        "https://github.com/Teapot321/M5Client/raw/refs/heads/main/Drivers/CH9102.exe", "CH9102.exe"),
        bg="#050403", fg="#ffffff")
    ch9102_button.pack(pady=5)

    ch340_button = tk.Button(driver_menu_window, text="CH340", command=lambda: download_driver(
        "https://github.com/Teapot321/M5Client/raw/refs/heads/main/Drivers/CH341SER.EXE", "CH341SER.EXE"),
        bg="#050403", fg="#ffffff")
    ch340_button.pack(pady=5)

    def on_enter(button):
        button.config(bg="white", fg="#050403")

    def on_leave(button):
        button.config(bg="#050403", fg="#ffffff")

    ch9102_button.bind("<Enter>", lambda e: on_enter(ch9102_button))
    ch9102_button.bind("<Leave>", lambda e: on_leave(ch9102_button))
    ch340_button.bind("<Enter>", lambda e: on_enter(ch340_button))
    ch340_button.bind("<Leave>", lambda e: on_leave(ch340_button))

def download_and_install_driver():
    open_driver_menu()

def install_firmware():
    try:
        firmware_url = get_latest_firmware_url()
        firmware_path = os.path.join(data_directory, "latest_firmware.bin")
        response = requests.get(firmware_url)
        with open(firmware_path, 'wb') as f:
            f.write(response.content)
        flash_firmware(firmware_path)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить прошивку: {e}")

def flash_firmware(firmware_path):
    com_port = com_port_var.get()
    esptool_path = os.path.join(data_directory, 'esptool.exe')
    loading_window = Toplevel(root)
    loading_window.title("M5Client | v2.4")
    loading_window.geometry("300x100")
    loading_window.configure(bg="#050403")
    loading_label = tk.Label(loading_window, text="Прошивка устройства...", bg="#050403", fg="#ffffff", font=("Arial", 14))
    loading_label.pack(pady=20)
    root.update()

    def flash_device():
        try:
            command = [esptool_path, '--port', com_port, '--baud', '1500000', 'write_flash', '0x00000', firmware_path]
            subprocess.run(command, check=True)
            messagebox.showinfo("Успех", "Прошивка установлена успешно!")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Ошибка", f"Не удалось прошить устройство: {e}")
        finally:
            loading_window.destroy()
            unblock_buttons()

    threading.Thread(target=flash_device).start()

def start_installation():
    install_button.config(state=tk.DISABLED)
    install_firmware()

def block_buttons():
    install_button.config(state=tk.DISABLED, bg="gray", fg="white")
    com_port_menu.config(state=tk.DISABLED, bg="gray", fg="white")
    driver_button.config(state=tk.DISABLED, bg="gray", fg="white")
    switch_firmware_button.config(state=tk.DISABLED, bg="gray", fg="white")
    device_menu.config(state=tk.DISABLED, bg="gray", fg="white")

def unblock_buttons():
    install_button.config(state=tk.NORMAL, bg="#050403", fg="#ff8e19")
    com_port_menu.config(state=tk.NORMAL, bg="#050403", fg="#ff8e19")
    driver_button.config(state=tk.NORMAL, bg="#050403", fg="#ff8e19")
    switch_firmware_button.config(state=tk.NORMAL, bg="#050403", fg="#ff8e19")
    device_menu.config(state=tk.NORMAL, bg="#050403", fg="#ff8e19")
    update_button_colors()

def get_com_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

root = tk.Tk()
root.title("M5Client | v2.4")
root.configure(bg="#050403")
root.geometry("600x350")
root.resizable(False, False)

check_and_download_files()

cat_hack_image = tk.PhotoImage(file=os.path.join(data_directory, "cathack.png"))
bruce_image = tk.PhotoImage(file=os.path.join(data_directory, "bruce.png"))
nemo_image = tk.PhotoImage(file=os.path.join(data_directory, "nemo.png"))
m5launcher_image = tk.PhotoImage(file=os.path.join(data_directory, "m5launcher.png"))
marauder_image = tk.PhotoImage(file=os.path.join(data_directory, "marauder.png"))

img = tk.Label(root, image=cat_hack_image, bg="#050403")
img.place(relx=0.5, rely=0.0, anchor='n')

install_button = tk.Button(root, text="Install", command=lambda: threading.Thread(target=start_installation).start(),
                           bg="#050403", fg="#ff8e19", borderwidth=2, relief="solid", highlightbackground="#d9d9d9",
                           highlightcolor="white", font=("Fixedsys", 20))

driver_button = tk.Button(root, text="Driver", command=download_and_install_driver,
                          bg="#050403", fg="#ff8e19", borderwidth=2, relief="solid", highlightbackground="#d9d9d9",
                          highlightcolor="white", font=("Fixedsys", 11))

current_firmware = StringVar(value="CatHack")

def switch_firmware():
    global current_firmware
    if current_firmware.get() == "CatHack":
        current_firmware.set("Bruce")
        switch_firmware_button.config(text="Bruce")
        img.config(image=bruce_image)
    elif current_firmware.get() == "Bruce":
        current_firmware.set("Nemo")
        switch_firmware_button.config(text="Nemo")
        img.config(image=nemo_image)
    elif current_firmware.get() == "Nemo":
        current_firmware.set("Marauder")
        switch_firmware_button.config(text="Marauder")
        img.config(image=marauder_image)
    elif current_firmware.get() == "Marauder":
        current_firmware.set("M5Launcher")
        switch_firmware_button.config(text="M5Launcher")
        img.config(image=m5launcher_image)
    else:
        current_firmware.set("CatHack")
        switch_firmware_button.config(text="CatHack")
        img.config(image=cat_hack_image)

    device_var.set("Plus2")
    update_device_options()
    update_button_colors()

def update_device_options():
    current_firmware_value = current_firmware.get()
    device_menu['menu'].delete(0, 'end')
    if current_firmware_value == "CatHack":
        device_menu['menu'].add_command(label='Plus2', command=lambda: device_var.set('Plus2'))
    elif current_firmware_value == "M5Launcher":
        device_menu['menu'].add_command(label='Plus2', command=lambda: device_var.set('Plus2'))
        device_menu['menu'].add_command(label='Plus1', command=lambda: device_var.set('Plus1'))
        device_menu['menu'].add_command(label='Cardputer', command=lambda: device_var.set('Cardputer'))
    elif current_firmware_value == "Marauder":
        device_menu['menu'].add_command(label='Plus2', command=lambda: device_var.set('Plus2'))
        device_menu['menu'].add_command(label='Plus1', command=lambda: device_var.set('Plus1'))
        device_menu['menu'].add_command(label='Cardputer', command=lambda: device_var.set('Cardputer'))
    else:
        device_menu['menu'].add_command(label='Plus2', command=lambda: device_var.set('Plus2'))
        device_menu['menu'].add_command(label='Plus1', command=lambda: device_var.set('Plus1'))
        device_menu['menu'].add_command(label='Cardputer', command=lambda: device_var.set('Cardputer'))

def update_button_colors():
    if current_firmware.get() == "Nemo":
        color = "#060606"
        text_color = "#7d9f71"
    elif current_firmware.get() == "Bruce":
        color = "#030407"
        text_color = "#a82da4"
    elif current_firmware.get() == "M5Launcher":
        color = "#030703"
        text_color = "#9cb597"
    elif current_firmware.get() == "Marauder":
        color = "#000000"
        text_color = "#c3c3c3"
    else:
        color = "#050403"
        text_color = "#ff8e19"

    install_button.config(bg=color, fg=text_color)
    com_port_menu.config(bg=color, fg=text_color)
    driver_button.config(bg=color, fg=text_color)
    switch_firmware_button.config(bg=color, fg=text_color)
    device_menu.config(bg=color, fg=text_color)

switch_firmware_button = tk.Button(root, text="CatHack", command=switch_firmware,
                                   bg="#050403", fg="#ff8e19", borderwidth=2, relief="solid",
                                   highlightbackground="#d9d9d9", highlightcolor="white", font=("Fixedsys", 11))

device_var = StringVar(root)
device_var.set("Plus2")

device_menu = OptionMenu(root, device_var, "Plus2")
device_menu.config(bg="#050403", fg="#ff8e19", highlightbackground="#161615", borderwidth=2)

com_port_var = StringVar(root)
com_ports = get_com_ports()
com_port_var.set(com_ports[0] if com_ports else "Нет доступных портов")

com_port_menu = OptionMenu(root, com_port_var, *com_ports)
com_port_menu.config(bg="#050403", fg="#ff8e19", highlightbackground="#161615", borderwidth=2)

def on_enter_install(event):
    install_button.config(bg="white", fg="#050403", highlightbackground="#d9d9d9")

def on_leave_install(event):
    update_button_colors()

def on_enter_driver(event):
    driver_button.config(bg="white", fg="#050403", highlightbackground="#d9d9d9")

def on_leave_driver(event):
    update_button_colors()

def on_enter_switch(event):
    switch_firmware_button.config(bg="white", fg="#050403", highlightbackground="#d9d9d9")

def on_leave_switch(event):
    update_button_colors()

install_button.bind("<Enter>", on_enter_install)
install_button.bind("<Leave>", on_leave_install)
driver_button.bind("<Enter>", on_enter_driver)
driver_button.bind("<Leave>", on_leave_driver)
switch_firmware_button.bind("<Enter>", on_enter_switch)
switch_firmware_button.bind("<Leave>", on_leave_switch)

install_button.place(relx=0.17, rely=0.11, anchor='center')
com_port_menu.place(relx=0.37, rely=0.11, anchor='center')
driver_button.place(relx=0.5, rely=0.93, anchor='center')
switch_firmware_button.place(relx=0.85, rely=0.05, anchor='n')
device_menu.place(relx=0.525, rely=0.11, anchor='center')

install_button.config(bg="#050403", fg="#ff8e19", highlightbackground="#d9d9d9", borderwidth=2)

install_esptool()

root.mainloop()
