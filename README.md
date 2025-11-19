# Foodgram — «Продуктовый помощник»

## Описание

Foodgram — это сервис для публикации рецептов и работы со списком покупок.

### Пользователь может:
- зарегистрироваться и авторизоваться по e-mail;
- публиковать рецепты с фотографиями, тегами и ингредиентами;
- добавлять рецепты в избранное;
- формировать список покупок на основе корзины (shopping cart) и скачивать его в виде текстового файла;
- подписываться на других авторов;
- получать короткие ссылки на рецепты.

Проект удобен как «личная кулинарная книга» с возможностью делиться рецептами и быстро собирать список продуктов для похода в магазин.

### Продакшн-версия развернута на виртуальной машине:
- Веб-интерфейс и API: http://89.169.177.182:8090/
--Корень API: http://89.169.177.182:8090/api/
- Health-чек API: http://89.169.177.182:8090/api/health/

## Технологии
- Python 3.12
- Django 5
- Django REST Framework
- PostgreSQL 16
- Djoser (аутентификация по токену)
- Nginx
- Docker, Docker Compose
- Node 18 (сборка фронтенда)

---

## Установка и запуск на локальной машине (Docker)

### 1. Предварительные требования:
- Установлен Docker
- Свободен порт 8090 на хосте

### 2. Клонирование репозитория
```bash
git clone https://github.com/YanaKachalova/foodgram.git
```

Дальнейшие команды выполняются из корня проекта

### 3. Настройка переменных окружения
Создать файл .env в корне проекта по шаблону .env.example:
```bash
cp .env.example .env
```

Открыть .env и заполнить/проверить значения:
```bash
DJANGO_SECRET_KEY=secret-key # обязательно поменять
DEBUG=0 # для локальной отладки можно поставить 1

ALLOWED_HOSTS=localhost,127.0.0.1,89.169.177.182,backend,nginx

POSTGRES_DB=foodgram
POSTGRES_USER=foodgram
POSTGRES_PASSWORD=foodgram
DB_HOST=db
DB_PORT=5432

PAGE_SIZE=6
```

Для локального запуска достаточно localhost и 127.0.0.1 в ALLOWED_HOSTS.

### 4. Запуск контейнеров
Перейти в папку infra и поднять проект:
```bash
cd infra
docker compose up -d --build
```

Docker Compose поднимет сервисы:
- foodgram_db — база данных PostgreSQL;
- foodgram_backend — Django-приложение (миграции и collectstatic выполняются автоматически);
- foodgram_frontend — однократно собирает фронтенд;
- foodgram_proxy — Nginx, отдаёт фронтенд и проксирует запросы к API.

После успешного запуска:
- фронтенд: http://localhost:8090/
- API: http://localhost:8090/api/
- health-чек: http://localhost:8090/api/health/

Проверить статус контейнеров:
```bash
docker compose ps
```

### 5. Создание суперпользователя
Для доступа в админ-панель (http://localhost:8090/admin/):
```bash
docker compose exec backend python manage.py createsuperuser
```

Следовать инструкциям в консоли.

### 6.1. Загрузка только списка ингредиентов

В проекте есть management-команда, которая загружает только ингредиенты из CSV-файла data/ingredients.csv:
```bash
docker compose exec backend python manage.py load_ingredients
```

### 6.1. Загрузка тестовых данных

Файл data/test_data.json содержит тестовые данные:
- пользователей,
- теги,
- ингредиенты,
- рецепты с изображениями,
- связи (избранное, корзина — если присутствуют).

Для загрузки тестовых данных:
```bash
docker compose exec backend python manage.py loaddata data/test_data.json
```

---

## Примеры запросов к API

Во всех примерах ниже базовый URL — локальный: http://localhost:8090/api/. Для продакшн-сервера нужно заменить http://localhost:8090 на http://89.169.177.182:8090.

### 1. Регистрация пользователя

Запрос:
```bash
curl -X POST http://localhost:8090/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "user123",
    "first_name": "Иван",
    "last_name": "Иванов",
    "password": "strong_password_123"
  }'
```

Ответ (201) — данные созданного пользователя (без пароля).

### 2. Получение списка рецептов

Запрос:
```bash
curl http://localhost:8090/api/recipes/
```

Поддерживаются фильтры:
- tags — несколько slug'ов тегов, например: ?tags=breakfast&tags=dinner
- author — id автора
- is_favorited — 1 / 0
- is_in_shopping_cart — 1 / 0
- name — поиск по части названия

Пример:
```bash
curl "http://localhost:8090/api/recipes/?tags=breakfast&is_favorited=1"
```

### 3. Создание рецепта

Требуется авторизация.
Запрос:
```bash
curl -X POST http://localhost:8090/api/recipes/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <auth_token>" \
  -d '{
    "name": "Яичница с помидорами",
    "text": "Взбить яйца, обжарить с помидорами на сковороде.",
    "cooking_time": 10,
    "tags": [1],
    "ingredients": [
      {"id": 1, "amount": 2},
      {"id": 5, "amount": 50}
    ],
    "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA..."
  }'
```

- tags — список ID тегов;
- ingredients — список объектов с полями id (ID ингредиента) и amount (количество);
- image — строка в формате Base64 (см. Base64ImageField).

### 4. Работа с избранным

Требуется авторизация.

Добавить рецепт в избранное
```bash
curl -X POST http://localhost:8090/api/recipes/1/favorite/ \
  -H "Authorization: Token <auth_token>"
```

Ответ — сериализованный рецепт (см. RecipeReadSerializer).


Удалить рецепт из избранного
```bash
curl -X DELETE http://localhost:8090/api/recipes/1/favorite/ \
  -H "Authorization: Token <auth_token>"
```

Успешный ответ — статус 204 No Content.

### 5. Список покупок (shopping cart) и скачивание файла

Требуется авторизация.
Добавить рецепт в список покупок:
```bash
curl -X POST http://localhost:8090/api/recipes/1/shopping_cart/ \
  -H "Authorization: Token <auth_token>"
```

Удалить рецепт из списка покупок:
```bash
curl -X DELETE http://localhost:8090/api/recipes/1/shopping_cart/ \
  -H "Authorization: Token <auth_token>"
```

Скачать список покупок:
```bash
curl -X GET http://localhost:8090/api/recipes/download_shopping_cart/ \
  -H "Authorization: Token <auth_token>" \
  -OJ
```

Ответ — текстовый файл shopping_cart.txt в кодировке UTF-8, формируемый во вью download_shopping_cart.

### 6. Подписки на авторов

Требуется авторизация.
Подписаться на автора:
```bash
curl -X POST http://localhost:8090/api/users/2/subscribe/ \
  -H "Authorization: Token <auth_token>"
```

Отписаться от автора:
```bash
curl -X DELETE http://localhost:8090/api/users/2/subscribe/ \
  -H "Authorization: Token <auth_token>"
```

Получить список подписок:
```bash
curl http://localhost:8090/api/users/subscriptions/ \
  -H "Authorization: Token <auth_token>"
```
