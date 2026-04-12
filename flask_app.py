from flask import Flask, request, jsonify
import logging
import random

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

cities = {
    'москва': [
        '1540737/a8be6dd9266d94f069a2',
        '965417/8b714f41c95e85f37000'
    ],
    'нью-йорк': [
        '1652229/3aacea929ed31da72ba5',
        '1652229/aa99ced8892d18761247'
    ],
    'париж': [
        '1656841/c8ca11a904144e809fc1',
        '965417/dacfdbd47a166db20b3e'
    ]
}

sessionStorage = {}


@app.route("/post", methods=["POST"])
def main():
    try:
        logging.info(f"Request: {request.json!r}")
        response = {
            "session": request.json["session"],
            "version": request.json["version"],
            "response": {"end_session": False},
        }
        handle_dialog(request.json, response)
        logging.info(f"Response: {response!r}")
        return jsonify(response)
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"response": {"text": "Ошибка сервера", "end_session": False}})


def handle_dialog(req, res):
    user_id = req["session"]["user_id"]
    utterance = req["request"]["original_utterance"].lower()

    if utterance in ["помощь", "help", "что ты умеешь", "как играть"]:
        help_text = (
            "Это игра 'Угадай город'. Я показываю фотографию города, "
            "а ты должен его назвать. Доступные города: Москва, Нью-Йорк, Париж. "
            "Назови имя чтобы начать, а потом называй города. "
            "В любой момент скажи 'Помощь' чтобы увидеть это сообщение."
        )
        res["response"]["text"] = help_text
        res["response"]["buttons"] = [{"title": "Помощь", "hide": True}]
        return

    if req["session"]["new"]:
        sessionStorage[user_id] = {"first_name": None}
        res["response"]["text"] = "Привет! Назови свое имя!"
        res["response"]["buttons"] = [{"title": "Помощь", "hide": True}]
        return

    if sessionStorage[user_id]["first_name"] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res["response"]["text"] = "Не расслышала имя. Повтори, пожалуйста!"
            res["response"]["buttons"] = [{"title": "Помощь", "hide": True}]
        else:
            sessionStorage[user_id]["first_name"] = first_name
            res["response"]["text"] = (
                f"Приятно познакомиться, {first_name.title()}. "
                f"Я - Алиса. Какой город хочешь увидеть?"
            )
            res["response"]["buttons"] = [
                {"title": city.title(), "hide": True} for city in cities
            ]
            res["response"]["buttons"].append({"title": "Помощь", "hide": True})
    else:
        city = get_city(req)
        if city and city in cities:
            res["response"]["card"] = {
                "type": "BigImage",
                "title": "Этот город я знаю.",
                "image_id": random.choice(cities[city])
            }
            res["response"]["text"] = "Я угадал! Хочешь еще город?"
            res["response"]["buttons"] = [
                {"title": city.title(), "hide": True} for city in cities
            ]
            res["response"]["buttons"].append({"title": "Помощь", "hide": True})
        else:
            res["response"]["text"] = (
                "Первый раз слышу об этом городе. Попробуй еще разок! "
                "Доступные города: Москва, Нью-Йорк, Париж"
            )
            res["response"]["buttons"] = [
                {"title": city.title(), "hide": True} for city in cities
            ]
            res["response"]["buttons"].append({"title": "Помощь", "hide": True})


def get_city(req):
    if "request" in req and "nlu" in req["request"]:
        for entity in req["request"]["nlu"]["entities"]:
            if entity["type"] == "YANDEX.GEO":
                return entity["value"].get("city", None)
    return None


def get_first_name(req):
    if "request" in req and "nlu" in req["request"]:
        for entity in req["request"]["nlu"]["entities"]:
            if entity["type"] == "YANDEX.FIO":
                return entity["value"].get("first_name", None)
    return None


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
