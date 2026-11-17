# TG WS Proxy — версия BomBilka

Локальный MTProto → WebSocket прокси для Telegram Desktop.
Первая целевая платформа — Windows 10/11 x64.

Основано на [Flowseal/tg-ws-proxy](https://github.com/Flowseal/tg-ws-proxy),
исходный коммит: `6690b78`. Лицензия MIT, авторство оригинала сохранено в LICENSE.
Это начальная версия форка: устранение конкретной проблемы подключения
пока не подтверждено. Доступность зависит от сети и адресов Telegram.

## Скачать и запустить

1. Откройте вкладку Actions → Windows build → последний успешный запуск.
2. Скачайте архив TgWsProxy-Windows-x64 в разделе Artifacts и распакуйте.
3. Запустите TgWsProxy_windows.exe. Программа появится в системном трее.
4. В меню трея выберите «Открыть в Telegram» и подтвердите подключение.

Python для готового EXE не нужен. Первая сборка не имеет цифровой подписи.
Сборка запускается при отправке изменений в main и вручную через Run workflow.
Теги вида v1.11.4 публикуют EXE также во вкладке Releases.

## Отличия этой версии

- Отдельная сборка Windows x64 без зависимости от сертификата подписи автора.
- Тесты перед сборкой, SHA256SUMS.txt рядом с EXE.
- Обновления проверяются в BomBilka1/tgwsproxy.
- Настройки хранятся отдельно: `%APPDATA%\TgWsProxyBomBilka`.
- Для переносного режима запустите EXE с `--portable`;
  данные появятся в `TgWsProxyBomBilka_data` рядом с ним.

Сетевой механизм унаследован от оригинала, включая общий список CF-прокси
и его обновление из репозитория Flowseal. Собственные домены можно задать
в настройках; инструкции сохранены в [документации](docs/README.md).

## Запуск из исходников на Windows

Требуется Python 3.11 x64 с Tkinter. Команды PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install . pyinstaller==6.13.0
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe windows.py
# Сборка EXE:
.\.venv\Scripts\python.exe -m PyInstaller packaging/windows.spec --noconfirm
```

При неполадках откройте «Открыть логи» в меню трея.
Перед публикацией логов удалите secret и ссылку подключения к прокси.
