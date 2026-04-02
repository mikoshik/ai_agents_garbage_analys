#!/bin/bash

# Скрипт для настройки Raspberry Pi 4 (2GB) под проект хакатона

echo "🔄 Обновление системы..."
sudo apt update && sudo apt upgrade -y

echo "📦 Установка системных зависимостей (OpenCV, CMake, BLAS, FFmpeg)..."
sudo apt install -y build-essential cmake git wget libopenblas-dev libopencv-dev python3-opencv ffmpeg

echo "🐍 Установка Python-библиотек..."
pip3 install -r requirements.txt

echo "🧱 Сборка llama.cpp с оптимизацией под ARM (NEON + OpenBLAS)..."
if [ ! -d "llama.cpp" ]; then
    git clone https://github.com/ggerganov/llama.cpp
fi
cd llama.cpp
mkdir -p build && cd build
cmake .. -DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS
make -j4 # Задействуем все 4 ядра Raspberry Pi 4
cd ../..

echo "📥 Загрузка моделей moondream2 (если еще нет)..."
if [ ! -f "moondream2-q4_k.gguf" ]; then
    wget -O moondream2-q4_k.gguf https://huggingface.co/salivosa/moondream2-gguf/resolve/main/moondream2-q4_k.gguf
fi
if [ ! -f "moondream2-mmproj-f16.gguf" ]; then
    wget -O moondream2-mmproj-f16.gguf https://huggingface.co/salivosa/moondream2-gguf/resolve/main/moondream2-mmproj-f16.gguf
fi

echo "✅ Настройка завершена! Можно запускать: python3 main.py"
