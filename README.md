## General info
Данное приложение поможет вам найти ключевые фразы в pdf документе.

## How to run
Как запустить приложение:
- Step 1: Убедитесь в том, что у вас установлен [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

- Step 2: Склонируйте репозиторий введя команду: `git clone https://github.com/CookIsGood/pdf-finder.git`

- Step 3: Убедитесь в том, что у вас установлен [Docker](https://docs.docker.com/engine/install)

- Step 4: Перейдите в папку приложения и создайте image приложения введя команду `docker build -t recognizer-app:latest .`

- Step 6: Запустите контейнер приложения с помощью команды `docker run -p 45000:80 recognizer-app:latest`

## How to use
Как пользоваться приложением?

- Request POST: https://localhost:45000/protocols/find-coordinates
     ```javascript
        {
            "data": string      
        }
    ```
- Response POST: https://localhost:45000/protocols/find-coordinates
     ```javascript
        {
            "data": {
                "x": int, 
                "y": int
            }
        }
     ```
      
