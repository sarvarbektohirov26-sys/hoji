OIL_DENSITY: float = 850.0 
M_MIN_THRESHOLD: float = 9.5
 
 
def read_valid_param(prompt: str, min_val: float, max_val: float) -> float: 
    """Запрашивает у пользователя число в цикле, пока оно не попадёт в [min_val; max_val]. 
 
    Args: 
        prompt (str): Текст подсказки при вводе. 
        min_val (float): Минимально допустимое значение. 
        max_val (float): Максимально допустимое значение. 
    Returns: 
        float: Проверенное число. 
    """ 
    ... 
 
 
def calc_oil_volume(q_liq: float, w_pct: float) -> float: 
    """Считает суточный объём чистой нефти по формуле: Qн = Qж * (1 - W / 100). 
 
    Args: 
        q_liq (float): Дебит жидкости, м3/сут (0..1000). 
        w_pct (float): Обводнённость, % (0..100). 
    Returns: 
        float: Объёмный дебит нефти Qн, м3/сут. 
    """ 
    result = q_liq * (1 - w_pct / 100)
    return result
 
 
def calc_oil_mass(q_oil: float, density: float = OIL_DENSITY) -> float: 
    """Переводит объём нефти (м3/сут) в массу (т/сут) по формуле: Mн = Qн * density / 1000. 
 
    Args: 
        q_oil (float): Объёмный дебит нефти, м3/сут. 
        density (float): Плотность нефти, кг/м3 (по умолчанию 850.0). 
    Returns: 
        float: Массовый дебит нефти Mн, т/сут. 
    """ 
    ... 
 
 
def evaluate_profitability(m_oil: float, m_min: float = M_MIN_THRESHOLD) -> str: 
    """Определяет статус рентабельности скважины по массе нефти Mн. 
 
    Правило: 
    - Mн < m_min -> 'Убыточна (стоп)' 
    - m_min <= Mн < 3 * m_min -> 'Рентабельна (база)' 
    - Mн >= 3 * m_min -> 'Высокодебитная (приоритет)' 
 
    Args: 
        m_oil (float): Массовый дебит нефти, т/сут. 
        m_min (float): Порог рентабельности, т/сут. 
    Returns: 
        str: Текстовый статус скважины. 
    """ 
    if m_oil < m_min: 
        return "Убыточна (стоп)" 
    elif m_oil < 3 * m_min: 
        return "Рентабельна (база)" 
    else: 
        return "Высокодебитная (приоритет)" 
 
 
if __name__ == "__main__": 
    my_test_mass = 25.0 
    status = evaluate_profitability(my_test_mass) 
    print(f"Масса нефти: {my_test_mass:.2f} т/сут (порог {M_MIN_THRESHOLD}) -> Статус: {status}")
    help(calc_oil_volume)
    test_q = calc_oil_volume(92.0, 35.0)
    print(f"(Результат Qh = {test_q} м3/сут")