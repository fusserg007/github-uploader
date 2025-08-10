#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Uploader - Простая рабочая версия
"""

import os
import sys
import json
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import requests
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

CONFIG_FILE = 'github_config.json'
DEFAULT_CONFIG = {
    "github_token": "",
    "github_username": "",
    "default_private": False,
    "default_description": ""
}

def load_config():
    """Загрузка конфигурации"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """Сохранение конфигурации"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False

def is_configured(config):
    """Проверка настройки"""
    return (config.get('github_token', '').strip() != '' and 
            config.get('github_username', '').strip() != '')

def setup_github():
    """Настройка GitHub"""
    
    root = tk.Tk()
    root.withdraw()

    try:
        username = simpledialog.askstring("GitHub Uploader", "Введите GitHub username:")
        if not username:
            root.destroy()
            return None

        token = simpledialog.askstring("GitHub Uploader", "Введите GitHub token:", show='*')
        if not token:
            root.destroy()
            return None

        # Простая проверка токена
        headers = {'Authorization': f'Bearer {token}'}
        try:
            response = requests.get('https://api.github.com/user', headers=headers, timeout=5)
            if response.status_code != 200:
                messagebox.showerror("Ошибка", "Неверный токен!")
                root.destroy()
                return None
        except:
            messagebox.showerror("Ошибка", "Ошибка подключения к GitHub!")
            root.destroy()
            return None

        config = load_config()
        config['github_username'] = username
        config['github_token'] = token

        if save_config(config):
            messagebox.showinfo("Успех", "Настройки сохранены!")

        root.destroy()
        return config

    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка настройки: {e}")
        root.destroy()
        return None

def create_repo(config, repo_name):
    """Создание репозитория"""
    headers = {
        'Authorization': f'Bearer {config["github_token"]}',
        'Accept': 'application/vnd.github+json'
    }
    
    data = {
        'name': repo_name,
        'private': config.get('default_private', False),
        'auto_init': False
    }
    
    response = requests.post('https://api.github.com/user/repos', headers=headers, json=data)
    
    if response.status_code == 201:
        return response.json()
    elif response.status_code == 422:
        # Репозиторий существует
        repo_url = f"https://api.github.com/repos/{config['github_username']}/{repo_name}"
        response = requests.get(repo_url, headers=headers)
        if response.status_code == 200:
            return response.json()
    
    raise Exception(f"Ошибка создания репозитория: {response.status_code}")

def upload_folder(config, folder_path):
    """Загрузка папки"""
    folder_path = Path(folder_path)
    
    if not folder_path.exists():
        raise Exception("Папка не найдена")
    
    # Проверяем Git
    try:
        subprocess.run(['git', '--version'], capture_output=True, check=True)
    except:
        raise Exception("Git не установлен")
    
    # Получаем имя репозитория
    root = tk.Tk()
    root.withdraw()
    
    repo_name = simpledialog.askstring(
        "GitHub Uploader",
        f"Имя репозитория:",
        initialvalue=folder_path.name
    )
    
    root.destroy()
    
    if not repo_name:
        raise Exception("Операция отменена")
    
    repo_info = create_repo(config, repo_name)
    
    original_cwd = os.getcwd()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_repo = Path(temp_dir) / repo_name
        temp_repo.mkdir()
        
        try:
            os.chdir(temp_repo)
            
            # Git операции
            subprocess.run(['git', 'init'], check=True)
            subprocess.run(['git', 'remote', 'add', 'origin', repo_info['clone_url']], check=True)
            
            # Копируем файлы
            for item in folder_path.iterdir():
                if item.name.startswith('.git'):
                    continue
                
                dest = temp_repo / item.name
                if item.is_file():
                    shutil.copy2(item, dest)
                elif item.is_dir():
                    shutil.copytree(item, dest)
            
            # Коммит и пуш
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], check=True)
            subprocess.run(['git', 'branch', '-M', 'main'], check=True)
            subprocess.run(['git', 'push', '-u', 'origin', 'main'], check=True)
            
            return repo_info['html_url']
            
        finally:
            os.chdir(original_cwd)

def main_menu(config):
    """Главное меню"""
    root = tk.Tk()
    root.title("GitHub Uploader - Simple")
    root.geometry("400x300")
    
    # Центрируем окно
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (400 // 2)
    y = (root.winfo_screenheight() // 2) - (300 // 2)
    root.geometry(f"400x300+{x}+{y}")
    
    tk.Label(root, text="GitHub Uploader", font=("Arial", 16, "bold")).pack(pady=20)
    
    if is_configured(config):
        tk.Label(root, text=f"Пользователь: {config['github_username']}").pack(pady=10)
    else:
        tk.Label(root, text="Не настроено", fg="red").pack(pady=10)
    
    def on_settings():
        root.destroy()
        new_config = setup_github()
        if new_config:
            main_menu(new_config)
    
    def on_upload():
        folder = filedialog.askdirectory(title="Выберите папку")
        if folder:
            try:
                if not is_configured(config):
                    messagebox.showerror("Ошибка", "Сначала настройте GitHub!")
                    return
                
                url = upload_folder(config, folder)
                messagebox.showinfo("Успех", f"Загружено!\n{url}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
    
    tk.Button(root, text="Настройки", command=on_settings, width=20, height=2).pack(pady=10)
    tk.Button(root, text="Загрузить папку", command=on_upload, width=20, height=2).pack(pady=10)
    tk.Button(root, text="Выход", command=root.quit, width=20, height=2).pack(pady=10)
    
    root.mainloop()

def main():
    """Главная функция"""
    
    try:
        config = load_config()
        
        # Если запущен с папкой как аргумент
        if len(sys.argv) > 1:
            folder_path = sys.argv[1]
            
            if not is_configured(config):
                config = setup_github()
                if not config:
                    return
            
            try:
                url = upload_folder(config, folder_path)
                print(f"Успех! {url}")
                
                root = tk.Tk()
                root.withdraw()
                messagebox.showinfo("Успех", f"Загружено!\n{url}")
                root.destroy()
                
            except Exception as e:
                print(f"Ошибка: {e}")
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("Ошибка", str(e))
                root.destroy()
        else:
            # Главное меню
            main_menu(config)
            
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Ошибка", f"Критическая ошибка:\n{e}")
            root.destroy()
        except:
            pass

if __name__ == "__main__":
    main()