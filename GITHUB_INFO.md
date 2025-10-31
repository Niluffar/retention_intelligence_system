# GitHub Repository Information

## Repository Details

- **GitHub URL**: https://github.com/Niluffar/retention_intelligence_system
- **Owner**: Niluffar (nilufarsharipova2001@gmail.com)
- **Visibility**: Public
- **Branch**: main

## Clone Repository

```bash
# HTTPS (рекомендуется для начала)
git clone https://github.com/Niluffar/retention_intelligence_system.git

# SSH (если настроен SSH ключ)
git clone git@github.com:Niluffar/retention_intelligence_system.git
```

## Basic Git Commands

### Проверить статус
```bash
git status
```

### Добавить изменения
```bash
# Добавить все изменения
git add .

# Добавить конкретный файл
git add path/to/file.py
```

### Создать коммит
```bash
git commit -m "Описание изменений"
```

### Запушить на GitHub
```bash
git push
```

### Получить последние изменения
```bash
# Скачать изменения
git fetch

# Скачать и применить изменения
git pull
```

### Посмотреть историю коммитов
```bash
git log

# Краткая история
git log --oneline

# С графом
git log --graph --oneline --all
```

## Working with Branches

### Создать новую ветку
```bash
git checkout -b feature/new-feature
```

### Переключиться на ветку
```bash
git checkout main
```

### Посмотреть все ветки
```bash
git branch -a
```

### Удалить ветку
```bash
git branch -d feature/old-feature
```

## Useful Git Configurations

### Настроить line endings для Windows
```bash
git config --global core.autocrlf true
```

### Настроить default editor
```bash
git config --global core.editor "code --wait"
```

### Посмотреть конфигурацию
```bash
git config --list
```

## .gitignore

В проекте уже настроен `.gitignore` который исключает:
- ✅ Виртуальные окружения (venv/, env/)
- ✅ Данные (data/, *.csv, *.parquet, etc.)
- ✅ Credentials (.env, *.key, *.pem)
- ✅ Логи (logs/, *.log)
- ✅ Модели (models/*.pkl, etc.)
- ✅ Python cache (__pycache__/, *.pyc)
- ✅ IDE файлы (.vscode/, .idea/)

## GitHub Authentication

### Вариант 1: Personal Access Token (рекомендуется)

1. Перейдите на https://github.com/settings/tokens
2. Нажмите "Generate new token (classic)"
3. Выберите scopes: `repo` (full control)
4. Скопируйте токен
5. При git push используйте токен вместо пароля:
   - Username: `Niluffar`
   - Password: `<ваш токен>`

### Вариант 2: SSH Key

```bash
# Генерация SSH ключа
ssh-keygen -t ed25519 -C "nilufarsharipova2001@gmail.com"

# Копировать публичный ключ
cat ~/.ssh/id_ed25519.pub

# Добавить на GitHub:
# https://github.com/settings/keys
```

## Collaborative Workflow

### Pull Request Process

1. Создайте новую ветку для фичи
```bash
git checkout -b feature/my-feature
```

2. Внесите изменения и закоммитьте
```bash
git add .
git commit -m "Add new feature"
```

3. Запушьте ветку
```bash
git push -u origin feature/my-feature
```

4. Откройте Pull Request на GitHub
5. После ревью, смержите в main

### Syncing with Main

```bash
# Переключиться на main
git checkout main

# Получить последние изменения
git pull

# Вернуться на вашу ветку
git checkout feature/my-feature

# Обновить вашу ветку
git merge main
# или
git rebase main
```

## Important Files Not to Commit

⚠️ **НИКОГДА не коммитьте**:
- `.env` файлы с credentials
- `data/` директория с данными
- `models/` с большими моделями
- Personal API keys или tokens
- Database passwords

Эти файлы уже в `.gitignore`, но будьте внимательны!

## GitHub Repository Settings

Рекомендуемые настройки (в GitHub web interface):

1. **Settings → Branches**:
   - Добавьте branch protection rules для `main`
   - Require pull request reviews
   - Require status checks

2. **Settings → Secrets**:
   - Добавьте секреты для CI/CD если нужно

3. **Settings → Collaborators**:
   - Добавьте членов команды

## Project Links

- 📖 [README.md](README.md) - Project overview
- 📖 [SETUP_SUMMARY.md](SETUP_SUMMARY.md) - Quick start guide
- 📖 [GETTING_STARTED.md](docs/GETTING_STARTED.md) - Detailed instructions
- 📋 [CHECKLIST.md](CHECKLIST.md) - Development checklist

## Support

Если возникнут проблемы с Git/GitHub:
1. Проверьте `git status`
2. Проверьте `.gitignore`
3. Проверьте remote: `git remote -v`
4. Проверьте branch: `git branch -a`

---

**Repository initialized and pushed**: 2025-10-30
**Initial commit**: 35 files, 2916+ lines of code
