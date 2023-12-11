# urfum_hack_3
# Название проекта

Описание цели проекта и его функциональности.

## Начало работы

Инструкции по настройке окружения для скачивания и запуска проекта локально.

Для сборки контейнеров:

1. перейти в `src` (`cd <...>/urfum_hack_3/src/`)
2. построить образ для API `docker build -t urfum/prescoring_api -f DockerfileApi .`
3. построить образ для WORKER `docker build -t urfum/prescoring_worker -f DockerfileWorker .`
4. запустить образы (с учетом проброса портов из докера наружу)

> Воркеры запускаются только **после** запуска api! Иначе базы не инициализируются!

Или можно так:
1. Запускаем сборку контейнеров: docker-compose build
2. Стартуем: docker-compose up
3. Пользуемся
4. Стопаем: docker-compose down

**TODO:**

* структура данных под финальную модель
* возвращать помимо скора объяснение решения (для каждого банка)
* подбор опимальной суммы/срока для конкретной анкеты

## Использование

Примеры, как использовать ваш продукт для решения проблем.

## Команда

Информация о членах команды и их ролях.

Искужин Ирамаль Р. - [Github](https://github.com/Lemeri02), [Telegram](https://t.me/lemeri)
Толстых А.А. - [GitHub](https://github.com/xausssr)

## Лицензия
