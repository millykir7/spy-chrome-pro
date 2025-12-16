#!/bin/bash

# --- НАСТРОЙКИ ---
APP_NAME="SpyChromePro"
BUNDLE_ID="com.spy.chrome.pro"
MAIN_SCRIPT="main.py"
SOURCE_ICON="icon.png"
FINAL_ICON="AppIcon.icns"

echo "🚀 ЗАПУСК СУПЕР-СБОРКИ..."

# 1. МАГИЯ ИКОНОК (Если есть icon.png)
if [ -f "$SOURCE_ICON" ]; then
    echo "🎨 Создаю профессиональную .icns иконку из $SOURCE_ICON..."
    
    # Создаем временную папку для набора иконок
    ICONSET_DIR="MyIcon.iconset"
    mkdir -p "$ICONSET_DIR"

    # Генерируем все необходимые размеры (Standard + Retina)
    # Нормальные размеры
    sips -z 16 16     "$SOURCE_ICON" --out "$ICONSET_DIR/icon_16x16.png" > /dev/null
    sips -z 32 32     "$SOURCE_ICON" --out "$ICONSET_DIR/icon_32x32.png" > /dev/null
    sips -z 128 128   "$SOURCE_ICON" --out "$ICONSET_DIR/icon_128x128.png" > /dev/null
    sips -z 256 256   "$SOURCE_ICON" --out "$ICONSET_DIR/icon_256x256.png" > /dev/null
    sips -z 512 512   "$SOURCE_ICON" --out "$ICONSET_DIR/icon_512x512.png" > /dev/null

    # Retina (2x) размеры
    sips -z 32 32     "$SOURCE_ICON" --out "$ICONSET_DIR/icon_16x16@2x.png" > /dev/null
    sips -z 64 64     "$SOURCE_ICON" --out "$ICONSET_DIR/icon_32x32@2x.png" > /dev/null
    sips -z 256 256   "$SOURCE_ICON" --out "$ICONSET_DIR/icon_128x128@2x.png" > /dev/null
    sips -z 512 512   "$SOURCE_ICON" --out "$ICONSET_DIR/icon_256x256@2x.png" > /dev/null
    sips -z 1024 1024 "$SOURCE_ICON" --out "$ICONSET_DIR/icon_512x512@2x.png" > /dev/null

    # Конвертируем папку в единый .icns файл
    iconutil -c icns "$ICONSET_DIR" -o "$FINAL_ICON"
    
    # Убираем мусор
    rm -rf "$ICONSET_DIR"
    echo "✅ Иконка готова: $FINAL_ICON"
    
    # Добавляем параметр иконки для PyInstaller
    ICON_PARAM="--icon=$FINAL_ICON"
else
    echo "⚠️ Файл icon.png не найден! Сборка пойдет со стандартной иконкой Python."
    ICON_PARAM=""
fi

# 2. Настройка окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание venv..."
    python3 -m venv venv
fi
source venv/bin/activate

echo "⬇️ Проверка библиотек..."
pip install --upgrade pip
pip install PyQt6 SpeechRecognition pyautogui pyaudio pyinstaller

# 3. Очистка старого
rm -rf build dist "$APP_NAME.spec" "$APP_NAME.dmg"

# 4. Сборка (Теперь с иконкой!)
echo "🔨 Компиляция..."
pyinstaller --noconfirm --windowed --name "$APP_NAME" \
    --osx-bundle-identifier "$BUNDLE_ID" \
    $ICON_PARAM \
    --hidden-import=pyaudio \
    --hidden-import=speech_recognition \
    --hidden-import=pyautogui \
    "$MAIN_SCRIPT"

# 5. Настройка прав (Info.plist)
PLIST="dist/$APP_NAME.app/Contents/Info.plist"
echo "🔧 Внедрение прав в $PLIST..."

plutil -remove NSMicrophoneUsageDescription "$PLIST" 2>/dev/null
plutil -remove NSAppleEventsUsageDescription "$PLIST" 2>/dev/null
plutil -remove NSACCESSIBILITYUsageDescription "$PLIST" 2>/dev/null

plutil -insert NSMicrophoneUsageDescription -string "Для записи собеседования нужен микрофон." "$PLIST"
plutil -insert NSAppleEventsUsageDescription -string "Для вставки текста нужен доступ к Chrome." "$PLIST"
plutil -insert NSSystemEventsUsageDescription -string "Для управления окнами нужен доступ." "$PLIST"

# 6. Подпись и упаковка
echo "🔏 Подписание..."
codesign --force --deep --sign - "dist/$APP_NAME.app"

echo "💿 Создание DMG..."
hdiutil create -volname "$APP_NAME" -srcfolder "dist/$APP_NAME.app" -ov -format UDZO "$APP_NAME.dmg"

# Чистим сгенерированную иконку, чтобы не мешалась
if [ -f "$FINAL_ICON" ]; then
    rm "$FINAL_ICON"
fi

echo "✅ ГОТОВО! Твой DMG с иконкой здесь: $(pwd)/$APP_NAME.dmg"