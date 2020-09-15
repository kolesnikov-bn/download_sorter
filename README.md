# download_sorter
Сортировщик скаченных файлов. Предназначен как расширение для Mac Workflow

## Описание
Скрипт предназначен в первую очередь для Mac Workflow, как `action folder`.
По этому он выполнен в виде одного файла

## Запуск и настройка
- Запустить Workflow
- Выбрать Folder Action c целевым каталог, в примере используется каталог `Downloads`
- Перетащить из `Actions -> Utils -> Run Shell Script` в поле Workflow
- скопировать скрипт в `Run Shell Script`
- В шапке скрипта переместить строку `/usr/local/bin/python3 <<'EOF' - "$@"` из doc string в самый верх
    
    **До**
    ```
        """
        /usr/local/bin/python3 <<'EOF' - "$@"
        Команда для запуска в WORKFLOW
        VERSION = "*.*"
        """
    ```
  
    **После**
    ```
        /usr/local/bin/python3 <<'EOF' - "$@"
        """
        Команда для запуска в WORKFLOW
        VERSION = "*.*"
        """
    ```
- Проверить что все работает кнопкой `RUN`
