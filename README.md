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
            "data": {
                  "pattern": string, //Слово, которое нужно найти
                  "max_area": int,   //необязательный параметр (по-умолчанию 35000),  
                                     //позволяет задать максимальную площадт блока, в котором может находится слово
                  "min_area": int,   //необязательный параметр (по-умолчанию 5000),
                                     //позволяет задать минимальную площадь блока, в котором может находится слово
                  "start_page": int  //необязательный параметр, по-умолчанию None
                                     //позволяет задать страницу, с которой начнется поиск слова (может быть отрицательным)
                  "stop_page": int   //необязательный параметр, по-умолчанию None
                                     //позволяет задать страницу, на которой закончится поиск слова (может быть отрицательным)
                  "b64_data": string //pdf в формате base64
            }       
        }
    ```
- Response POST: https://localhost:45000/protocols/find-coordinates
     ```javascript
        {
            "data": {
                "count_pages": int, //кол-во страниц в документе
                "matches": [ //массив со всеми совпадения которые удалось найти
                    {
                        "coords": { //коодинаты блока с совпадением
                            "x": int,
                            "y": int
                        },
                        "page": int //страница, на которой найдено совпадение
                    }
                ],
                "b64_pdf": string
            }
        }
     ```
        



