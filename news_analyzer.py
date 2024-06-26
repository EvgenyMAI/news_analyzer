import os
import sys
import warnings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

# Отключение предупреждений
warnings.filterwarnings("ignore", category=FutureWarning)

# Создание директории output, если она не существует
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# Загрузка меток
labels = [-2, 2, 1, 0, 1, -1, 1, -1, -2, 1, 1, -1, 0, -1, -2, -2, -1, 1, -1, 2, 2, 0, 0, 2, 0, -1, 1, -1, -1, -1, 2, 0, -1, -1, 1, 1, 2, 2, -2, -1, -2, 1]

# Загрузка новостей для обучения
input_path = "training_news"
files = os.listdir(input_path)
txt_files = [filename for filename in files if filename.endswith(".txt")]
sorted_files = sorted(txt_files, key=lambda x: int(x.split('.')[0].replace('_en', ''), 16))
news_train = []
for filename in sorted_files:
    with open(os.path.join(input_path, filename), 'r', encoding='utf-8') as file:
        news_train.append(file.read().replace('\n', ' '))

# Загрузка новостей для тестирования
news_test = []
test_files = os.listdir("news_en")  # Здесь задается путь к папке с тестовыми новостями
txt_test_files = [filename for filename in test_files if filename.endswith(".txt")]
for filename in txt_test_files:
    with open(os.path.join("news_en", filename), 'r', encoding='utf-8') as file:
        news_test.append(file.read().replace('\n', ' '))

# Список названий компаний
companies = ["Тинькофф", "МТС", "Магнит", "Газпром", "Металлоинвест"]

# Инициализация словаря для хранения обработанных файлов
processed_files = {}

# Векторизация новостей
vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2), stop_words='english')
X_train = vectorizer.fit_transform(news_train)
X_test = vectorizer.transform(news_test)

# Обучение модели
model = LogisticRegression(random_state=42, solver='lbfgs')
model.fit(X_train, labels)

# Прогнозирование классов новостей
predictions = model.predict(X_test)

# Прогнозирование вероятностей классов
probabilities = model.predict_proba(X_test)

# Инициализация словаря для хранения данных по компаниям
company_data = {company: {"ratios": [], "count": 0} for company in companies}

output_path = os.path.join(output_dir, "output.txt")
with open(output_path, 'w', encoding='utf-8') as output_file:
    for i, filename in enumerate(txt_test_files):
        # Получение вероятностей классов
        (neg_2, neg_1, neutral, pos_1, pos_2) = probabilities[i]

        # Получение оригинального названия файла
        original_filename = filename.replace('_en', '')

        # Загрузка оригинальной новости
        with open(os.path.join("news", original_filename), 'r', encoding='utf-8') as file:
            original_news = file.read().replace('\n', ' ')

        # Получение списка названий компаний из первой строки файла
        company_names = original_news.split("\n")[0].strip().split()

        output_file.write(f"Файл: {filename}\n")
        output_file.write(f"Новость: {original_news}\n")

        # Расчет вероятного поведения актива
        ratio = (pos_2 * 2 + pos_1 * 1 + neutral * 0 - neg_1 * 1 - neg_2 * 2)

        # Применение штрафов/надбавок в зависимости от количества упоминаний
        for company in companies:
            company_count = company_names.count(company)
            if company_count == 1:
                ratio /= 2
            elif company_count == 2:
                ratio /= 1.2
            elif company_count >= 4:
                ratio *= 1.1

        output_file.write(f"Вероятное поведение актива: {'+' if ratio > 0 else '-'} {abs(ratio) ** (2 / 3) * 10:.2f}% "
            f"с разбросом {((1 - abs(pos_2 - neg_2)) * 30 + 15) * abs(ratio) ** (2 / 3) * 20 / 100:.2f}%\n\n")

        # Сохранение данных в файлы для анализа по компаниям
        for company in company_names:
            if company in companies:
                company_output_path = f"output_{company.replace(' ', '_')}.txt"
                if company_output_path not in processed_files:
                    processed_files[company_output_path] = set()
                if filename not in processed_files[company_output_path]:
                    company_data[company]["ratios"].append(ratio)  # Сохраняем каждый ratio
                    company_data[company]["count"] += 1
                    processed_files[company_output_path].add(filename)

# Обработка файлов по компаниям для записи агрегированных данных
for company in companies:
    company_output_path = os.path.join(output_dir, f"output_{company.replace(' ', '_')}.txt")
    ratios = company_data[company]["ratios"]
    count = company_data[company]["count"]

    if count > 0:
        # Вычисляем среднее, применяя преобразование и штраф
        average_ratio = sum(ratios) / count
        average_ratio = round(average_ratio * 30, 2)
        average_ratio -= 3

        # Вычисляем стандартное отклонение для разброса
        variance = sum([(ratio - average_ratio) ** 2 for ratio in ratios]) / count
        std_dev = variance ** 0.5
        spread = round((std_dev * 20 / 100) * 3, 2)

        with open(company_output_path, 'w', encoding='utf-8') as company_output_file:
            company_output_file.write(f"{average_ratio}\n")
            company_output_file.write(f"{spread}\n")
    else:
        # Если нет данных для компании, создаем пустой файл или файл с нулевыми значениями
        with open(company_output_path, 'w', encoding='utf-8') as company_output_file:
            company_output_file.write("0.00\n")
            company_output_file.write("0.00\n")

sys.exit(0)
