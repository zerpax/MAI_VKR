import time
import random
from PyQt6.QtWidgets import QApplication, QGraphicsScene
# Предполагаем, что ваш исходный код интерфейса сохранен в файл view.py
from visual import GraphicsView 

class OntologyBenchmark:
    def __init__(self, model_instance):
        """
        Инициализация тестового стенда.
        Для корректной работы сигналов и графического движка PyQt 
        необходимо инициализировать контекст приложения и привязать модель к представлению.
        """
        # Проверяем, запущен ли QApplication (нужно для работы Qt-приложения)
        self.app = QApplication.instance() or QApplication([])
        
        self.scene = QGraphicsScene()
        self.model = model_instance
        self.view = GraphicsView(self.scene, self.model)
        
        # Переменные для хранения сгенерированных ID элементов
        self.generated_node_ids = []
        self.generated_edge_keys = []

    def run_generate_ontology_test(self, size=1000):
        """
        Автоматическое создание онтологии заданного размера.
        Измеряет суммарное время добавления элементов (классов, атрибутов, отношений).
        """
        self.generated_node_ids.clear()
        self.generated_edge_keys.clear()
        self.scene.clear()
        
        # Распределяем типы элементов равномерно
        types = ["class", "attribute", "relation"]
        
        start_time = time.perf_counter()
        
        for i in range(size):
            node_type = types[i % 3]
            label = f"{node_type.capitalize()}_{i}"
            
            # Генерируем случайные координаты, чтобы элементы распределились по сцене
            x = random.randint(-2000, 2000)
            y = random.randint(-2000, 2000)
            
            # Добавление в модель. Сигнал PyQt автоматически вызовет on_node_added в интерфейсе
            node_id = self.model.add_node(node_type, label, pos=(x, y))
            self.generated_node_ids.append(node_id)
            
            # Принудительно заставляем Qt обработать графические события отрисовки,
            # чтобы время рендеринга вошло в замер производительности интерфейса
            self.app.processEvents()
            
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        print(f"[ТЕСТ] Создание {size} элементов: {elapsed:.4f} сек.")
        return elapsed

    def run_add_single_element_test(self, node_type="class"):
        """
        Тест 1: Время добавления одного атомарного элемента на текущем объеме данных
        """
        label = f"Test_Single_{node_type}"
        x, y = 0, 0
        
        start_time = time.perf_counter()
        node_id = self.model.add_node(node_type, label, pos=(x, y))
        self.app.processEvents() # Рендеринг на сцене
        end_time = time.perf_counter()
        
        elapsed = end_time - start_time
        print(f"[ТЕСТ] Добавление 1 элемента ({node_type}): {elapsed:.6f} сек.")
        
        # Сохраняем ID, чтобы потом его использовать в тестах изменения/удаления
        return node_id, elapsed

    def run_edit_element_test(self, node_id):
        """
        Тест 2: Время изменения (переименования) элемента на текущем объеме данных
        """
        new_label = "Updated_Label_Name"
        
        start_time = time.perf_counter()
        self.model.set_label(node_id, new_label)
        self.app.processEvents() # Обновление текста на сцене (on_node_updated)
        end_time = time.perf_counter()
        
        elapsed = end_time - start_time
        print(f"[ТЕСТ] Модификация имени элемента: {elapsed:.6f} сек.")
        return elapsed

    def run_create_edge_test(self, size_edges=100):
        """
        Тест 3: Время создания связей (отношений) между случайными элементами
        """
        if len(self.generated_node_ids) < 2:
            return 0
            
        start_time = time.perf_counter()
        
        count = 0
        while count < size_edges:
            src = random.choice(self.generated_node_ids)
            tgt = random.choice(self.generated_node_ids)
            
            if src != tgt and not self.model.has_edge(src, tgt):
                self.model.add_edge(src, tgt)
                self.generated_edge_keys.append((src, tgt))
                self.app.processEvents() # Отрисовка стрелки на сцене (on_edge_added)
                count += 1
                
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        print(f"[ТЕСТ] Создание {size_edges} связей: {elapsed:.4f} сек. (Среднее на 1 связь: {elapsed/size_edges:.6f} сек.)")
        return elapsed / size_edges

    def run_delete_element_test(self, node_id):
        """
        Тест 4: Время удаления элемента со сцены на текущем объеме данных
        """
        start_time = time.perf_counter()
        self.model.remove_node(node_id)
        self.app.processEvents() # Удаление объекта и связанных стрелок со сцены (on_node_removed)
        end_time = time.perf_counter()
        
        elapsed = end_time - start_time
        print(f"[ТЕСТ] Удаление элемента: {elapsed:.6f} сек.")
        return elapsed
    
    # Запускающий блок (main.py или в конце performance_test.py)
if __name__ == "__main__":
    import structure # Подключаем ваш модуль модели данных
    
    # 1. Инициализируем вашу реальную модель (базу данных / внутреннюю структуру)
    # Предполагаем, что класс модели в вашем файле structure.py называется OntologyModel
    model_data = structure.OntologyModel() 
    
    # 2. Создаем бенчмарк
    benchmark = OntologyBenchmark(model_data)
    
    print("=== ЗАПУСК НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ ОНТОЛОГИИ ===")
    
    # ==========================================
    # ЭТАП 1: ТЕСТИРОВАНИЕ НА ОБЪЕМЕ N1 = 1 000
    # ==========================================
    print("\n--- Эксперимент 1: Объем онтологии n1 = 1 000 элементов ---")
    benchmark.run_generate_ontology_test(size=1000)
    
    # Проводим замеры базовых операций на объеме 1000 элементов
    test_node_id, t1_add = benchmark.run_add_single_element_test("class")
    t1_edit = benchmark.run_edit_element_test(test_node_id)
    t1_edge = benchmark.run_create_edge_test(size_edges=50) # замеряем среднее на связь
    t1_del = benchmark.run_delete_element_test(test_node_id)
    
    # Считаем среднее время выполнения базовой операции на объеме n1
    T_n1 = (t1_add + t1_edit + t1_edge + t1_del) / 4
    print(f"-> Среднее время базовой операции T(n1): {T_n1:.6f} сек.")
    
    # ==========================================
    # ЭТАП 2: ТЕСТИРОВАНИЕ НА ОБЪЕМЕ N2 = 10 000
    # ==========================================
    print("\n--- Эксперимент 2: Объем онтологии n2 = 10 000 элементов ---")
    # Доращиваем онтологию до 10 000 элементов
    benchmark.run_generate_ontology_test(size=10000)
    
    # Проводим аналогичные замеры базовых операций на объеме 10 000 элементов
    test_node_id_large, t2_add = benchmark.run_add_single_element_test("class")
    t2_edit = benchmark.run_edit_element_test(test_node_id_large)
    t2_edge = benchmark.run_create_edge_test(size_edges=50)
    t2_del = benchmark.run_delete_element_test(test_node_id_large)
    
    # Считаем среднее время выполнения базовой операции на объеме n2
    T_n2 = (t2_add + t2_edit + t2_edge + t2_del) / 4
    print(f"-> Среднее время базовой операции T(n2): {T_n2:.6f} сек.")
    
    # ==========================================
    # ЭТАП 3: РАСЧЕТ МАСШТАБИРУЕМОСТИ
    # ==========================================
    print("\n=== ИТОГОВЫЙ РАСЧЕТ МАСШТАБИРУЕМОСТИ ===")
    n1 = 1000
    n2 = 10000
    
    # Ваша формула ненормализованного коэффициента К
    K = (T_n2 / T_n1) * (n1 / n2)
    print(f"Фактический коэффициент замедления системы K: {K:.4f}")
    
    if K <= 1:
        print("Результат: Масштабируемость идеальная (линейная или сублинейная).")
    else:
        print("Результат: Присутствует нелинейное замедление системы при росте данных.")