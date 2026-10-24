
f0= True
while   f0:
    try:
        print("1 -- Цетнробежный (n = 0.75)")
        print("2 -- Поршневой (n = 0.85)")
        print("3 -- Вихревой (n = 0.55)")
        pump = int(input("Выберите тип насоса (1 - 3): "))
        f0= False
    except ValueError:
        print("error")
if f0 == False:
    if pump == 1:
        name = "Центробежный"
        n = 0.75
    elif pump == 2:
        name = "Поршневой"
        n = 0.85
    elif pump == 3:
        name = "Вихревой"
        n = 0.55
    else:
        print("Выберите от 1 до 3!")


f1= True
while   f1:
    try:
        Q = float(input("Введите подачу: "))
        f1= False
    except ValueError:
        print ("error Q")

f2= True
while   f2:
    try:
        H = float(input("Введите напор :"))
        f2= False
    except ValueError:
        print ("error H")
f3= True
while   f3:
    try:
        rho = float(input("Введите плотность среды: "))
        F3= False
    except ValueError:
        print ("error rho")
if (f1 == False) and (f2 == False) and (f3 == False):
     g = 9.81
     P = rho * g * Q * H / (3600 * n * 1000)
if H < 10:
    n_class = "Малый напор"
elif 10 <= H <= 60:
    n_class = "Средний напор"
else:
    n_class = "Высокий напор"
    print("-Результаты: ")
    print("Тип насоса: ", name)
    print("Подача: ", Q)
    print("Напор: ", H)
    print("Мощность: ", P)
    print("Класс напора: ", n_class)

    