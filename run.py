from app import create_app

print("[1/3] Импортируем приложение...")
app = create_app()
print("[2/3] Приложение создано, запускаем сервер...")

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
